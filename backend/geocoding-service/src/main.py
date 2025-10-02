from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import requests
import os
from datetime import datetime

app = FastAPI(
    title="Geocoding Service",
    description="Сервис для работы с OpenStreetMap Nominatim и GeoNames",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация API
OSM_NOMINATIM_URL = "https://nominatim.openstreetmap.org"
GEONAMES_URL = "http://api.geonames.org"

# GeoNames username (бесплатная регистрация на geonames.org)
GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "demo")

# Модели данных
class Coordinates(BaseModel):
    latitude: float
    longitude: float

class Address(BaseModel):
    formatted_address: str
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None

class GeocodingResponse(BaseModel):
    coordinates: Coordinates
    address: Address
    place_id: Optional[str] = None
    osm_id: Optional[str] = None
    osm_type: Optional[str] = None

class ElevationResponse(BaseModel):
    elevation: float
    source: str

class TimezoneResponse(BaseModel):
    timezone: str
    offset: str
    country_code: str

@app.get("/")
async def root():
    return {
        "message": "Geocoding Service работает!",
        "status": "success",
        "apis": ["OpenStreetMap Nominatim", "GeoNames"],
        "features": ["Geocoding", "Reverse Geocoding", "Elevation", "Timezone"]
    }

@app.get("/health")
async def health_check():
    # Проверяем доступность сервисов
    osm_status = "unknown"
    geonames_status = "unknown"
    
    try:
        # Проверка OSM Nominatim
        response = requests.get(f"{OSM_NOMINATIM_URL}/search", 
                              params={"q": "test", "format": "json", "limit": 1},
                              timeout=10)
        osm_status = "available" if response.status_code == 200 else "unavailable"
    except:
        osm_status = "unreachable"
    
    try:
        # Проверка GeoNames
        response = requests.get(f"{GEONAMES_URL}/countryInfoJSON",
                              params={"username": GEONAMES_USERNAME},
                              timeout=10)
        geonames_status = "available" if response.status_code == 200 else "unavailable"
    except:
        geonames_status = "unreachable"
    
    return {
        "status": "healthy", 
        "service": "geocoding",
        "openstreetmap": osm_status,
        "geonames": geonames_status
    }

