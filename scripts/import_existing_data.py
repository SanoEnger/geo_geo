import pandas as pd
import os
import psycopg2
from datetime import datetime
import uuid
import time

def wait_for_database(max_retries=10, retry_interval=5):
    """Ожидание готовности базы данных"""
    print("🔄 Ожидание готовности базы данных...")
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5432", 
                dbname="geo_photo_db",
                user="admin",
                password="admin123",
                connect_timeout=5
            )
            cursor = conn.cursor()
            
            # Проверяем что таблицы существуют
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'datasets', 'photo_metadata')
            """)
            
            table_count = cursor.fetchone()[0]
            
            if table_count >= 3:
                print("✅ База данных готова!")
                cursor.close()
                conn.close()
                return True
            else:
                print(f"⏳ Таблицы еще не созданы ({table_count}/3), ждем...")
                
        except Exception as e:
            print(f"⏳ База данных недоступна (попытка {attempt + 1}/{max_retries}): {e}")
        
        time.sleep(retry_interval)
    
    print("❌ База данных не готова после всех попыток")
    return False

def import_existing_data():
    """Импорт существующих данных из Excel и папок"""
    
    # Ждем готовности БД
    if not wait_for_database():
        return
    
    # Подключение к БД
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="geo_photo_db", 
            user="admin",
            password="admin123"
        )
        cursor = conn.cursor()
        
        print("🔄 Начинаем импорт существующих данных...")
        
        # Импорт данных из Excel файлов
        excel_files = [
            "data/raw/dataset_1/18-001_gin_building_echd_19.08.25.xlsx",
            "data/raw/dataset_2/19-001_gin_garbage_echd_19.08.25.xlsx"
        ]
        
        for excel_file in excel_files:
            if os.path.exists(excel_file):
                print(f"📊 Импорт данных из {excel_file}")
                import_excel_data(cursor, conn, excel_file)
            else:
                print(f"⚠️ Файл не найден: {excel_file}")
        
        # Импорт информации о фото из папок
        photo_folders = [
            "data/raw/dataset_1/18-001_gin_building_echd_19.08.25",
            "data/raw/dataset_2/19-001_gin_garbage_echd_19.08.25", 
            "data/raw/bpla_bbox"
        ]
        
        for folder in photo_folders:
            if os.path.exists(folder):
                print(f"📸 Импорт фото из {folder}")
                import_photos_from_folder(cursor, conn, folder)
            else:
                print(f"⚠️ Папка не найдена: {folder}")
        
        conn.commit()
        print("✅ Импорт данных завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def import_excel_data(cursor, conn, excel_file):
    """Импорт данных из Excel файла"""
    try:
        # Читаем Excel файл
        df = pd.read_excel(excel_file)
        print(f"📋 Найдено {len(df)} записей в {excel_file}")
        
        # Анализируем структуру данных
        print("Структура данных:")
        for col in df.columns:
            sample_value = df[col].iloc[0] if len(df) > 0 else 'N/A'
            print(f"  - {col}: {df[col].dtype}, пример: {sample_value}")
        
        # Определяем тип датасета по имени файла
        if "building" in excel_file.lower():
            dataset_type = "building"
            dataset_name = "dataset_1_buildings"
        elif "garbage" in excel_file.lower():
            dataset_type = "garbage" 
            dataset_name = "dataset_2_garbage"
        else:
            dataset_type = "unknown"
            dataset_name = os.path.basename(excel_file).replace('.xlsx', '')
        
        # Создаем или получаем датасет
        dataset_id = get_or_create_dataset(cursor, conn, dataset_name, dataset_type)
        
        # Импортируем записи из Excel
        imported_count = 0
        for index, row in df.iterrows():
            try:
                # Извлекаем данные из строки
                filename = row['Имя файла']
                latitude = row['latitude'] if pd.notna(row['latitude']) else None
                longitude = row['longitude'] if pd.notna(row['longitude']) else None
                camera_id = row['camera'] if pd.notna(row['camera']) else None
                
                # Полный путь к файлу
                folder_name = "dataset_1" if dataset_type == "building" else "dataset_2"
                file_path = f"data/raw/{folder_name}/{os.path.basename(excel_file).replace('.xlsx', '')}/{filename}"
                
                # Проверяем существует ли файл
                file_exists = os.path.exists(file_path)
                
                # Вставляем или обновляем запись о фото
                cursor.execute("""
                    INSERT INTO photo_metadata 
                    (dataset_id, original_filename, file_path, file_size, 
                     gps_latitude, gps_longitude, processing_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (file_path) DO UPDATE SET
                    gps_latitude = EXCLUDED.gps_latitude,
                    gps_longitude = EXCLUDED.gps_longitude,
                    updated_at = CURRENT_TIMESTAMP
                """, (
                    dataset_id,
                    filename,
                    file_path,
                    os.path.getsize(file_path) if file_exists else 0,
                    latitude,
                    longitude,
                    'pending' if file_exists else 'file_not_found'
                ))
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    print(f"  ⏳ Обработано {imported_count} записей...")
                    conn.commit()
                    
            except Exception as e:
                print(f"  ⚠️ Ошибка обработки строки {index}: {e}")
                continue
        
        print(f"  ✅ Импортировано {imported_count} записей из Excel")
        conn.commit()
        
    except Exception as e:
        print(f"❌ Ошибка чтения Excel {excel_file}: {e}")
        raise

def get_or_create_dataset(cursor, conn, dataset_name, dataset_type):
    """Получаем или создаем датасет"""
    try:
        # Пробуем найти существующий датасет
        cursor.execute("SELECT id FROM datasets WHERE name = %s", (dataset_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # Создаем новый датасет
            cursor.execute("""
                INSERT INTO datasets (name, description, source_type, created_by) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id
            """, (
                dataset_name,
                f"Датасет {dataset_type} из импорта",
                'archive', 
                1
            ))
            dataset_id = cursor.fetchone()[0]
            conn.commit()
            print(f"  ✅ Создан новый датасет: {dataset_name} (ID: {dataset_id})")
            return dataset_id
            
    except Exception as e:
        print(f"❌ Ошибка создания датасета {dataset_name}: {e}")
        raise

def import_photos_from_folder(cursor, conn, folder_path):
    """Импорт информации о фото из папки"""
    try:
        photo_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        
        dataset_name = os.path.basename(folder_path)
        
        # Получаем или создаем датасет
        dataset_id = get_or_create_dataset(cursor, conn, dataset_name, "folder_import")
        
        # Сканируем папку с фото
        photo_count = 0
        for filename in os.listdir(folder_path):
            if any(filename.lower().endswith(ext) for ext in photo_extensions):
                file_path = os.path.join(folder_path, filename)
                
                try:
                    # Вставляем запись о фото
                    cursor.execute("""
                        INSERT INTO photo_metadata 
                        (dataset_id, original_filename, file_path, file_size, processing_status)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (file_path) DO NOTHING
                    """, (
                        dataset_id,
                        filename,
                        file_path,
                        os.path.getsize(file_path),
                        'pending'
                    ))
                    
                    if cursor.rowcount > 0:
                        photo_count += 1
                    
                    if photo_count % 100 == 0:
                        print(f"  ⏳ Обработано {photo_count} фото...")
                        conn.commit()
                        
                except Exception as e:
                    print(f"  ⚠️ Ошибка обработки файла {filename}: {e}")
                    continue
        
        conn.commit()
        print(f"  ✅ Добавлено {photo_count} фото в датасет '{dataset_name}'")
        
    except Exception as e:
        print(f"❌ Ошибка импорта из папки {folder_path}: {e}")
        raise

if __name__ == "__main__":
    import_existing_data()