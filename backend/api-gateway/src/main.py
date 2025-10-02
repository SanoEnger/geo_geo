from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio

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

# Photo upload endpoint
@app.post("/api/photo_upload/upload")
async def upload_photo(file: UploadFile = File(...)):
    try:
        print(f"📨 API Gateway: Received file {file.filename}")
        
        # Read file content
        contents = await file.read()
        file_size = len(contents)
        
        print(f"📊 File size: {file_size} bytes")
        print(f"🎯 Sending to: http://photo-upload-service:8003/api/upload")
        
        # Forward to upload service
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": (file.filename, contents, file.content_type)}
            
            response = await client.post(
                "http://photo-upload-service:8003/api/upload",  # ← ПРАВИЛЬНЫЙ URL
                files=files
            )
            
            print(f"🔄 Upload service response: {response.status_code}")
            print(f"📝 Upload service response text: {response.text}")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upload service error: {response.text}"
                )
                
    except httpx.ConnectError as e:
        print(f"❌ Connection error: {e}")
        raise HTTPException(status_code=503, detail="Upload service unavailable")
    except Exception as e:
        print(f"❌ API Gateway error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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