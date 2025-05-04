"""
AFAD Emergency Gathering Areas Data Collector

This module provides a class-based interface to collect data about
emergency gathering areas in Turkey from the AFAD website.
"""

import json
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any, Optional

import unidecode
from tqdm import tqdm

from scraper import AFADScraper


class GatheringAreaCollector:
    """
    A class to collect emergency gathering area data for Turkish cities.
    
    This class handles the collection process including city processing,
    district and neighborhood data retrieval, and saving results to files.
    """
    
    def __init__(self, cities_file: str = "cities.json", max_workers: int = 10):
        """
        Initialize the collector.
        
        Args:
            cities_file (str): Path to the JSON file containing city information
            max_workers (int): Maximum number of parallel workers for processing neighborhoods
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("collection.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.cities_file = cities_file
        self.max_workers = max_workers
        self.scraper = AFADScraper()
        
        # Ensure output directory exists
        os.makedirs("iller", exist_ok=True)
    
    def load_cities(self) -> List[Tuple[int, str]]:
        """
        Load the list of cities to process from a JSON file.
        
        Returns:
            List[Tuple[int, str]]: List of city information in format [(code, name), ...]
            
        Raises:
            FileNotFoundError: If cities file is not found
            ValueError: If cities file format is invalid or no valid cities found
        """
        try:
            if not os.path.exists(self.cities_file):
                raise FileNotFoundError(f"Şehir dosyası '{self.cities_file}' bulunamadı. Lütfen dosyanın varlığını kontrol edin.")
            
            with open(self.cities_file, 'r', encoding='utf-8') as f:
                cities_data = json.load(f)
                
            # Validate the file format
            if not isinstance(cities_data, list):
                raise ValueError(f"Geçersiz şehir dosyası formatı. Liste bekleniyor, alınan: {type(cities_data)}.")
                
            # Convert to expected format and validate each entry
            cities = []
            for city in cities_data:
                if isinstance(city, dict) and 'code' in city and 'name' in city:
                    cities.append((int(city['code']), city['name']))
                else:
                    logging.warning(f"Geçersiz şehir kaydı: {city}. Atlanıyor.")
            
            if not cities:
                raise ValueError("Dosyada geçerli şehir bulunamadı. Lütfen dosya içeriğini kontrol edin.")
                
            logging.info(f"{self.cities_file} dosyasından {len(cities)} şehir yüklendi")
            return cities
            
        except json.JSONDecodeError:
            raise ValueError(f"'{self.cities_file}' dosyası geçerli bir JSON formatında değil.")
        except Exception as e:
            raise RuntimeError(f"Şehir dosyası yüklenirken hata oluştu: {e}")
    
    def fetch_data_with_retry(self, query_string: str) -> Dict[str, Any]:
        """
        Fetch data from API with automatic retries on failure.
        
        Args:
            query_string (str): Query parameters for the API
            
        Returns:
            Dict[str, Any]: Parsed JSON response
            
        Raises:
            Exception: If all retry attempts fail
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.scraper.get_data(query_string)
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Hata sonrası yeniden deneme {attempt+1}/{max_retries}: {e}")
                    time.sleep(2 * (attempt + 1))  # Exponential backoff
                else:
                    logging.error(f"{max_retries} deneme sonrası veri çekilemedi: {e}")
                    raise RuntimeError(f"Veri çekme işlemi başarısız oldu: {e}")
    
    def process_neighborhood(self, 
                             city_code: int, 
                             city_name: str, 
                             district: Dict[str, Any], 
                             neighborhood: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Process a single neighborhood to gather data.
        
        Args:
            city_code (int): City code
            city_name (str): City name
            district (Dict[str, Any]): District information
            neighborhood (Dict[str, Any]): Neighborhood information
            
        Returns:
            Tuple[str, Optional[Dict[str, Any]]]: Neighborhood name and processed data or None if error
        """
        try:
            neighborhood_result = {
                'mahalleId': neighborhood['id'], 
                'sokaklar': {}, 
                'toplanmaAlanlari': {}
            }
            
            # Get streets
            street_data = self.fetch_data_with_retry(
                f"ilKodu={city_code}&ilceKodu={district['id']}&sokakKodu={neighborhood['id']}&islem=sokakKodu"
            )
            
            # Get gathering areas
            query_results = self.scraper.get_from_map(city_code, district['id'], neighborhood['id'])
            if query_results is not None:
                for query_res in query_results:
                    neighborhood_result['toplanmaAlanlari'][query_res['properties']['id']] = query_res['properties']
            
            # Process streets
            streets = street_data['data']['dataArr']
            for street in streets:
                neighborhood_result['sokaklar'][street['name']] = {'sokakId': street['id']}
            
            return (neighborhood['name'], neighborhood_result)
        except Exception as e:
            logging.error(f"{district['name']} ilçesindeki {neighborhood['name']} mahallesi işlenirken hata: {e}")
            return (neighborhood['name'], None)
    
    def process_city(self, city_code: int, city_name: str) -> None:
        """
        Process a city to collect all its emergency gathering areas data.
        
        Args:
            city_code (int): City code
            city_name (str): City name
        """
        start_time = time.time()
        logging.info(f"{city_name} işlemeye başlandı - Saat: {time.strftime('%H:%M:%S')}")
        
        all_data = {city_name: {'ilId': city_code, 'ilceler': {}}}
        
        # Get districts
        district_data = self.fetch_data_with_retry(f"ilKodu={city_code}&islem=ilceKodu")
        districts = district_data['data']['dataArr']
        
        logging.info(f"{city_name} için {len(districts)} ilçe işlenecek")
        
        # Process each district
        for district in districts:
            all_data[city_name]['ilceler'][district['name']] = {
                'ilceId': district['id'], 
                'mahalleler': {}
            }
            
            # Get neighborhoods
            neighborhood_data = self.fetch_data_with_retry(
                f"ilKodu={city_code}&ilceKodu={district['id']}&islem=mahalleKodu"
            )
            neighborhoods = neighborhood_data['data']['dataArr']
            
            logging.info(f"{district['name']} ilçesi {len(neighborhoods)} mahalle ile işleniyor")
            
            # Process neighborhoods in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_neighborhood = {
                    executor.submit(
                        self.process_neighborhood, 
                        city_code, city_name, district, neighborhood
                    ): neighborhood for neighborhood in neighborhoods
                }
                
                for future in tqdm(
                    as_completed(future_to_neighborhood), 
                    total=len(neighborhoods), 
                    desc=f"{district['name']} ilerleme"
                ):
                    neighborhood_name, result = future.result()
                    if result is not None:
                        all_data[city_name]['ilceler'][district['name']]['mahalleler'][neighborhood_name] = result
            
            logging.info(f"İlçe tamamlandı: {district['name']}")
        
        # Save results to file
        output_filename = f"iller/{unidecode.unidecode(city_name)}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False)
        
        # Calculate and log elapsed time
        end_time = time.time()
        elapsed_time = end_time - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        logging.info(f"{city_name} tamamlandı - Süre: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        logging.info(f"{city_name} verileri şu dosyaya kaydedildi: {output_filename}")
    
    def run(self) -> None:
        """
        Run the collection process for all cities in the cities file.
        """
        try:
            cities = self.load_cities()
            for city_code, city_name in cities:
                self.process_city(city_code, city_name)
        except FileNotFoundError as e:
            logging.critical(f"Kritik hata: {e}")
            print(f"Hata: {e}")
            exit(1)
        except ValueError as e:
            logging.critical(f"Kritik hata: {e}")
            print(f"Hata: {e}")
            exit(1)
        except Exception as e:
            logging.critical(f"Beklenmeyen kritik hata: {e}")
            print(f"Beklenmeyen hata: {e}")
            exit(1)


if __name__ == "__main__":
    collector = GatheringAreaCollector()
    collector.run()
    logging.info("Veri toplama işlemi tamamlandı.")