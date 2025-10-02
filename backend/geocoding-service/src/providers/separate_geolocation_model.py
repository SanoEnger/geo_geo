# separate_geolocation_model.py
import torch
import torch.nn as nn

class BuildingGeolocationModel(nn.Module):
    """ML модель для определения региона по архитектуре здания"""
    
    def __init__(self, num_regions=100):
        super().__init__()
        self.backbone = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.region_classifier = nn.Linear(1024, num_regions)  # классификация региона
        self.coord_regressor = nn.Linear(1024, 2)  # координаты внутри региона
    
    def predict_region_and_coords(self, building_image):
        """Предсказание региона и координат по изображению здания"""
        # Используем фичи от YOLO + дополнительная классификация
        features = self.backbone(building_image)
        region_probs = torch.softmax(self.region_classifier(features), dim=1)
        coords = torch.tanh(self.coord_regressor(features))
        
        return region_probs, coords