import requests
from typing import Dict, List, Optional

class GeoNamesProvider:
    def __init__(self, username: str = "demo"):
        self.base_url = "http://api.geonames.org"
        self.username = username
    
    def get_elevation(self, lat: float, lng: float) -> Optional[float]:
        """Получение высоты над уровнем моря"""
        try:
            params = {
                "lat": lat,
                "lng": lng,
                "username": self.username
            }
            
            response = requests.get(f"{self.base_url}/srtm3JSON", 
                                  params=params, 
                                  timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("srtm3")
        except:
            return None
    
    def get_timezone(self, lat: float, lng: float) -> Dict:
        """Получение информации о часовом поясе"""
        params = {
            "lat": lat,
            "lng": lng,
            "username": self.username
        }
        
        response = requests.get(f"{self.base_url}/timezoneJSON", 
                              params=params, 
                              timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def search_places(self, query: str, country: str = "", max_rows: int = 10) -> Dict:
        """Поиск мест"""
        params = {
            "q": query,
            "maxRows": max_rows,
            "username": self.username,
            "style": "FULL"
        }
        
        if country:
            params["country"] = country.upper()
        
        response = requests.get(f"{self.base_url}/searchJSON", 
                              params=params, 
                              timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    def get_country_info(self, country_code: str) -> Dict:
        """Информация о стране"""
        params = {
            "country": country_code.upper(),
            "username": self.username
        }
        
        response = requests.get(f"{self.base_url}/countryInfoJSON", 
                              params=params, 
                              timeout=10)
        response.raise_for_status()
        
        return response.json()