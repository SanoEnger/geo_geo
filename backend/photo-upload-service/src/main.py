from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import uuid
import io
from PIL import Image
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import traceback 

# Определение модели запроса для Geocoding Service (нужно для создания JSON-запроса)
class BuildingGeocodingRequest(BaseModel):
    file_id: str
    building_bbox: Optional[List[float]] = None

app = FastAPI(
    title="Photo Upload Service",
    description="Сервис загрузки и валидации фотографий",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/uploaded_photos/raw")
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))

# Адреса сервисов
GEOCODING_SERVICE_URL = os.getenv("GEOCODING_SERVICE_URL", "http://geocoding-service:8004")
CV_PROCESSING_SERVICE_URL = os.getenv("CV_PROCESSING_SERVICE_URL", "http://cv-processing-service:8002")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --------------------------------------------------------------------------------------------------
# Вспомогательные функции
# --------------------------------------------------------------------------------------------------

async def call_cv_processing_service(file_id: str, original_filename: str, file_path: str) -> List[Dict]:
    """Вызов CV Processing Service для детекции зданий."""
    print(f"🔄 CV-Processing: Отправка на обработку {file_id}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Предполагаем, что CV Service принимает JSON с file_id и file_path
            response = await client.post(
                f"{CV_PROCESSING_SERVICE_URL}/api/process",
                json={
                    "file_id": file_id,
                    "original_filename": original_filename,
                    "file_path": file_path # Сервисы используют общий том 'storage'
                },
            )
            response.raise_for_status()
            
            # Предполагаем, что CV Service возвращает данные в формате {"results": {"buildings": [...]}}
            cv_result = response.json().get("results", {}).get("buildings", [])
            print(f"✅ CV-Processing: Обнаружено {len(cv_result)} зданий.")
            return cv_result
            
    except httpx.HTTPStatusError as e:
        print(f"❌ CV Service HTTP Error: {e.response.text}")
        raise HTTPException(e.response.status_code, detail=f"CV Service Error: {e.response.json().get('detail', e.response.text)}")
    except Exception as e:
        print(f"❌ CV Service Connection Error: {e}")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"CV Service Unavailable: {str(e)}")


async def call_geocoding_service(request_data: BuildingGeocodingRequest) -> Dict:
    """Вызов Geocoding Service для определения координат."""
    bbox_log = f"[{request_data.building_bbox[0]}, ...]" if request_data.building_bbox else "нет BBOX"
    print(f"🔄 Geocoding: Отправка BBOX ({bbox_log}) для {request_data.file_id}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{GEOCODING_SERVICE_URL}/api/geocode-building",
                json=request_data.model_dump(),
            )
            response.raise_for_status()
            
            print(f"✅ Geocoding: Успешный ответ: {response.json().get('address', 'Координаты получены')}")
            return response.json()
            
    except httpx.HTTPStatusError as e:
        print(f"❌ Geocoding Service HTTP Error: {e.response.text}")
        raise HTTPException(e.response.status_code, detail=f"Geocoding Service Error: {e.response.json().get('detail', e.response.text)}")
    except Exception as e:
        print(f"❌ Geocoding Service Connection Error: {e}")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Geocoding Service Unavailable: {str(e)}")

async def upload_photo(file: UploadFile) -> Dict:
    """Обработка одного загруженного файла."""
    if file.filename is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Отсутствует имя файла.")
        
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Недопустимое расширение файла: {file_extension}. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}")

    # Создание уникального ID и имени файла
    file_id = str(uuid.uuid4())
    original_filename_safe = file.filename.replace('/', '_').replace('\\', '_')
    storage_filename = f"{file_id}_{original_filename_safe}"
    file_path = os.path.join(UPLOAD_DIR, storage_filename)
    
    # Сохранение файла
    print(f"💾 Сохранение файла: {file.filename} как {storage_filename}")
    file_size = 0
    
    try:
        # Чтение содержимого из UploadFile
        # Ключевой момент: файл уже должен быть считан в API Gateway, но httpx передает его в memory.
        # file.read() сбрасывает курсор и читает.
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Файл {file.filename} ({file_size} bytes) превышает максимальный размер {MAX_FILE_SIZE} bytes.")
            
        with open(file_path, "wb") as f:
            f.write(contents)
            
        print(f"✅ Файл сохранен. Размер: {file_size} bytes")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        # Очистка, если сохранение не удалось
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Ошибка при сохранении файла: {str(e)}")

    # 1. Вызов CV Processing Service
    cv_buildings = await call_cv_processing_service(file_id, original_filename_safe, file_path)
    
    geocoding_result = {"success": False, "note": "Здания не обнаружены."}
    
    # 2. Геокодирование (если найдены здания)
    if cv_buildings:
        # Берем первый BBOX для геокодирования
        first_building = cv_buildings[0]
        bbox = first_building.get('bbox')
        
        if bbox and len(bbox) == 4 and all(isinstance(x, (int, float)) for x in bbox):
            print(f"🔄 Geocoding: Обнаружено 1 зданий. BBOX первого: {bbox}")
            
            geocoding_request = BuildingGeocodingRequest(
                file_id=storage_filename, 
                building_bbox=bbox
            )
            
            geocoding_result = await call_geocoding_service(geocoding_request)
        else:
            geocoding_result = {"success": False, "note": "Здания обнаружены, но BBOX отсутствует или некорректен."}

    # 3. Формирование финального ответа
    return {
        "file_id": file_id,
        "filename": original_filename_safe,
        "size": file_size,
        "status": "processed",
        "geocoding_result": geocoding_result
    }

# --------------------------------------------------------------------------------------------------
# Эндпоинты
# --------------------------------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "photo-upload-service"}

# 🌟 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ 🌟
@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)): # <-- ИСПРАВЛЕНО: теперь ожидаем список файлов в поле 'files'
    """Пакетная загрузка и обработка фотографий."""
    
    if not files:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Необходимо загрузить хотя бы один файл.")
        
    results = []
    
    # Перебор всех файлов в пакете
    for file in files:
        try:
            # Важно: Сбросить курсор в 0, чтобы upload_photo мог прочитать содержимое
            await file.seek(0) 

            # Вызов функции, обрабатывающей один файл
            result = await upload_photo(file)
            results.append({
                "filename": file.filename,
                "status": "success",
                "data": result
            })
        except HTTPException as he:
             results.append({
                "filename": file.filename,
                "status": "error",
                "error": he.detail
            })
        except Exception as e:
            # Для целей отладки
            print(f"❌ Непредвиденная ошибка при обработке {file.filename}: {traceback.format_exc()}")
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": f"Непредвиденная ошибка: {str(e)}"
            })
    
    # Финальный ответ в формате батча
    return {
        "processed": len(results),
        "results": results
    }

@app.get("/api/files")
async def list_uploaded_files():
    """Список загруженных файлов"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "modified": os.path.getmtime(file_path)
                })
        return files
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Ошибка при получении списка файлов: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)