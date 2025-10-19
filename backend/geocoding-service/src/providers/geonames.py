import httpx
from typing import Dict, List, Optional

class GeoNamesProvider:
    # ИСПРАВЛЕНИЕ: Добавляем логику, чтобы убедиться, что 'demo' используется, если переданная строка пуста
    def __init__(self, username: str = "demo", client: Optional[httpx.AsyncClient] = None):
        self.base_url = "http://api.geonames.org"
        
        # 🎯 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Используем 'demo', если полученное имя пользователя пусто
        self.username = username if username else "demo" 
        
        # Сохраняем асинхронный клиент
        self.client = client if client else httpx.AsyncClient()
    
    async def get_elevation(self, lat: float, lng: float) -> Optional[float]:
        """Получение высоты над уровнем моря"""
        try:
            params = {
                "lat": lat,
                "lng": lng,
                "username": self.username
            }
            
            # Используем асинхронный клиент
            response = await self.client.get(
                f"{self.base_url}/srtm3JSON", 
                params=params, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            elevation = data.get("srtm3")
            
            # Корректная обработка None и строки "null"
            if isinstance(elevation, (int, float)):
                return float(elevation)
            elif isinstance(elevation, str) and elevation.lower() not in ["null", ""]:
                return float(elevation)
            return None
        except Exception:
            return None
    
    async def get_timezone(self, lat: float, lng: float) -> Dict:
        """Получение информации о часовом поясе"""
        params = {
            "lat": lat,
            "lng": lng,
            "username": self.username
        }
        
        # Используем асинхронный клиент
        response = await self.client.get(
            f"{self.base_url}/timezoneJSON", 
            params=params, 
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
    
    async def search_places(self, query: str, country: str = "", max_rows: int = 10) -> Dict:
        """Поиск мест"""
        params = {
            "q": query,
            "maxRows": max_rows,
            "username": self.username,
            "style": "FULL"
        }
        
        if country:
            params["country"] = country.upper()
        
        # Используем асинхронный клиент
        response = await self.client.get(
            f"{self.base_url}/searchJSON", 
            params=params, 
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
    
    async def get_country_info(self, country_code: str) -> Dict:
        """Информация о стране"""
        params = {
            "country": country_code.upper(),
            "username": self.username
        }
        
        # Используем асинхронный клиент
        response = await self.client.get(
            f"{self.base_url}/countryInfoJSON", 
            params=params, 
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()