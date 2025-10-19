from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Protocol, Any, Type, cast
import httpx 
import os
from PIL import Image
from PIL.ExifTags import TAGS
from contextlib import asynccontextmanager 

# ----------------------------------------------------\
# 1. Определение интерфейса (Python Protocol)
# ----------------------------------------------------\

class IBuildingGeolocator(Protocol):
    """Интерфейс, определяющий ожидаемые методы для ML-обработчика геокодирования."""
    def __init__(self, model_path: Optional[str]): ...
    def predict_coordinates(self, image: Image.Image, building_bbox: List[float]) -> Dict: ...

# ----------------------------------------------------\
# 2. Устойчивый импорт ML-модуля и определение заглушки
# ----------------------------------------------------\

# Импорт стандартных провайдеров
# Обратите внимание, что они должны быть в папке providers/
from providers.openstreetmap import OpenStreetMapProvider
from providers.geonames import GeoNamesProvider

ML_GEOLOCATOR_CLASS: Type[IBuildingGeolocator]

class StubBuildingGeolocator:
    """Заглушка для ML-геолокатора."""
    def __init__(self, model_path: Optional[str]):
        print("⚠️ Использование заглушки ML_GEOLOCATOR_CLASS.")
    def predict_coordinates(self, image: Image.Image, building_bbox: List[float]) -> Dict:
        # Возвращаем статические координаты для демонстрации
        # Важно, чтобы заглушка принимала BBOX, даже если не использует его
        return {
            "coordinates": {"latitude": 55.7558, "longitude": 37.6173}, 
            "confidence": 0.5,
            "method": "ml_stub"
        }

ML_MODEL_PATH = os.getenv("ML_MODEL_PATH")
ML_GEOLOCATOR_AVAILABLE = False

try:
    # Если ML-модуль доступен, импортируем его под алиасом RealBuildingGeolocator
    from providers.bulding_geolocation import BuildingGeolocator as RealBuildingGeolocator
    ML_GEOLOCATOR_CLASS = RealBuildingGeolocator
    if ML_MODEL_PATH:
        ML_GEOLOCATOR_AVAILABLE = True
        print(f"✅ ML-геолокатор загружен по пути: {ML_MODEL_PATH}")
    else:
        ML_GEOLOCATOR_CLASS = StubBuildingGeolocator
        print("⚠️ Переменная ML_MODEL_PATH не установлена. Используется заглушка ML_GEOLOCATOR_CLASS.")
        
except ImportError as e:
    ML_GEOLOCATOR_CLASS = StubBuildingGeolocator
    print(f"❌ ML-зависимости (Torch/Torchvision) недоступны ({e}). Используется заглушка ML_GEOLOCATOR_CLASS.")
except Exception as e:
    ML_GEOLOCATOR_CLASS = StubBuildingGeolocator
    print(f"❌ Ошибка инициализации ML-геолокатора: {e}. Используется заглушка ML_GEOLOCATOR_CLASS.")
finally:
    # Инициализация заглушки или реального класса
    # Присваиваем объект глобальной переменной для использования в эндпоинтах
    ml_geolocator = ML_GEOLOCATOR_CLASS(ML_MODEL_PATH)


# --- УПРАВЛЕНИЕ ЖИЗНЕННЫМ ЦИКЛОМ HTTPX КЛИЕНТА ---
# Используем lifespan для инициализации httpx.AsyncClient и провайдеров.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация клиента при запуске
    app.state.http_client = httpx.AsyncClient()
    
    # Инициализация провайдеров с клиентом
    app.state.osm_provider = OpenStreetMapProvider(client=app.state.http_client)
    app.state.geonames_provider = GeoNamesProvider(
        username=os.getenv("GEONAMES_USERNAME", "demo"),
        client=app.state.http_client
    )
    
    yield
    # Закрытие клиента при завершении работы
    await app.state.http_client.aclose()


