import httpx
from typing import Dict, List, Optional
import time

class OpenStreetMapProvider:
    # Принимаем асинхронный клиент в конструкторе
    def __init__(self, client: httpx.AsyncClient):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.headers = {
            "User-Agent": "GeoPhotoAnalyzer/1.0 (https://github.com/your-repo)"
        }
        self.client = client # Сохраняем httpx.AsyncClient

    async def search(self, query: str, country: str = "", language: str = "ru", limit: int = 5) -> Dict:
        """Асинхронный поиск мест по запросу"""
        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": limit,
            "accept-language": language
        }
        
        if country:
            params["countrycodes"] = country
        
        # Используем асинхронный клиент
        response = await self.client.get(
            f"{self.base_url}/search", 
            params=params, 
            headers=self.headers,
            timeout=15
        )
        response.raise_for_status()
        
        return response.json()
    
    async def reverse(self, lat: float, lon: float, language: str = "ru") -> Dict:
        """Асинхронное обратное геокодирование"""
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18,
            "accept-language": language
        }
        
        # Используем асинхронный клиент
        response = await self.client.get(
            f"{self.base_url}/reverse", 
            params=params, 
            headers=self.headers,
            timeout=15
        )
        response.raise_for_status()
        
        return response.json()
    
    async def get_place_details(self, osm_type: str, osm_id: int) -> Dict:
        """Асинхронная детальная информация о месте"""
        params = {
            "osm_type": osm_type[0].upper(),  # N, W, R
            "osm_id": osm_id,
            "format": "json"
        }
        
        # Используем асинхронный клиент
        response = await self.client.get(
            f"{self.base_url}/details", 
            params=params, 
            headers=self.headers,
            timeout=15
        )
        response.raise_for_status()
        
        return response.json()
