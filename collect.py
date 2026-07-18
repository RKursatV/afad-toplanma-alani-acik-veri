"""
AFAD Acil Toplanma Alanı Veri Toplayıcı

cities.json'daki iller için ilçe/mahalle/sokak ve toplanma alanı verilerini
çekip il başına bir JSON dosyası olarak `iller/` klasörüne kaydeder.

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
from typing import Any, Dict, List, Optional, Tuple

import unidecode
from tqdm import tqdm

from scraper import AFADScraper, AFADScraperError


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
            raise ValueError(f"Geçersiz şehir dosyası formatı: liste bekleniyordu.")

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
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Tek bir mahallenin sokak ve toplanma alanı verilerini toplar."""
        try:
            result: Dict[str, Any] = {
                "mahalleId": neighborhood["id"],
                "sokaklar": {},
                "toplanmaAlanlari": {},
            }

            for street in self.scraper.get_streets(neighborhood["id"]):
                result["sokaklar"][street["name"]] = {"sokakId": street["id"]}

            areas = self.scraper.get_gathering_areas(
                city_code, district["id"], neighborhood["id"]
            )
            for feature in areas or []:
                properties = feature["properties"]
                result["toplanmaAlanlari"][properties["id"]] = properties

            return (neighborhood["name"], result)
        except Exception as error:
            logging.error(
                f"{district['name']} / {neighborhood['name']} işlenirken hata: {error}"
            )
            return (neighborhood["name"], None)

    def process_city(self, city_code: int, city_name: str) -> None:
        """Bir ilin tüm verisini toplayıp dosyaya kaydeder."""
        output_filename = os.path.join(
            self.output_dir, f"{unidecode.unidecode(city_name)}.json"
        )
        if not self.force and os.path.exists(output_filename):
            logging.info(f"{city_name} atlanıyor: {output_filename} zaten mevcut "
                         f"(yeniden toplamak için --force kullanın)")
            return

        start_time = time.time()
        logging.info(f"{city_name} işlenmeye başlandı")

        city_data: Dict[str, Any] = {city_name: {"ilId": city_code, "ilceler": {}}}
        failed_neighborhoods = 0

        districts = self.scraper.get_districts(city_code)
        logging.info(f"{city_name} için {len(districts)} ilçe işlenecek")

        for district in districts:
            district_entry: Dict[str, Any] = {"ilceId": district["id"], "mahalleler": {}}
            city_data[city_name]["ilceler"][district["name"]] = district_entry

            neighborhoods = self.scraper.get_neighborhoods(district["id"])

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self.process_neighborhood, city_code, district, neighborhood
                    ): neighborhood
                    for neighborhood in neighborhoods
                }

                for future in tqdm(
                    as_completed(futures),
                    total=len(neighborhoods),
                    desc=f"{city_name} / {district['name']}",
                ):
                    neighborhood_name, result = future.result()
                    if result is not None:
                        district_entry["mahalleler"][neighborhood_name] = result
                    else:
                        failed_neighborhoods += 1

            logging.info(f"İlçe tamamlandı: {district['name']}")

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(city_data, f, ensure_ascii=False)

        elapsed = time.time() - start_time
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        logging.info(
            f"{city_name} tamamlandı - Süre: {hours:02d}:{minutes:02d}:{seconds:02d} "
            f"- Dosya: {output_filename}"
            + (f" - {failed_neighborhoods} mahalle işlenemedi!" if failed_neighborhoods else "")
        )

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
