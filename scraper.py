"""
AFAD Emergency Gathering Areas Scraper

This module provides a class-based interface to scrape and interact with the official AFAD
(Disaster and Emergency Management Authority) website to retrieve information
about emergency gathering areas in Turkey.
"""

import json
import re
import warnings
from typing import Any, Dict, List, Optional, Tuple

import requests

# Disable SSL warnings for development purposes
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


class AFADScraper:
    """
    A class to interact with AFAD emergency gathering areas API.
    
    This class handles authentication, API requests, and data processing
    for AFAD's emergency gathering areas information.
    """
    
    # Constants
    BASE_URL = "https://www.turkiye.gov.tr"
    TOPLANMA_ALANI_URL = f"{BASE_URL}/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama"
    
    # Common headers for API requests
    BASE_HEADERS = {
        'Host': 'www.turkiye.gov.tr',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,tr-TR;q=0.8,tr;q=0.7',
        'Connection': 'close',
        'Dnt': '1',
    }
    
    def __init__(self) -> None:
        """Initialize the scraper with a new session and auth token."""
        self.session = requests.Session()
        self.session.verify = False
        self.token = self._get_token()
    
    def _get_token(self) -> str:
        """
        Obtain a new authentication token from the AFAD website.
        
        Returns:
            str: Authentication token required for API requests
            
        Raises:
            ValueError: If token cannot be found in the response
        """
        try:
            response = self.session.get(self.TOPLANMA_ALANI_URL, headers=self.BASE_HEADERS)
            token_match = re.search(r'data-token=\"([^"]*)\"', response.text)
            
            if not token_match:
                raise ValueError("Kimlik doğrulama jetonu yanıtta bulunamadı")
            
            return token_match.group(1)
        except requests.RequestException as e:
            raise ConnectionError(f"AFAD sunucusuna bağlanırken hata oluştu: {e}")
    
    def refresh_token(self) -> None:
        """Refresh the authentication token."""
        self.token = self._get_token()
    
    def get_data(self, payload: str) -> Dict[str, Any]:
        """
        Make a POST request to get data from the AFAD API.
        
        Args:
            payload (str): Query parameters for the API request
            
        Returns:
            Dict[str, Any]: JSON response data
        """
        headers = {
            **self.BASE_HEADERS, 
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        data = f"token={self.token}&ajax=1&pn=/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama&{payload}"
        
        try:
            response = self.session.post(
                f"{self.TOPLANMA_ALANI_URL}?submit", 
                headers=headers, 
                data=data
            )
            
            # If response is not JSON, token might be expired; refresh and retry
            if not response.headers['Content-Type'].startswith('application/json'):
                self.refresh_token()
                return self.get_data(payload)
            
            return json.loads(response.text)
            
        except requests.RequestException as e:
            raise ConnectionError(f"API isteği sırasında bağlantı hatası: {e}")
        except json.JSONDecodeError:
            raise ValueError("API yanıtı geçerli bir JSON formatında değil")
    
    def query_point(self, lng: float, lat: float) -> Optional[Dict[str, Any]]:
        """
        Query the gathering area for a specific geographical point.
        
        Args:
            lng (float): Longitude of the point
            lat (float): Latitude of the point
            
        Returns:
            Optional[Dict[str, Any]]: JSON response containing gathering area information
                                     or None if not found
        """
        headers = {
            **self.BASE_HEADERS,
            'Sec-Ch-Ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Origin': self.BASE_URL,
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': f"{self.TOPLANMA_ALANI_URL}?harita=goster",
        }

        data = {
            'pn': '/afet-ve-acil-durum-yonetimi-acil-toplanma-alani-sorgulama',
            'ajax': '1',
            'token': self.token,
            'islem': 'getAlanlarForNokta',
            'lat': lat,
            'lng': lng,
        }

        try:
            response = self.session.post(
                f"{self.TOPLANMA_ALANI_URL}?harita=goster&submit",
                headers=headers,
                data=data,
            )
            
            return response.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            return None
    
    def get_from_map(self, il_code: int, district_code: int, neighborhood_code: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get gathering area data from the map for the specified location.
        
        Args:
            il_code (int): City/province code
            district_code (int): District code
            neighborhood_code (int): Neighborhood code
            
        Returns:
            Optional[List[Dict[str, Any]]]: List of gathering areas or None if not found
        """
        data = {
            'ilKodu': il_code,
            'ilceKodu': district_code,
            'mahalleKodu': neighborhood_code,
            'sokakKodu': '',
            'token': self.token,
            'btn': 'Sorgula',
        }
        
        try:
            response = self.session.post(
                f"{self.TOPLANMA_ALANI_URL}?submit", 
                headers=self.BASE_HEADERS, 
                data=data
            )
            
            # Extract gathering areas data using regex
            toplanma_alanlari_match = re.search(r'toplanmaAlanlari = (.*);', response.text)
            
            if not toplanma_alanlari_match or toplanma_alanlari_match.group(1) == 'null':
                return None

            areas = json.loads(toplanma_alanlari_match.group(1))
            if not areas:
                return None

            return self._process_gathering_areas(areas[0]['geometry']['coordinates'])
            
        except (requests.RequestException, json.JSONDecodeError, IndexError) as e:
            return None
    
    def _process_gathering_areas(self, coordinates: List) -> List[Dict[str, Any]]:
        """
        Process gathering area coordinates and get detailed information.
        
        Args:
            coordinates (List): List of coordinate points defining the area
            
        Returns:
            List[Dict[str, Any]]: Processed gathering area information
        """
        significant_points = self._extract_significant_vertices(coordinates)
        query_results = []
        
        for point in significant_points:
            result = None
            retry_count = 0
            max_retries = 3
            
            while result is None and retry_count < max_retries:
                result = self.query_point(point[0], point[1])
                if result is None:
                    self.refresh_token()
                    retry_count += 1
            
            if result:
                query_results.extend(result['features'])
        
        return query_results
    
    @staticmethod
    def _extract_significant_vertices(polygon: List) -> List[Tuple[float, float]]:
        """
        Extract significant vertices from a polygon to optimize API calls.
        
        This function extracts key points such as extremes and center to
        represent the area efficiently with fewer API calls.
        
        Args:
            polygon (List): Polygon coordinates
            
        Returns:
            List[Tuple[float, float]]: List of significant vertices
        """
        points = polygon[0]
        if len(points) < 6:
            return points

        result = []
        # Get extreme points (min/max in both X and Y dimensions)
        for key in ['min', 'max']:
            points_x = sorted(points, key=lambda x: x[0], reverse=(key=='max'))
            points_y = sorted(points, key=lambda x: x[1], reverse=(key=='max'))
            result.extend([points_x[0], points_y[0]])

        # Calculate and add the center point
        center_x = sum(p[0] for p in result) / 4
        center_y = sum(p[1] for p in result) / 4
        result.append([center_x, center_y])
        
        return result


# For backward compatibility with existing code
_instance = None

def __init__() -> AFADScraper:
    """Initialize a global scraper instance for backward compatibility."""
    global _instance
    _instance = AFADScraper()
    return _instance

def getData(payload: str) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    global _instance
    if _instance is None:
        _instance = AFADScraper()
    return _instance.get_data(payload)

def getFromMap(il_code: int, district_code: int, neighborhood_code: int) -> Optional[List[Dict[str, Any]]]:
    """Legacy function for backward compatibility."""
    global _instance
    if _instance is None:
        _instance = AFADScraper()
    return _instance.get_from_map(il_code, district_code, neighborhood_code)

# For compatibility
get_token = lambda: _instance._get_token() if _instance else AFADScraper()._get_token()
queryPoint = lambda lng, lat: _instance.query_point(lng, lat) if _instance else AFADScraper().query_point(lng, lat)


if __name__ == '__main__':
    try:
        scraper = AFADScraper()
        print(f"Token başarıyla alındı: {scraper.token[:10]}...")
    except Exception as e:
        print(f"Hata oluştu: {e}")