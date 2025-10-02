from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import uuid
from PIL import Image

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
UPLOAD_DIR = "storage/uploaded_photos/raw"
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Photo Upload Service работает!", "status": "success"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "photo-upload"}

def validate_image(file: UploadFile) -> bool:
    """Валидация загружаемого изображения"""
    # Проверка расширения
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, "Недопустимый формат файла"
    
    return True, "Файл валиден"

@app.post("/api/upload")
async def upload_photo(file: UploadFile = File(...)):
    """Загрузка одного фото"""
    print(f"🚨 UPLOAD SERVICE: Начало загрузки {file.filename}")
    
    try:
        # Валидация файла
        is_valid, message = validate_image(file)
        if not is_valid:
            print(f"❌ Валидация не пройдена: {message}")
            raise HTTPException(400, message)
        
        print(f"✅ Валидация пройдена")

        # Генерация уникального имени файла
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1].lower()
        filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Сохранение файла
        content = await file.read()
        file_size = len(content)
        print(f"📦 Размер файла: {file_size} байт")
        
        # Проверка размера
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(400, "Файл слишком большой")
        
        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(content)
        print(f"💾 Файл сохранен: {file_path}")

        # Дополнительная валидация через PIL
        try:
            print(f"🔍 Проверка изображения через PIL...")
            with Image.open(file_path) as img:
                img.verify()
            print(f"✅ PIL верификация успешна")
        except Exception as e:
            print(f"❌ Ошибка PIL верификации: {e}")
            os.remove(file_path)
            raise HTTPException(400, f"Невалидное изображение: {e}")
        
        # Получение метаданных
        with Image.open(file_path) as img:
            metadata = {
                "format": img.format,
                "size": img.size,
                "mode": img.mode
            }
        print(f"📊 Метаданные: {metadata}")

        # ✅ ВЫЗОВ CV SERVICE ДЛЯ АНАЛИЗА
        print(f"🔗 Отправка в CV Service для анализа...")
        cv_results = {}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Используем уже прочитанный контент из памяти
                files = {"file": (file.filename, content, file.content_type)}
                
                cv_response = await client.post(
                    "http://cv-processing-service:8002/process-image",
                    files=files,
                    timeout=30.0
                )
                
                print(f"📊 CV Response статус: {cv_response.status_code}")
                
                if cv_response.status_code == 200:
                    cv_data = cv_response.json()
                    print(f"✅ CV Service вернул данные: {cv_data}")
                    
                    # ✅ ИСПРАВЛЕНИЕ: Правильно извлекаем результаты из структуры CV Service
                    if cv_data.get("success"):
                        # CV Service возвращает результаты в поле "results"
                        results_data = cv_data.get("results", {})
                        cv_results = {
                            "status": "success",
                            "buildings_detected": results_data.get("buildings_detected", 0),
                            "buildings": results_data.get("buildings", []),
                            "metadata": results_data.get("metadata", {}),
                            "file_info": results_data.get("file_info", {})
                        }
                        print(f"🏠 Найдено зданий: {cv_results['buildings_detected']}")
                    else:
                        print(f"⚠️ CV Service вернул success: false")
                        cv_results = {
                            "status": "error", 
                            "message": "CV processing failed",
                            "cv_response": cv_data
                        }
                else:
                    print(f"❌ CV Error: {cv_response.status_code} - {cv_response.text}")
                    cv_results = {
                        "status": "error",
                        "message": f"CV processing failed with status {cv_response.status_code}",
                        "details": cv_response.text
                    }
                    
        except httpx.ConnectError as e:
            error_msg = f"Не удалось подключиться к CV Service: {e}"
            print(f"❌ {error_msg}")
            cv_results = {"status": "error", "message": error_msg}
        except httpx.TimeoutException as e:
            error_msg = f"Таймаут подключения к CV Service: {e}"
            print(f"⏰ {error_msg}")
            cv_results = {"status": "error", "message": error_msg}
        except Exception as e:
            error_msg = f"Ошибка соединения с CV Service: {e}"
            print(f"❌ {error_msg}")
            cv_results = {"status": "error", "message": error_msg}

        # Формируем финальный ответ
        response_data = {
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "original_name": file.filename,
            "file_size": file_size,
            "metadata": metadata,
            "cv_results": cv_results,
            "message": "Файл успешно загружен и обработан"
        }

        print(f"✅ UPLOAD SERVICE: Загрузка завершена успешно")
        return response_data
        
    except HTTPException as he:
        print(f"🚫 HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print(f"❌ Общая ошибка загрузки: {str(e)}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Ошибка загрузки: {str(e)}")

@app.post("/api/upload/batch")
async def upload_batch_photos(files: list[UploadFile] = File(...)):
    """Пакетная загрузка фото"""
    results = []
    
    for file in files:
        try:
            result = await upload_photo(file)
            results.append({
                "filename": file.filename,
                "status": "success",
                "data": result
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
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
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(500, f"Ошибка получения списка файлов: {e}")