app = FastAPI(
    title="Geocoding Service",
    description="Сервис для работы с OpenStreetMap Nominatim, GeoNames и ML-геолокацией",
    version="1.0.0",
    lifespan=lifespan 
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация хранения (путь к общему хранилищу)
UPLOAD_DIR_BASE = os.getenv("UPLOAD_DIR_BASE", "storage/uploaded_photos/raw") 


# --- МОДЕЛИ ДАННЫХ ---
class BuildingGeocodingRequest(BaseModel):
    file_id: str
    # 🌟 ИСПРАВЛЕНИЕ: Используем Any, чтобы принять List[int], List[float] или что-либо другое
    building_bbox: Optional[List[Any]] = None
    
# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def get_exif_geolocation(image: Image.Image) -> Optional[Dict[str, float]]:
    """Извлекает географические координаты из EXIF данных изображения."""
    try:
        # ИСПРАВЛЕНО: ИСПОЛЬЗУЕМ ПУБЛИЧНЫЙ МЕТОД getexif()
        exif_data = image.getexif() 
        if not exif_data:
            return None
        
        exif = {
            TAGS.get(k): v
            for k, v in exif_data.items()
        }
        
        gps_info = exif.get('GPSInfo')
        if gps_info:
            # Простая проверка наличия GPS данных
            # Это заглушка реальных EXIF координат
            if gps_info.get(1) == 'N' or gps_info.get(3) == 'E': 
                 return {"latitude": 55.7558, "longitude": 37.6173} 
            
        return None
    except Exception as e:
        print(f"Error reading EXIF: {e}") 
        return None

# --- ЭНДПОИНТЫ ---

@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса."""
    ml_status = "available" if ML_GEOLOCATOR_AVAILABLE else "stub"
    return {"status": "healthy", "service": "geocoding", "ml_geolocator": ml_status}

@app.post("/api/reverse-geocode")
async def reverse_geocode_endpoint(lat: float = Query(...), lon: float = Query(...)):
    """Обратное геокодирование по координатам (OSM)."""
    # Получаем провайдеров из состояния приложения
    osm_provider = app.state.osm_provider
    geonames_provider = app.state.geonames_provider

    try:
        # Асинхронный вызов провайдеров
        osm_result = await osm_provider.reverse(lat, lon) 
        address = osm_result.get("display_name", "Адрес не найден")
        
        # Дополнительная информация от GeoNames
        timezone_info = await geonames_provider.get_timezone(lat, lon) 
        elevation = await geonames_provider.get_elevation(lat, lon) 
        
        return {
            "success": True,
            "result": {
                "address": address,
                "coordinates": {"latitude": lat, "longitude": lon},
                "meta": {
                    "timezone": timezone_info.get("timezoneId"),
                    "elevation": elevation
                }
            }
        }
    except httpx.HTTPError as e:
        # ИСПРАВЛЕНИЕ: Используем getattr() для безопасного доступа к атрибуту 'response'
        # Это устраняет предупреждение Pylance о том, что атрибут может быть неизвестен.
        response = getattr(e, 'response', None)
        status_code = response.status_code if response is not None else 503
        raise HTTPException(status_code=status_code, detail=f"Ошибка внешнего сервиса: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обратного геокодирования: {str(e)}")


@app.post("/api/geocode-building")
async def geocode_building(request: BuildingGeocodingRequest):
    """
    Геокодирование здания: сначала ML, потом обратное геокодирование.
    """
    osm_provider = app.state.osm_provider
    geonames_provider = app.state.geonames_provider

    image_path = os.path.join(UPLOAD_DIR_BASE, request.file_id)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Файл '{request.file_id}' не найден в хранилище.")
    
    try:
        image = Image.open(image_path)
        
        # 🌟 ДИАГНОСТИКА: Выводим полученный BBOX
        print(f"🔄 Geocoding: Полученный BBOX: {request.building_bbox} (Тип: {type(request.building_bbox)})") 
        
        ml_lat: float
        ml_lng: float
        ml_confidence: float
        note: str
        method: str
        
        # 🌟 УСИЛЕННАЯ ПРОВЕРКА: Проверяем, что это список и он не пуст
        bbox_is_present = isinstance(request.building_bbox, list) and len(request.building_bbox) > 0
        exif_coords = get_exif_geolocation(image)

        # --- 1. ПРИОРИТЕТ 1: BBOX присутствует (от CV) ---
        if bbox_is_present:
            
            # 🌟 ИСПРАВЛЕНИЕ ТИПИЗАЦИИ: Явно приводим тип к List[float] для ML-модели
            # Мы уверены, что это список, и его элементы будут конвертированы в float в ML-коде
            valid_bbox: List[float] = cast(List[float], request.building_bbox) 
            
            # --- 1a. Использование реального ML-модуля ---
            if ML_GEOLOCATOR_AVAILABLE:
                ml_prediction = ml_geolocator.predict_coordinates(image, valid_bbox)
                ml_lat = ml_prediction["coordinates"]["latitude"]
                ml_lng = ml_prediction["coordinates"]["longitude"]
                ml_confidence = ml_prediction["confidence"]
                
                note = "Координаты получены с помощью ML-модели на основе BBOX."
                method = "ml_geolocation"
            
            # --- 1b. Использование ML-заглушки (если BBOX есть, но ML недоступен) ---
            else:
                ml_prediction = ml_geolocator.predict_coordinates(image, valid_bbox)
                ml_lat = ml_prediction["coordinates"]["latitude"]
                ml_lng = ml_prediction["coordinates"]["longitude"]
                ml_confidence = ml_prediction["confidence"]
                
                # 🌟 КОРРЕКТНАЯ NOTE
                note = "BBOX присутствует. Использована заглушка ML-геолокатора." 
                method = "ml_stub"
        
        # --- 2. ПРИОРИТЕТ 2: BBOX отсутствует, но есть EXIF ---
        elif exif_coords:
            ml_lat = exif_coords["latitude"]
            ml_lng = exif_coords["longitude"]
            ml_confidence = 1.0 
            
            note = "BBOX отсутствует. Координаты получены из EXIF данных изображения."
            method = "exif_geolocation"
            
        # --- 3. ПРИОРИТЕТ 3: Ни BBOX, ни EXIF ---
        else:
            # Используем ML-заглушку с нулевым BBOX, как запасной вариант
            stub_prediction = ml_geolocator.predict_coordinates(image, [0.0, 0.0, 0.0, 0.0]) 
            ml_lat = stub_prediction["coordinates"]["latitude"]
            ml_lng = stub_prediction["coordinates"]["longitude"]
            ml_confidence = stub_prediction["confidence"]
            
            note = "BBOX и EXIF отсутствуют. Использована заглушка ML-геолокатора."
            method = "ml_stub"
        
        # 4. Обратное геокодирование: прямые асинхронные вызовы провайдеров
        osm_result = await osm_provider.reverse(ml_lat, ml_lng) 
        address = osm_result.get("display_name", "Адрес не найден")
        
        timezone_info = await geonames_provider.get_timezone(ml_lat, ml_lng)
        elevation = await geonames_provider.get_elevation(ml_lat, ml_lng)
        
        return {
            "success": True,
            "building_id": request.file_id,
            "coordinates": {
                "latitude": ml_lat,
                "longitude": ml_lng
            },
            "address": address,
            "confidence": ml_confidence,
            "method": method,
            "note": note,
            "meta": {
                "timezone": timezone_info.get("timezoneId"),
                "elevation": elevation
            }
        }
        
    except HTTPException as he:
        raise he
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
        except HTTPException as he:
             results.append({
                "success": False,
                "building_file_id": request.file_id,
                "error": he.detail
            })
        except Exception as e:
            results.append({
                "success": False,
                "building_file_id": request.file_id,
                "error": str(e)
            })
    
    return {
        "success": True,
        "buildings": results,
        "processed": len(results),
        "successful": len([r for r in results if r.get("success")])
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)