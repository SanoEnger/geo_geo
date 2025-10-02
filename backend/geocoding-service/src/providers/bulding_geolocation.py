# building_geolocation.py
from matplotlib import transforms
import torch
import torch.nn as nn
from PIL import Image
import numpy as np
from typing import List, Dict

class BuildingGeolocationModel(nn.Module):
    """ML модель для определения координат здания по изображению"""
    
    def __init__(self):
        super().__init__()
        # Архитектура модели для регрессии координат
        self.backbone = torch.hub.load('pytorch/vision:v0.10.0', 'resnet50', pretrained=True)
        self.backbone.fc = nn.Linear(2048, 512)
        self.coord_head = nn.Linear(512, 2)  # lat, lng
        self.confidence_head = nn.Linear(512, 1)
    
    def forward(self, x):
        features = self.backbone(x)
        coords = torch.tanh(self.coord_head(features))  # нормализованные координаты
        confidence = torch.sigmoid(self.confidence_head(features))
        return coords, confidence

class BuildingGeolocator:
    def __init__(self, model_path: str = None):
        self.model = BuildingGeolocationModel()
        if model_path:
            self.model.load_state_dict(torch.load(model_path))
        self.model.eval()
    
    def predict_coordinates(self, image: Image.Image, building_bbox: List[float]) -> Dict:
        """Предсказание координат для здания"""
        # Вырезаем здание из изображения
        cropped_building = self.crop_building(image, building_bbox)
        
        # Препроцессинг
        processed_image = self.preprocess(cropped_building)
        
        # Предсказание
        with torch.no_grad():
            coords, confidence = self.model(processed_image)
        
        # Денормализация координат (пример для определенного региона)
        lat = 55.0 + coords[0].item() * 10.0  # для региона Москвы
        lng = 37.0 + coords[1].item() * 10.0
        
        return {
            "coordinates": {"latitude": lat, "longitude": lng},
            "confidence": confidence.item(),
            "method": "ml_geolocation"
        }
    
    def crop_building(self, image: Image.Image, bbox: List[float]) -> Image.Image:
        """Вырезает здание по bounding box"""
        x1, y1, x2, y2 = bbox
        return image.crop((x1, y1, x2, y2))
    
    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """Препроцессинг изображения"""
        # Ресайз, нормализация и т.д.
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        return transform(image).unsqueeze(0)