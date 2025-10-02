from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from PIL import Image
import json

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

# Папки для хранения
UPLOAD_DIR = "storage/uploaded_photos/raw"
PROCESSED_DIR = "storage/uploaded_photos/processed"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Простой детектор для теста (без YOLO пока)
class SimpleDetector:
    def __init__(self):
        print("🔄 Простой детектор инициализирован")
    
    def extract_metadata(self, image_path: str):
        """Извлечение базовых метаданных"""
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode,
                    'filename': os.path.basename(image_path),
                    'file_size': os.path.getsize(image_path)
                }
        except Exception as e:
            return {'error': str(e)}
    
    def mock_detect_buildings(self, image_path: str):
        """Заглушка для детекции зданий"""
        # В реальной системе здесь будет YOLO
        return [
            {
                'class': 'building',
                'confidence': 0.85,
                'bbox': [100, 100, 300, 300],
                'center': [200, 200],
                'area': 15.5
            }
        ]

detector = SimpleDetector()

@app.get("/")
async def root():
    return {
        "message": "CV Processing Service работает!",
        "status": "success",
        "mode": "simple_detector",
        "endpoints": [
            "/health",
            "/process-image",
            "/model-info"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cv-processing"}

@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    """Обработка одного изображения (упрощенная версия)"""
    try:
        # Валидация файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "Файл должен быть изображением")
        
        # Сохранение файла
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1] or '.jpg'
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_extension}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Проверка что файл является валидным изображением
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as e:
            os.remove(file_path)
            raise HTTPException(400, f"Невалидное изображение: {e}")
        
        print(f"🔄 Обработка изображения: {file.filename}")
        
        # Извлекаем метаданные
        metadata = detector.extract_metadata(file_path)
        
        # Моковая детекция
        buildings = detector.mock_detect_buildings(file_path)
        
        result = {
            'metadata': metadata,
            'buildings_detected': len(buildings),
            'buildings': buildings,
            'file_info': {
                'original_filename': file.filename,
                'file_id': file_id
            }
        }
        
        print(f"✅ Обработка завершена. Найдено зданий: {result['buildings_detected']}")
        
        return {
            "success": True,
            "results": result
        }
        
    except Exception as e:
        raise HTTPException(500, f"Ошибка обработки: {str(e)}")

@app.get("/model-info")
async def model_info():
    """Информация о модели"""
    return {
        "model_name": "Simple Detector (Mock)",
        "status": "YOLO will be integrated in next step",
        "input_size": "variable",
        "framework": "Pillow"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)