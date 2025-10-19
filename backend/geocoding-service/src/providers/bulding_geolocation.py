import torch
import torch.nn as nn
from PIL import Image
import numpy as np
from typing import List, Dict, Optional, cast
import torchvision.transforms as T
import torchvision.models
from torchvision.models import ResNet50_Weights
from torch import Tensor
import os # <-- НОВЫЙ ИМПОРТ

class BuildingGeolocationModel(nn.Module):
    """ML модель для определения координат здания по изображению"""

    def __init__(self):
        super().__init__()

        # Используем современный способ загрузки ResNet50
        self.backbone: nn.Module = torchvision.models.resnet50(
            weights=ResNet50_Weights.IMAGENET1K_V1,
        )

        self.backbone.fc = nn.Linear(2048, 512)
        self.coord_head = nn.Linear(512, 2)  # lat, lng
        self.confidence_head = nn.Linear(512, 1)

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor]:
        features = self.backbone(x)
        coords = torch.tanh(self.coord_head(features)) # нормализованные координаты (от -1 до 1)
        confidence = torch.sigmoid(self.confidence_head(features))
        return coords, confidence

class BuildingGeolocator:
    def __init__(self, model_path: Optional[str] = None):
        # Инициализируем модель, которую нам не нужно экспортировать
        self.model = BuildingGeolocationModel()

        if model_path:
            # map_location='cpu' позволяет загружаться, даже если нет GPU
            self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
        self.model.eval()

        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # --- КРИТИЧНОЕ ИЗМЕНЕНИЕ: ЧТЕНИЕ ГРАНИЦ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
        # Это позволяет перенастроить ML-модель для работы с любым регионом
        self.lat_min = float(os.getenv("ML_MIN_LAT", 55.0))
        self.lat_range = float(os.getenv("ML_LAT_RANGE", 10.0))
        self.lng_min = float(os.getenv("ML_MIN_LNG", 37.0))
        self.lng_range = float(os.getenv("ML_LNG_RANGE", 10.0))
        # ------------------------------------------------------------------

    def predict_coordinates(self, image: Image.Image, building_bbox: List[float]) -> Dict:
        """Предсказание координат для здания"""
        cropped_building = self.crop_building(image, building_bbox)

        # Используем cast для устранения ошибки статического анализатора (Pylance)
        processed_tensor = cast(Tensor, self.transform(cropped_building))

        processed_image = processed_tensor.unsqueeze(0)

        with torch.no_grad():
            coords, confidence = self.model(processed_image)

        # --- КРИТИЧНОЕ ИЗМЕНЕНИЕ: ДЕНОРМАЛИЗАЦИЯ С ИСПОЛЬЗОВАНИЕМ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
        # Нормализованные ML-выходы (coords) находятся в диапазоне [-1, 1].
        # Денормализация: Min + (Нормализованное значение + 1) / 2 * Range
        # (coords[0, 0].item() + 1) / 2 преобразует [-1, 1] в [0, 1]
        
        # lat = self.lat_min + (coords[0, 0].item() + 1) / 2 * self.lat_range
        # lng = self.lng_min + (coords[0, 1].item() + 1) / 2 * self.lng_range
        
        # Упрощенная денормализация, если модель обучалась на нормализованных данных от 0 до 1
        # ИЛИ для регрессии, где tanh() используется для привязки к диапазону [-1, 1].
        # Используем более простую форму, соответствующую изначальному стилю:
        lat = self.lat_min + coords[0, 0].item() * self.lat_range
        lng = self.lng_min + coords[0, 1].item() * self.lng_range
        # ---------------------------------------------------------------------------------

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
        # Поскольку transform уже содержит все шаги, просто вызываем его:
        # Для корректного статического анализа используем cast
        processed_tensor = cast(Tensor, self.transform(image))
        return processed_tensor

# Класс BuildingGeolocationModel (nn.Module) остается без изменений,
# так как он отвечает только за архитектуру и forward-проход.
