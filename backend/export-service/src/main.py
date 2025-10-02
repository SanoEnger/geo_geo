from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import pandas as pd
import os
import uuid
from datetime import datetime
import json

app = FastAPI(
    title="Export Service",
    description="Сервис экспорта данных в XLSX и другие форматы",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Папка для экспортов
EXPORT_DIR = "storage/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# Модели данных
class ExportRequest(BaseModel):
    dataset_ids: Optional[List[int]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    include_photos: bool = True
    include_detections: bool = True
    include_geocoding: bool = True
    format: str = "xlsx"

class ExportResponse(BaseModel):
    export_id: str
    status: str
    file_path: Optional[str] = None
    message: str

@app.get("/")
async def root():
    return {
        "message": "Export Service работает!",
        "status": "success",
        "endpoints": [
            "/health",
            "/api/export",
            "/api/export/{export_id}/download"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "export-service"}

@app.post("/api/export", response_model=ExportResponse)
async def create_export(request: ExportRequest, background_tasks: BackgroundTasks):
    """Создание экспорта данных"""
    try:
        export_id = str(uuid.uuid4())
        
        # В реальности здесь будет запрос к БД для получения данных
        # Сейчас используем mock данные
        mock_data = generate_mock_export_data()
        
        # Создаем файл экспорта в фоновом режиме
        background_tasks.add_task(create_export_file, export_id, mock_data, request.format)
        
        return ExportResponse(
            export_id=export_id,
            status="processing",
            message="Экспорт начат. Файл будет готов через несколько секунд."
        )
        
    except Exception as e:
        raise HTTPException(500, f"Ошибка создания экспорта: {str(e)}")

@app.get("/api/export/{export_id}/download")
async def download_export(export_id: str):
    """Скачивание готового экспорта"""
    file_path = os.path.join(EXPORT_DIR, f"{export_id}.xlsx")
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "Файл экспорта не найден или еще не готов")
    
    filename = f"geo_photo_export_{export_id[:8]}.xlsx"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.get("/api/export/{export_id}/status")
async def get_export_status(export_id: str):
    """Получение статуса экспорта"""
    file_path = os.path.join(EXPORT_DIR, f"{export_id}.xlsx")
    
    if os.path.exists(file_path):
        return {
            "export_id": export_id,
            "status": "completed",
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "download_url": f"/api/export/{export_id}/download"
        }
    else:
        return {
            "export_id": export_id,
            "status": "processing",
            "message": "Экспорт все еще обрабатывается"
        }

def generate_mock_export_data() -> List[Dict]:
    """Генерация mock данных для экспорта"""
    return [
        {
            "photo_id": f"photo_{i}",
            "filename": f"building_{i}.jpg",
            "taken_at": datetime.now().isoformat(),
            "latitude": 55.7558 + (i * 0.001),
            "longitude": 37.6173 + (i * 0.001),
            "building_count": 1,
            "confidence": 0.85 + (i * 0.01),
            "address": f"Москва, ул. Примерная, д. {i}",
            "status": "completed"
        }
        for i in range(1, 6)
    ]

def create_export_file(export_id: str, data: List[Dict], format: str):
    """Создание файла экспорта"""
    try:
        # Создаем DataFrame
        df = pd.DataFrame(data)
        
        # Создаем Excel файл с несколькими листами
        file_path = os.path.join(EXPORT_DIR, f"{export_id}.xlsx")
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Основные данные
            df.to_excel(writer, sheet_name='Фотографии', index=False)
            
            # Статистика
            stats_data = {
                'Метрика': ['Всего фото', 'Фото с координатами', 'Успешно обработано', 'Средняя уверенность'],
                'Значение': [
                    len(data),
                    len([d for d in data if d.get('latitude')]),
                    len([d for d in data if d.get('status') == 'completed']),
                    df['confidence'].mean() if 'confidence' in df.columns else 0
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)
            
            # Детекции
            detections_data = []
            for item in data:
                if item.get('building_count', 0) > 0:
                    detections_data.append({
                        'photo_id': item['photo_id'],
                        'building_count': item['building_count'],
                        'confidence': item.get('confidence', 0),
                        'address': item.get('address', 'Не определен')
                    })
            
            if detections_data:
                detections_df = pd.DataFrame(detections_data)
                detections_df.to_excel(writer, sheet_name='Детекции', index=False)
        
        print(f"✅ Файл экспорта создан: {file_path}")
        
    except Exception as e:
        print(f"❌ Ошибка создания файла экспорта: {e}")

@app.get("/api/export/formats")
async def get_export_formats():
    """Получение доступных форматов экспорта"""
    return {
        "formats": [
            {"value": "xlsx", "label": "Excel (.xlsx)", "description": "Формат Microsoft Excel"},
            {"value": "csv", "label": "CSV (.csv)", "description": "Текстовый формат с разделителями"},
            {"value": "json", "label": "JSON (.json)", "description": "JavaScript Object Notation"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)