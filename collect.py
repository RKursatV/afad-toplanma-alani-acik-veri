"""
AFAD Acil Toplanma Alanı Veri Toplayıcı

cities.json'daki iller için ilçe/mahalle/sokak ve toplanma alanı verilerini
çekip il başına bir JSON (v2 şeması) ve bir GeoJSON dosyası olarak `iller/`
klasörüne kaydeder.

Kullanım:
    python collect.py                        # tüm iller (mevcut dosyalar atlanır)
    python collect.py --only Hatay,Adana     # sadece belirtilen iller
    python collect.py --force                # mevcut dosyaların üzerine yaz
    python collect.py --workers 2            # paralel istek sayısını düşür
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import unidecode
from tqdm import tqdm

from scraper import AFADScraper, AFADScraperError

SCHEMA_VERSION = 2


def normalize_area(feature: Dict[str, Any]) -> Tuple[Optional[int], Dict[str, Any]]:
    """API'den gelen GeoJSON Feature'ı v2 alan kaydına dönüştürür.

    API'deki x/y alanları boylam/enlemdir (poligon geometrisiyle
    karşılaştırılarak doğrulandı).
    """
    properties = feature.get("properties") or {}
    area = {
        "ad": properties.get("tesis_adi"),
        "tabelaKod": properties.get("tabela_kod"),
        "adres": properties.get("acik_adres"),
        "il": properties.get("il_adi"),
        "ilce": properties.get("ilce_adi"),
        "mahalle": properties.get("mahalle_adi"),
        "sokak": properties.get("sokak_adi"),
        "enlem": properties.get("y"),
        "boylam": properties.get("x"),
        "geometri": feature.get("geometry"),
    }
    return properties.get("id"), area


class GatheringAreaCollector:
    """İllerin toplanma alanı verilerini toplayıp dosyaya kaydeder."""

    def __init__(
        self,
        cities_file: str = "cities.json",
        output_dir: str = "iller",
        max_workers: int = 4,
        force: bool = False,
    ):
        self.cities_file = cities_file
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.force = force
        self.scraper = AFADScraper()

        os.makedirs(self.output_dir, exist_ok=True)

    def load_cities(self) -> List[Tuple[int, str]]:
        """cities.json'dan [(kod, ad), ...] listesi döndürür."""
        if not os.path.exists(self.cities_file):
            raise FileNotFoundError(f"Şehir dosyası '{self.cities_file}' bulunamadı.")

        try:
            with open(self.cities_file, "r", encoding="utf-8") as f:
                cities_data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"'{self.cities_file}' geçerli bir JSON dosyası değil.")

        if not isinstance(cities_data, list):
            raise ValueError("Geçersiz şehir dosyası formatı: liste bekleniyordu.")

        cities = []
        for city in cities_data:
            if isinstance(city, dict) and "code" in city and "name" in city:
                cities.append((int(city["code"]), city["name"]))
            else:
                logging.warning(f"Geçersiz şehir kaydı atlanıyor: {city}")

        if not cities:
            raise ValueError("Dosyada geçerli şehir kaydı bulunamadı.")

        logging.info(f"{self.cities_file} dosyasından {len(cities)} şehir yüklendi")
        return cities

    def process_neighborhood(
        self, city_code: int, district: Dict[str, Any], neighborhood: Dict[str, Any]
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Tek bir mahallenin sokaklarını ve toplanma alanlarını toplar.

        Returns:
            (mahalle kaydı | None, alan Feature listesi). Alanların il seviyesinde
            tekilleştirilmesi çağıran tarafta yapılır.
        """
        try:
            streets = self.scraper.get_streets(neighborhood["id"])
            features = self.scraper.get_gathering_areas(
                city_code, district["id"], neighborhood["id"]
            ) or []

            area_ids = []
            for feature in features:
                area_id = (feature.get("properties") or {}).get("id")
                if area_id is not None and area_id not in area_ids:
                    area_ids.append(area_id)

            entry = {
                "id": neighborhood["id"],
                "ad": neighborhood["name"],
                "sokaklar": [street["name"] for street in streets],
                "toplanmaAlanlari": area_ids,
            }
            return entry, features
        except Exception as error:
            logging.error(
                f"{district['name']} / {neighborhood['name']} işlenirken hata: {error}"
            )
            return None, []

    def process_city(self, city_code: int, city_name: str) -> None:
        """Bir ilin tüm verisini toplayıp JSON + GeoJSON olarak kaydeder."""
        base = os.path.join(self.output_dir, unidecode.unidecode(city_name))
        json_path = f"{base}.json"
        geojson_path = f"{base}.geojson"
        if not self.force and os.path.exists(json_path):
            logging.info(f"{city_name} atlanıyor: {json_path} zaten mevcut "
                         f"(yeniden toplamak için --force kullanın)")
            return

        start_time = time.time()
        logging.info(f"{city_name} işlenmeye başlandı")

        city_data: Dict[str, Any] = {
            "sema": SCHEMA_VERSION,
            "kaynak": AFADScraper.SERVICE_URL,
            "toplanmaTarihi": datetime.now().astimezone().isoformat(timespec="seconds"),
            "il": {"id": city_code, "ad": city_name},
            "ilceler": [],
            "alanlar": {},
        }
        failed_neighborhoods = 0

        districts = self.scraper.get_districts(city_code)
        logging.info(f"{city_name} için {len(districts)} ilçe işlenecek")

        for district in districts:
            district_entry: Dict[str, Any] = {
                "id": district["id"],
                "ad": district["name"],
                "mahalleler": [],
            }
            city_data["ilceler"].append(district_entry)

            neighborhoods = self.scraper.get_neighborhoods(district["id"])

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(
                        self.process_neighborhood, city_code, district, neighborhood
                    )
                    for neighborhood in neighborhoods
                ]

                for future in tqdm(
                    as_completed(futures),
                    total=len(neighborhoods),
                    desc=f"{city_name} / {district['name']}",
                ):
                    entry, features = future.result()
                    if entry is None:
                        failed_neighborhoods += 1
                        continue
                    district_entry["mahalleler"].append(entry)
                    for feature in features:
                        area_id, area = normalize_area(feature)
                        if area_id is not None:
                            city_data["alanlar"].setdefault(str(area_id), area)

            # Thread tamamlanma sırası rastgele; çıktıyı kararlı tutmak için sırala.
            district_entry["mahalleler"].sort(key=lambda m: m["ad"])
            logging.info(f"İlçe tamamlandı: {district['name']}")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(city_data, f, ensure_ascii=False)
        self.write_geojson(geojson_path, city_data)

        elapsed = time.time() - start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        logging.info(
            f"{city_name} tamamlandı - Süre: {hours:02d}:{minutes:02d}:{seconds:02d} "
            f"- {len(city_data['alanlar'])} toplanma alanı - Dosyalar: {json_path}, {geojson_path}"
            + (f" - {failed_neighborhoods} mahalle işlenemedi!" if failed_neighborhoods else "")
        )

    @staticmethod
    def write_geojson(path: str, city_data: Dict[str, Any]) -> None:
        """İlin toplanma alanlarını standalone GeoJSON FeatureCollection yazar."""
        features = []
        for area_id, area in city_data["alanlar"].items():
            properties = {k: v for k, v in area.items() if k != "geometri"}
            properties["id"] = int(area_id)
            features.append({
                "type": "Feature",
                "geometry": area["geometri"],
                "properties": properties,
            })

        collection = {
            "type": "FeatureCollection",
            "features": features,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(collection, f, ensure_ascii=False)

    def run(self, only: Optional[List[str]] = None) -> None:
        """Toplama işlemini çalıştırır.

        Args:
            only: Sadece bu adlardaki illeri işle (Türkçe karakterlere ve
                  büyük/küçük harfe duyarsız karşılaştırılır).
        """
        cities = self.load_cities()

        if only:
            wanted = {unidecode.unidecode(name).strip().lower() for name in only}
            cities = [
                (code, name) for code, name in cities
                if unidecode.unidecode(name).lower() in wanted
            ]
            if not cities:
                raise ValueError(f"--only ile eşleşen il bulunamadı: {only}")

        for city_code, city_name in cities:
            self.process_city(city_code, city_name)


def main() -> int:
    parser = argparse.ArgumentParser(description="AFAD toplanma alanı veri toplayıcı")
    parser.add_argument("--cities", default="cities.json", help="Şehir listesi dosyası")
    parser.add_argument("--output-dir", default="iller", help="Çıktı klasörü")
    parser.add_argument("--workers", type=int, default=4, help="Paralel istek sayısı")
    parser.add_argument("--only", help="Sadece bu iller (virgülle ayrılmış adlar)")
    parser.add_argument("--force", action="store_true",
                        help="Mevcut il dosyalarının üzerine yaz")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("collection.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    try:
        collector = GatheringAreaCollector(
            cities_file=args.cities,
            output_dir=args.output_dir,
            max_workers=args.workers,
            force=args.force,
        )
        collector.run(only=args.only.split(",") if args.only else None)
    except (FileNotFoundError, ValueError, AFADScraperError) as error:
        logging.critical(f"Kritik hata: {error}")
        return 1
    except KeyboardInterrupt:
        logging.warning("Kullanıcı tarafından durduruldu.")
        return 130

    logging.info("Veri toplama işlemi tamamlandı.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
