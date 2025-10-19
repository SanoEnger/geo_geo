from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from typing import Optional, Dict, List, Any
from PIL import Image
from PIL.ExifTags import TAGS
import traceback

# 1. Модель для входных данных (должна соответствовать JSON, который отправляет Photo Upload Service)
class ProcessRequest(BaseModel):
    file_id: str
    original_filename: str
    file_path: str # Путь к файлу на общем томе

app = FastAPI(
    title="CV Processing Service",
    description="Сервис компьютерного зрения для детекции зданий на фотографиях",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Папки для хранения (должны соответствовать docker-compose.yml)
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/uploaded_photos/raw")
PROCESSED_DIR = os.getenv("PROCESSED_DIR", "storage/uploaded_photos/processed")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# --------------------------------------------------------------------------------------------------
# Вспомогательные классы (SimpleDetector)
# --------------------------------------------------------------------------------------------------

class SimpleDetector:
    def __init__(self):
        print("🔄 Простой детектор инициализирован")
    
    def extract_metadata(self, image_path: str) -> Dict:
        """Извлечение базовых метаданных"""
        try:
            with Image.open(image_path) as img:
                file_size = os.path.getsize(image_path) 
                return {
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode,
                    'filename': os.path.basename(image_path),
                    'file_size': file_size,
                    'exif': self._get_exif_data(img)
                }
        except Exception as e:
            return {'error': str(e)}

    def _get_exif_data(self, img: Image.Image) -> Dict:
        """Извлечение EXIF данных"""
        exif_data = {}
        try:
            # 🌟 ИСПРАВЛЕНИЕ: Используем публичный метод getexif()
            exif = img.getexif() 
            if exif:
                for tag, value in exif.items():
                    decoded = TAGS.get(tag, tag)
                    exif_data[decoded] = str(value)
        except Exception:
            pass
        return exif_data
    
    def mock_detect_buildings(self, file_path: str) -> List[Dict]:
        """Заглушка для детекции зданий"""
        # Всегда возвращаем один фиктивный BBOX, как необходимо для продолжения пайплайна
        return [
            {
                'class': 'building',
                'confidence': 0.85,
                # BBOX: [x_min, y_min, x_max, y_max]
                'bbox': [500, 500, 1500, 1500], 
                'center': [1000, 1000],
                'area': 1000000
            }
        ]

detector = SimpleDetector()

# --------------------------------------------------------------------------------------------------
# Эндпоинты
# --------------------------------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cv-processing-service"}

@app.post("/api/process") 
async def process_photo(request: ProcessRequest):
    """
    Обрабатывает загруженный файл: извлекает метаданные и выполняет детекцию зданий.
    Использует file_path для доступа к файлу на общем томе.
    """
    file_path = request.file_path
    file_id = request.file_id
    original_filename_safe = request.original_filename

    if not os.path.exists(file_path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            f"Файл не найден на общем томе: {file_path}"
        )

    try:
        # Проверка, что файл является изображением
        try:
            with Image.open(file_path) as img:
                img.verify() 
        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Невалидное изображение: {e}")
        
        print(f"🔄 Обработка изображения: {original_filename_safe} ({file_id})")
        
        # 1. Извлекаем метаданные
        metadata = detector.extract_metadata(file_path)
        
        # 2. Моковая детекция
        buildings = detector.mock_detect_buildings(file_path)
        
        result = {
            'metadata': metadata,
            'buildings_detected': len(buildings),
            'buildings': buildings,
            'file_info': {
                'original_filename': original_filename_safe,
                'file_id': file_id
            }
        }
        
        print(f"✅ Обработка завершена. Найдено зданий: {result['buildings_detected']}")
        
        return {
            "success": True,
            "results": result 
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Непредвиденная ошибка в CV Service: {traceback.format_exc()}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Ошибка обработки: {str(e)}")

@app.get("/model-info")
async def model_info():
    """Информация о модели"""
    return {
        "model_name": "Simple Detector (Mock)",
        "status": "Ready",
        "description": "Используется моковая детекция для тестирования пайплайна."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)