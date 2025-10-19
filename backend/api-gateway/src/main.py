from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from typing import List # <-- ДОБАВЛЕНО: для поддержки списка файлов

app = FastAPI(title="API Gateway")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "service": "api-gateway"}

# Root endpoint
@app.get("/")
async def root():
    return {"message": "API Gateway is running"}

# Photo upload endpoint (ИСПРАВЛЕНО: handles batch upload and forwards with 'files' plural)
@app.post("/api/photo_upload/upload")
async def upload_photos(files: List[UploadFile] = File(...)): # <-- ИСПРАВЛЕНО: Принимаем List[UploadFile]
    try:
        if not files:
            raise HTTPException(400, "Необходимо загрузить хотя бы один файл.")
            
        print(f"📨 API Gateway: Received {len(files)} files")
        
        transfer_files = []
        total_size = 0
        
        # Читаем все файлы и готовим их для пересылки
        for file in files:
            # Сначала перемещаемся в начало файла (если он уже был прочитан), затем читаем
            await file.seek(0) 
            contents = await file.read()
            total_size += len(contents)
            
            # Формат httpx для multipart/form-data: (имя_поля, (имя_файла, содержимое, mime_тип))
            # Используем 'files' (plural) для соответствия ожидаемому API Photo Upload Service
            transfer_files.append((
                'files', # <-- ИСПРАВЛЕНО: Используем 'files' plural
                (file.filename, contents, file.content_type)
            ))
            
            print(f"📊 File {file.filename} size: {len(contents)} bytes")
            
        target_url = "http://photo-upload-service:8003/api/upload"
        print(f"🎯 Sending {len(files)} files (Total size: {total_size} bytes) to: {target_url}")
        
        # Forward to upload service
        # Используем таймаут 60 секунд, так как загрузка может быть долгой
        async with httpx.AsyncClient(timeout=60.0) as client: 
            
            response = await client.post(
                target_url,
                files=transfer_files # Пересылка в виде батча
            )
            
            print(f"🔄 Upload service response: {response.status_code}")
            print(f"📝 Upload service response text: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                # Пытаемся получить детали ошибки из JSON, если они есть
                error_detail = response.json().get("detail", response.text) if response.content else response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upload service error: {error_detail}"
                )
                
    except httpx.ConnectError as e:
        print(f"❌ Connection error: {e}")
        raise HTTPException(status_code=503, detail="Upload service unavailable (Connection error)")
    except HTTPException as he:
        # Переброс HTTPException, поднятых внутри блока
        raise he
    except Exception as e:
        print(f"❌ API Gateway error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal API Gateway error: {str(e)}")

# Test endpoint to check upload service directly
@app.get("/test-upload-service")
async def test_upload_service():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://photo-upload-service:8003/health")
            return {
                "upload_service_status": response.status_code,
                "upload_service_response": response.json() if response.status_code == 200 else "Error"
            }
    except Exception as e:
        return {"error": str(e)}