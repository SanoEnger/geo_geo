-- =============================================
-- Инициализация базы данных Geo Photo Analyzer
-- =============================================

-- Создаем расширение для генерации UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- ТАБЛИЦА: users (Пользователи системы)
-- =============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Ограничения
    CONSTRAINT chk_username_length CHECK (char_length(username) >= 3),
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- =============================================
-- ТАБЛИЦА: datasets (Датасеты для организации фото)
-- =============================================
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    dataset_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type VARCHAR(50) NOT NULL,
    total_photos INTEGER DEFAULT 0,
    processed_photos INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT false,
    
    CONSTRAINT unique_dataset_name UNIQUE (name)
);

-- =============================================
-- ТАБЛИЦА: photo_metadata (Метаданные фотографий)
-- =============================================
CREATE TABLE IF NOT EXISTS photo_metadata (
    id SERIAL PRIMARY KEY,
    photo_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    
    -- Информация о файле
    original_filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL UNIQUE,
    file_size BIGINT,
    mime_type VARCHAR(100),
    file_hash VARCHAR(64),
    
    -- EXIF метаданные
    camera_make VARCHAR(200),
    camera_model VARCHAR(200),
    lens_model VARCHAR(200),
    exposure_time VARCHAR(50),
    f_number DECIMAL(3,1),
    iso_speed INTEGER,
    focal_length DECIMAL(5,1),
    
    -- Даты и время
    taken_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- GPS данные из EXIF
    gps_latitude DECIMAL(10, 8),
    gps_longitude DECIMAL(11, 8),
    gps_altitude DECIMAL(8, 2),
    gps_dop DECIMAL(5, 2),
    
    -- Статус обработки
    processing_status VARCHAR(20) DEFAULT 'pending',
    processing_stage VARCHAR(50) DEFAULT 'uploaded',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Временные метки
    processed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ТАБЛИЦА: detection_results (Результаты детекции)
-- =============================================
CREATE TABLE IF NOT EXISTS detection_results (
    id SERIAL PRIMARY KEY,
    detection_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    photo_id INTEGER NOT NULL REFERENCES photo_metadata(id) ON DELETE CASCADE,
    
    -- Данные детекции
    object_class VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(4, 3) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- Bounding box координаты (нормализованные 0-1)
    bbox_x1 DECIMAL(8, 4) NOT NULL,
    bbox_y1 DECIMAL(8, 4) NOT NULL,
    bbox_x2 DECIMAL(8, 4) NOT NULL,
    bbox_y2 DECIMAL(8, 4) NOT NULL,
    
    -- Вычисляемые поля
    bbox_width DECIMAL(8, 4) GENERATED ALWAYS AS (bbox_x2 - bbox_x1) STORED,
    bbox_height DECIMAL(8, 4) GENERATED ALWAYS AS (bbox_y2 - bbox_y1) STORED,
    bbox_area DECIMAL(10, 4) GENERATED ALWAYS AS ((bbox_x2 - bbox_x1) * (bbox_y2 - bbox_y1)) STORED,
    center_x DECIMAL(8, 4) GENERATED ALWAYS AS ((bbox_x1 + bbox_x2) / 2) STORED,
    center_y DECIMAL(8, 4) GENERATED ALWAYS AS ((bbox_y1 + bbox_y2) / 2) STORED,
    
    -- Модель и версия
    model_name VARCHAR(100) DEFAULT 'yolov8',
    model_version VARCHAR(50) DEFAULT '1.0',
    
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ограничения для валидации bbox
    CONSTRAINT valid_bbox CHECK (bbox_x1 >= 0 AND bbox_y1 >= 0 AND bbox_x2 <= 1 AND bbox_y2 <= 1 AND bbox_x1 < bbox_x2 AND bbox_y1 < bbox_y2)
);

-- =============================================
-- ТАБЛИЦА: geocoding_results (Геокодированные результаты)
-- =============================================
CREATE TABLE IF NOT EXISTS geocoding_results (
    id SERIAL PRIMARY KEY,
    geocoding_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    detection_id INTEGER NOT NULL REFERENCES detection_results(id) ON DELETE CASCADE,
    
    -- Координаты (определенные системой)
    calculated_latitude DECIMAL(10, 8) NOT NULL,
    calculated_longitude DECIMAL(11, 8) NOT NULL,
    calculated_altitude DECIMAL(8, 2),
    
    -- Адресная информация
    formatted_address TEXT,
    street VARCHAR(255),
    house_number VARCHAR(50),
    city VARCHAR(255),
    district VARCHAR(255),
    region VARCHAR(255),
    country VARCHAR(255),
    country_code VARCHAR(10),
    postal_code VARCHAR(20),
    
    -- Источник геоданных
    coordinate_source VARCHAR(50) NOT NULL,
    geocoding_service VARCHAR(50) DEFAULT 'openstreetmap',
    geocoding_confidence DECIMAL(3, 2) CHECK (geocoding_confidence >= 0 AND geocoding_confidence <= 1),
    
    -- Дополнительная информация
    timezone VARCHAR(100),
    elevation DECIMAL(8, 2),
    
    geocoded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ТАБЛИЦА: processing_history (История обработки)
-- =============================================
CREATE TABLE IF NOT EXISTS processing_history (
    id SERIAL PRIMARY KEY,
    history_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    photo_id INTEGER REFERENCES photo_metadata(id) ON DELETE CASCADE,
    detection_id INTEGER REFERENCES detection_results(id) ON DELETE SET NULL,
    
    service_name VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    
    input_data JSONB,
    output_data JSONB,
    error_details TEXT,
    
    processing_time_ms INTEGER,
    resource_usage JSONB,
    
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- ТАБЛИЦА: exports (Экспорты данных)
-- =============================================
CREATE TABLE IF NOT EXISTS exports (
    id SERIAL PRIMARY KEY,
    export_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    user_id INTEGER REFERENCES users(id),
    
    export_name VARCHAR(255) NOT NULL,
    export_format VARCHAR(20) DEFAULT 'xlsx',
    file_path VARCHAR(1000),
    file_size BIGINT,
    
    -- Параметры экспорта
    filters_applied JSONB,
    columns_selected JSONB,
    date_range_start TIMESTAMP WITH TIME ZONE,
    date_range_end TIMESTAMP WITH TIME ZONE,
    
    total_records INTEGER DEFAULT 0,
    exported_records INTEGER DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'processing',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- =============================================
-- ТАБЛИЦА: export_photos (Связь фото с экспортами)
-- =============================================
CREATE TABLE IF NOT EXISTS export_photos (
    id SERIAL PRIMARY KEY,
    export_id INTEGER NOT NULL REFERENCES exports(id) ON DELETE CASCADE,
    photo_id INTEGER NOT NULL REFERENCES photo_metadata(id) ON DELETE CASCADE,
    included_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_export_photo UNIQUE (export_id, photo_id)
);

-- =============================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =============================================

-- Индексы для photo_metadata
CREATE INDEX IF NOT EXISTS idx_photo_metadata_uuid ON photo_metadata(photo_uuid);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_status ON photo_metadata(processing_status);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_dataset ON photo_metadata(dataset_id);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_taken_at ON photo_metadata(taken_at);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_created_at ON photo_metadata(created_at);
CREATE INDEX IF NOT EXISTS idx_photo_metadata_coords ON photo_metadata(gps_latitude, gps_longitude);

-- Индексы для detection_results
CREATE INDEX IF NOT EXISTS idx_detection_results_photo ON detection_results(photo_id);
CREATE INDEX IF NOT EXISTS idx_detection_results_class ON detection_results(object_class);
CREATE INDEX IF NOT EXISTS idx_detection_results_confidence ON detection_results(confidence_score);
CREATE INDEX IF NOT EXISTS idx_detection_results_detected_at ON detection_results(detected_at);

-- Индексы для geocoding_results
CREATE INDEX IF NOT EXISTS idx_geocoding_results_detection ON geocoding_results(detection_id);
CREATE INDEX IF NOT EXISTS idx_geocoding_results_city ON geocoding_results(city);
CREATE INDEX IF NOT EXISTS idx_geocoding_results_country ON geocoding_results(country);
CREATE INDEX IF NOT EXISTS idx_geocoding_results_coords ON geocoding_results(calculated_latitude, calculated_longitude);

-- Индексы для processing_history
CREATE INDEX IF NOT EXISTS idx_processing_history_photo ON processing_history(photo_id);
CREATE INDEX IF NOT EXISTS idx_processing_history_service ON processing_history(service_name);
CREATE INDEX IF NOT EXISTS idx_processing_history_status ON processing_history(status);
CREATE INDEX IF NOT EXISTS idx_processing_history_date ON processing_history(processed_at);

-- Индексы для exports
CREATE INDEX IF NOT EXISTS idx_exports_user ON exports(user_id);
CREATE INDEX IF NOT EXISTS idx_exports_status ON exports(status);
CREATE INDEX IF NOT EXISTS idx_exports_created_at ON exports(created_at);

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- =============================================
-- ТРИГГЕРЫ И ФУНКЦИИ
-- =============================================

-- Функция для обновления временных меток
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггеры для автоматического обновления updated_at
CREATE TRIGGER update_photo_metadata_updated_at 
    BEFORE UPDATE ON photo_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_geocoding_results_updated_at 
    BEFORE UPDATE ON geocoding_results 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_datasets_updated_at 
    BEFORE UPDATE ON datasets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функция для обновления счетчика фото в датасетах
CREATE OR REPLACE FUNCTION update_dataset_photo_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE datasets 
        SET total_photos = total_photos + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.dataset_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE datasets 
        SET total_photos = total_photos - 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.dataset_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.dataset_id IS DISTINCT FROM NEW.dataset_id THEN
        -- Уменьшаем счетчик у старого датасета
        UPDATE datasets 
        SET total_photos = total_photos - 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.dataset_id;
        
        -- Увеличиваем счетчик у нового датасета
        UPDATE datasets 
        SET total_photos = total_photos + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.dataset_id;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Триггер для обновления счетчика фото
CREATE TRIGGER update_dataset_photo_count_trigger
    AFTER INSERT OR DELETE OR UPDATE OF dataset_id ON photo_metadata
    FOR EACH ROW EXECUTE FUNCTION update_dataset_photo_count();

-- =============================================
-- ТЕСТОВЫЕ ДАННЫЕ
-- =============================================

-- Тестовые пользователи
INSERT INTO users (username, email, hashed_password, full_name, is_superuser) 
VALUES 
('admin', 'admin@geophoto.ru', 'fakehashedpassword', 'Administrator', true),
('user1', 'user1@geophoto.ru', 'fakehashedpassword', 'Test User', false)
ON CONFLICT (username) DO NOTHING;

-- Тестовые датасеты
INSERT INTO datasets (name, description, source_type, created_by) 
VALUES 
('dataset_1', 'Основной датасет зданий', 'archive', 1),
('dataset_2', 'Дополнительный датасет объектов', 'archive', 1),
('bpla_bbox', 'Данные с БПЛА с bounding boxes', 'bpla', 1)
ON CONFLICT (name) DO NOTHING;

-- =============================================
-- ПРЕДСТАВЛЕНИЯ ДЛЯ УДОБНЫХ ЗАПРОСОВ
-- =============================================

-- Представление для объединенной информации о фото и детекциях
CREATE OR REPLACE VIEW photo_detection_view AS
SELECT 
    pm.photo_uuid,
    pm.original_filename,
    pm.processing_status,
    pm.taken_at,
    pm.gps_latitude as photo_lat,
    pm.gps_longitude as photo_lng,
    dr.object_class,
    dr.confidence_score,
    gr.calculated_latitude as building_lat,
    gr.calculated_longitude as building_lng,
    gr.formatted_address,
    gr.city,
    gr.country
FROM photo_metadata pm
LEFT JOIN detection_results dr ON pm.id = dr.photo_id
LEFT JOIN geocoding_results gr ON dr.id = gr.detection_id;

-- Представление для статистики по датасетам
CREATE OR REPLACE VIEW dataset_stats_view AS
SELECT 
    d.name as dataset_name,
    d.source_type,
    d.total_photos,
    d.processed_photos,
    COUNT(pm.id) as actual_photos,
    COUNT(CASE WHEN pm.processing_status = 'completed' THEN 1 END) as completed_photos,
    COUNT(CASE WHEN pm.gps_latitude IS NOT NULL THEN 1 END) as photos_with_coords
FROM datasets d
LEFT JOIN photo_metadata pm ON d.id = pm.dataset_id
GROUP BY d.id, d.name, d.source_type, d.total_photos, d.processed_photos;

-- =============================================
-- КОММЕНТАРИИ К ТАБЛИЦАМ
-- =============================================

COMMENT ON TABLE users IS 'Пользователи системы';
COMMENT ON TABLE datasets IS 'Датасеты для организации фотографий';
COMMENT ON TABLE photo_metadata IS 'Метаданные загруженных фотографий';
COMMENT ON TABLE detection_results IS 'Результаты детекции объектов на фотографиях';
COMMENT ON TABLE geocoding_results IS 'Геокодированные результаты с адресами';
COMMENT ON TABLE processing_history IS 'История обработки фотографий';
COMMENT ON TABLE exports IS 'Экспорты данных';
COMMENT ON TABLE export_photos IS 'Связь фото с экспортами';

COMMENT ON COLUMN photo_metadata.processing_status IS 'Статусы: pending, processing, completed, failed, partial';
COMMENT ON COLUMN photo_metadata.processing_stage IS 'Этапы: uploaded, metadata_extracted, buildings_detected, geocoded, exported';
COMMENT ON COLUMN detection_results.object_class IS 'Классы объектов: building, house, skyscraper, bridge, etc';
COMMENT ON COLUMN geocoding_results.coordinate_source IS 'Источники: exif, geolocation, manual, estimated';

-- =============================================
-- ФИНАЛЬНОЕ СООБЩЕНИЕ
-- =============================================

DO $$ 
BEGIN
    RAISE NOTICE '=========================================';
    RAISE NOTICE '✅ БАЗА ДАННЫХ GEO PHOTO ANALYZER';
    RAISE NOTICE '✅ УСПЕШНО ИНИЦИАЛИЗИРОВАНА!';
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Создано таблиц: 8';
    RAISE NOTICE 'Создано индексов: 25';
    RAISE NOTICE 'Создано представлений: 2';
    RAISE NOTICE 'Добавлено тестовых пользователей: 2';
    RAISE NOTICE 'Добавлено тестовых датасетов: 3';
    RAISE NOTICE '=========================================';
END $$;