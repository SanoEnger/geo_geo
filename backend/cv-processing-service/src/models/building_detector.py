import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image, ExifTags
import json
from typing import List, Dict, Optional
import os

class BuildingDetector:
    def __init__(self, model_path: str = 'yolov8n.pt'):
        """Инициализация YOLO детектора зданий"""
        print("🔄 Загрузка YOLO модели...")
        self.model = YOLO(model_path)
        print(f"✅ Модель {model_path} загружена")
        
        # Классы объектов для детекции зданий
        self.building_classes = ['building', 'house', 'skyscraper', 'bridge']

    def extract_metadata(self, image_path: str) -> Dict:
        """Извлечение метаданных из изображения"""
        try:
            with Image.open(image_path) as img:
                metadata = {
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode,
                    'filename': os.path.basename(image_path),
                    'file_size': os.path.getsize(image_path)
                }
                
                # EXIF данные
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    for tag_id, value in img._getexif().items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
                    
                    # GPS данные
                    gps_info = self._extract_gps_info(exif_data)
                    if gps_info:
                        metadata['gps'] = gps_info
                
                metadata['exif'] = exif_data
                return metadata
                
        except Exception as e:
            print(f"❌ Ошибка извлечения метаданных: {e}")
            return {}

    def _extract_gps_info(self, exif_data: Dict) -> Optional[Dict]:
        """Извлечение GPS информации из EXIF данных"""
        try:
            if 'GPSInfo' not in exif_data:
                return None
                
            gps_info = {}
            gps_data = exif_data['GPSInfo']
            
            # Извлечение координат
            def convert_to_degrees(value):
                """Конвертация GPS координат в градусы"""
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            # Широта
            if 2 in gps_data and 1 in gps_data:
                lat_ref = gps_data[1]
                lat = convert_to_degrees(gps_data[2])
                if lat_ref == 'S':
                    lat = -lat
                gps_info['latitude'] = lat
            
            # Долгота
            if 4 in gps_data and 3 in gps_data:
                lon_ref = gps_data[3]
                lon = convert_to_degrees(gps_data[4])
                if lon_ref == 'W':
                    lon = -lon
                gps_info['longitude'] = lon
            
            # Высота
            if 6 in gps_data:
                gps_info['altitude'] = gps_data[6]
                
            return gps_info
            
        except Exception as e:
            print(f"⚠️ Ошибка извлечения GPS: {e}")
            return None

    def detect_buildings(self, image_path: str) -> List[Dict]:
        """Детекция зданий на изображении"""
        try:
            # Проверяем существование файла
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Файл не найден: {image_path}")
            
            # Детекция с помощью YOLO
            results = self.model(image_path, conf=0.5)
            
            buildings = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    
                    # Фильтруем только здания
                    if class_name in self.building_classes:
                        confidence = float(box.conf[0])
                        bbox = box.xyxy[0].tolist()
                        
                        buildings.append({
                            'class': class_name,
                            'confidence': round(confidence, 3),
                            'bbox': [round(coord, 2) for coord in bbox],  # [x1, y1, x2, y2]
                            'center': self._get_center(bbox),
                            'area': self._calculate_area(bbox, result.orig_shape)
                        })
            
            print(f"🏢 Найдено зданий: {len(buildings)}")
            return buildings
            
        except Exception as e:
            print(f"❌ Ошибка детекции: {e}")
            return []

    def _get_center(self, bbox: List[float]) -> List[float]:
        """Вычисляем центр bounding box"""
        x1, y1, x2, y2 = bbox
        return [round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2)]

    def _calculate_area(self, bbox: List[float], image_shape: tuple) -> float:
        """Вычисляем площадь bounding box в процентах от изображения"""
        x1, y1, x2, y2 = bbox
        img_height, img_width = image_shape
        area = (x2 - x1) * (y2 - y1) / (img_width * img_height)
        return round(area * 100, 2)  # в процентах

    def process_image(self, image_path: str, output_dir: str = None) -> Dict:
        """Полная обработка изображения"""
        # Извлекаем метаданные
        metadata = self.extract_metadata(image_path)
        
        # Детекция зданий
        buildings = self.detect_buildings(image_path)
        
        # Визуализация результатов (если указана выходная директория)
        processed_image_path = None
        if output_dir and buildings:
            processed_image_path = self.visualize_detection(image_path, output_dir, buildings)
        
        return {
            'metadata': metadata,
            'buildings_detected': len(buildings),
            'buildings': buildings,
            'processed_image_path': processed_image_path
        }

    def visualize_detection(self, image_path: str, output_dir: str, buildings: List[Dict]) -> str:
        """Визуализация детекций на изображении"""
        try:
            image = cv2.imread(image_path)
            
            for building in buildings:
                x1, y1, x2, y2 = map(int, building['bbox'])
                confidence = building['confidence']
                class_name = building['class']
                
                # Рисуем bounding box
                color = (0, 255, 0)  # Зеленый
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Подпись
                label = f"{class_name} {confidence:.2f}"
                cv2.putText(image, label, (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Сохраняем результат
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, f"detected_{filename}")
            cv2.imwrite(output_path, image)
            print(f"📸 Результат сохранен: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Ошибка визуализации: {e}")
            return None