import os
from PIL import Image
import cv2
import numpy as np

def validate_image(file_path: str) -> tuple:
    """Валидация изображения"""
    try:
        with Image.open(file_path) as img:
            img.verify()
        
        # Проверка размера файла
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # в MB
        if file_size > 50:  # Максимум 50MB
            return False, "Файл слишком большой"
            
        return True, "Изображение валидно"
        
    except Exception as e:
        return False, f"Невалидное изображение: {e}"

def resize_image_for_processing(image_path: str, max_size: tuple = (1024, 1024)) -> str:
    """Изменение размера изображения для обработки"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Сохраняем временную копию
            temp_path = f"{image_path}_resized.jpg"
            img.save(temp_path, "JPEG", quality=85)
            
            return temp_path
            
    except Exception as e:
        print(f"❌ Ошибка изменения размера: {e}")
        return image_path

def get_image_dimensions(image_path: str) -> tuple:
    """Получение размеров изображения"""
    try:
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception as e:
        print(f"❌ Ошибка получения размеров: {e}")
        return (0, 0)