@app.get("/api/geocode")
async def geocode_address(
    address: str = Query(..., description="Адрес для геокодирования"),
    language: str = Query("ru", description="Язык ответа"),
    country: str = Query("", description="Ограничение по стране (например: ru)")
):
    """
    Геокодирование адреса в координаты через OpenStreetMap Nominatim
    """
    try:
        params = {
            "q": address,
            "format": "json",
            "addressdetails": 1,
            "limit": 1,
            "accept-language": language
        }
        
        if country:
            params["countrycodes"] = country
        
        headers = {
            "User-Agent": "GeoPhotoAnalyzer/1.0 (https://github.com/your-repo)"
        }
        
        response = requests.get(f"{OSM_NOMINATIM_URL}/search", 
                              params=params, 
                              headers=headers,
                              timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            raise HTTPException(404, "Address not found")
        
        result = data[0]
        address_data = result.get("address", {})
        
        geocoding_response = GeocodingResponse(
            coordinates=Coordinates(
                latitude=float(result["lat"]),
                longitude=float(result["lon"])
            ),
            address=Address(
                formatted_address=result["display_name"],
                street=address_data.get("road") or address_data.get("pedestrian"),
                city=address_data.get("city") or address_data.get("town") or address_data.get("village"),
                country=address_data.get("country"),
                country_code=address_data.get("country_code"),
                postal_code=address_data.get("postcode")
            ),
            place_id=result.get("place_id"),
            osm_id=result.get("osm_id"),
            osm_type=result.get("osm_type")
        )
        
        return {
            "success": True,
            "source": "openstreetmap",
            "result": geocoding_response,
            "raw_response": result
        }
        
    except requests.RequestException as e:
        raise HTTPException(500, f"OpenStreetMap API error: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Geocoding error: {str(e)}")

@app.get("/api/reverse-geocode")
async def reverse_geocode(
    lat: float = Query(..., description="Широта"),
    lng: float = Query(..., description="Долгота"),
    language: str = Query("ru", description="Язык ответа")
):
    """
    Обратное геокодирование - координаты в адрес через OpenStreetMap
    """
    try:
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1,
            "zoom": 18,  # Детальный уровень
            "accept-language": language
        }
        
        headers = {
            "User-Agent": "GeoPhotoAnalyzer/1.0 (https://github.com/your-repo)"
        }
        
        response = requests.get(f"{OSM_NOMINATIM_URL}/reverse", 
                              params=params, 
                              headers=headers,
                              timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if "error" in data:
            raise HTTPException(404, "No address found for these coordinates")
        
        address_data = data.get("address", {})
        
        reverse_geocode_response = GeocodingResponse(
            coordinates=Coordinates(latitude=lat, longitude=lng),
            address=Address(
                formatted_address=data["display_name"],
                street=address_data.get("road") or address_data.get("pedestrian"),
                city=address_data.get("city") or address_data.get("town") or address_data.get("village"),
                country=address_data.get("country"),
                country_code=address_data.get("country_code"),
                postal_code=address_data.get("postcode")
            ),
            place_id=data.get("place_id"),
            osm_id=data.get("osm_id"),
            osm_type=data.get("osm_type")
        )
        
        return {
            "success": True,
            "source": "openstreetmap",
            "result": reverse_geocode_response,
            "raw_response": data
        }
        
    except requests.RequestException as e:
        raise HTTPException(500, f"OpenStreetMap API error: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Reverse geocoding error: {str(e)}")

@app.get("/api/elevation")
async def get_elevation(
    lat: float = Query(..., description="Широта"),
    lng: float = Query(..., description="Долгота")
):
    """
    Получение высоты над уровнем моря через GeoNames
    """
    try:
        params = {
            "lat": lat,
            "lng": lng,
            "username": GEONAMES_USERNAME
        }
        
        response = requests.get(f"{GEONAMES_URL}/srtm3JSON", 
                              params=params, 
                              timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "srtm3" not in data:
            # Если GeoNames не дал результат, пробуем альтернативный источник
            elevation = await _get_elevation_alternative(lat, lng)
            source = "alternative"
        else:
            elevation = data["srtm3"]
            source = "geonames"
        
        elevation_response = ElevationResponse(
            elevation=elevation,
            source=source
        )
        
        return {
            "success": True,
            "result": elevation_response,
            "coordinates": Coordinates(latitude=lat, longitude=lng)
        }
        
    except requests.RequestException as e:
        # Пробуем альтернативный источник при ошибке
        try:
            elevation = await _get_elevation_alternative(lat, lng)
            elevation_response = ElevationResponse(
                elevation=elevation,
                source="alternative"
            )
            return {
                "success": True,
                "result": elevation_response,
                "coordinates": Coordinates(latitude=lat, longitude=lng)
            }
        except:
            raise HTTPException(500, f"Elevation service error: {str(e)}")

async def _get_elevation_alternative(lat: float, lng: float) -> float:
    """Альтернативный источник высоты (OpenElevation API)"""
    try:
        url = "https://api.open-elevation.com/api/v1/lookup"
        payload = {"locations": [{"latitude": lat, "longitude": lng}]}
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data["results"][0]["elevation"]
    except:
        # Возвращаем 0 если все источники недоступны
        return 0.0

@app.get("/api/timezone")
async def get_timezone(
    lat: float = Query(..., description="Широта"),
    lng: float = Query(..., description="Долгота")
):
    """
    Получение информации о часовом поясе через GeoNames
    """
    try:
        params = {
            "lat": lat,
            "lng": lng,
            "username": GEONAMES_USERNAME
        }
        
        response = requests.get(f"{GEONAMES_URL}/timezoneJSON", 
                              params=params, 
                              timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "timezoneId" not in data:
            raise HTTPException(404, "Timezone not found")
        
        timezone_response = TimezoneResponse(
            timezone=data["timezoneId"],
            offset=data["gmtOffset"],
            country_code=data.get("countryCode", "")
        )
        
        return {
            "success": True,
            "result": timezone_response,
            "coordinates": Coordinates(latitude=lat, longitude=lng)
        }
        
    except requests.RequestException as e:
        raise HTTPException(500, f"GeoNames API error: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Timezone error: {str(e)}")

@app.get("/api/country-info")
async def get_country_info(
    country_code: str = Query(..., description="Код страны (например: RU)")
):
    """
    Получение информации о стране через GeoNames
    """
    try:
        params = {
            "country": country_code.upper(),
            "username": GEONAMES_USERNAME
        }
        
        response = requests.get(f"{GEONAMES_URL}/countryInfoJSON", 
                              params=params, 
                              timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "geonames" not in data or not data["geonames"]:
            raise HTTPException(404, "Country not found")
        
        country = data["geonames"][0]
        
        return {
            "success": True,
            "country": {
                "name": country["countryName"],
                "code": country["countryCode"],
                "capital": country["capital"],
                "population": country["population"],
                "area": country["areaInSqKm"],
                "continent": country["continentName"]
            }
        }
        
    except requests.RequestException as e:
        raise HTTPException(500, f"GeoNames API error: {str(e)}")

@app.get("/api/search-places")
async def search_places(
    query: str = Query(..., description="Название места для поиска"),
    country: str = Query("", description="Ограничение по стране"),
    max_results: int = Query(5, description="Максимальное количество результатов")
):
    """
    Поиск мест через GeoNames
    """
    try:
        params = {
            "q": query,
            "maxRows": max_results,
            "username": GEONAMES_USERNAME,
            "style": "FULL"
        }
        
        if country:
            params["country"] = country.upper()
        
        response = requests.get(f"{GEONAMES_URL}/searchJSON", 
                              params=params, 
                              timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        places = []
        for place in data.get("geonames", []):
            places.append({
                "name": place["name"],
                "country": place.get("countryName"),
                "country_code": place.get("countryCode"),
                "coordinates": {
                    "latitude": float(place["lat"]),
                    "longitude": float(place["lng"])
                },
                "feature_class": place.get("fcl"),
                "feature_code": place.get("fcode"),
                "population": place.get("population"),
                "elevation": place.get("elevation")
            })
        
        return {
            "success": True,
            "results": places,
            "count": len(places)
        }
        
    except requests.RequestException as e:
        raise HTTPException(500, f"GeoNames API error: {str(e)}")

class BuildingData(BaseModel):
    bbox: List[float]  # [x1, y1, x2, y2]
    center: List[float]  # [x, y]
    area: float
    confidence: float
    class_name: str = "building"

class BuildingGeocodingRequest(BaseModel):
    file_id: str
    building: BuildingData
    image_metadata: Optional[Dict] = None

@app.post("/api/geocode-building")
async def geocode_building(request: BuildingGeocodingRequest):
    """
    Геокодирование здания по визуальным признакам
    TODO: Интегрировать с ML моделью для определения местоположения
    """
    try:
        # ВРЕМЕННОЕ РЕШЕНИЕ - используем центр здания как псевдо-координаты
        # В реальности здесь должна быть ML модель, которая по визуальным признакам
        # определяет реальные координаты
        
        building = request.building
        center_x, center_y = building.center
        
        # Псевдо-координаты на основе положения в изображении
        # Это временное решение - нужно заменить на реальную ML модель
        pseudo_lat = 55.7558 + (center_x / 1000 - 0.5) * 0.1  # Пример для Москвы
        pseudo_lng = 37.6173 + (center_y / 1000 - 0.5) * 0.1
        
        # Обратное геокодирование для получения адреса
        reverse_geocode_result = await reverse_geocode(pseudo_lat, pseudo_lng)
        
        return {
            "success": True,
            "building_id": request.file_id,
            "coordinates": {
                "latitude": pseudo_lat,
                "longitude": pseudo_lng
            },
            "address": reverse_geocode_result["result"]["address"],
            "confidence": building.confidence,
            "method": "pseudo_coordinates",  # Временное решение
            "note": "Это временные координаты. Нужно интегрировать ML модель для точного определения."
        }
        
    except Exception as e:
        raise HTTPException(500, f"Building geocoding error: {str(e)}")

@app.post("/api/geocode-buildings")
async def geocode_buildings(buildings_request: List[BuildingGeocodingRequest]):
    """
    Пакетное геокодирование нескольких зданий
    """
    results = []
    for request in buildings_request:
        try:
            result = await geocode_building(request)
            results.append(result)
        except Exception as e:
            results.append({
                "success": False,
                "building_id": request.file_id,
                "error": str(e)
            })
    
    return {
        "success": True,
        "buildings": results,
        "processed": len(results),
        "successful": len([r for r in results if r["success"]])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port="8004")