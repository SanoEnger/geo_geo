import apiClient from './client'

export const photoService = {
  // Загрузка одного фото
  async uploadPhoto(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/photo_upload/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    const apiData = response.data;
    
    console.log('📊 API Response structure:', apiData.cv_results);
    
    if (apiData.cv_results && apiData.cv_results.status === 'success') {
      // Успешная CV обработка - ТЕПЕРЬ ДОБАВЛЯЕМ ГЕОКОДИРОВАНИЕ
      let buildingsWithGeocoding = apiData.cv_results.buildings;
      
      // Если есть здания - пытаемся их геокодировать
      if (buildingsWithGeocoding && buildingsWithGeocoding.length > 0) {
        try {
          const geocodingResult = await this.geocodeDetectedBuildings(
            apiData.file_id, 
            buildingsWithGeocoding
          );
          buildingsWithGeocoding = geocodingResult.buildings;
        } catch (error) {
          console.warn('Geocoding failed, using buildings without coordinates:', error);
        }
      }
      
      // Берем координаты первого здания для общего отображения
      const firstBuilding = buildingsWithGeocoding[0];
      
      return {
        success: true,
        data: {
          file_id: apiData.file_id,
          original_filename: apiData.original_name,
          status: 'completed',
          buildings_detected: apiData.cv_results.buildings_detected,
          buildings: buildingsWithGeocoding, // ← здания с координатами!
          coordinates: firstBuilding?.coordinates || null,
          address: firstBuilding?.address || null,
          full_response: apiData
        }
      };
    } else if (apiData.cv_results && apiData.cv_results.status === 'error') {
      // Ошибка CV обработки
      return {
        success: false,
        error: 'CV processing failed',
        data: {
          file_id: apiData.file_id,
          original_filename: apiData.original_name,
          status: 'failed',
          buildings_detected: 0,
          error: 'CV processing failed'
        }
      };
    } else {
      return {
        success: false,
        error: 'Неизвестный формат ответа от сервера',
        data: apiData
      };
    }
  },

  async geocodeDetectedBuildings(fileId, buildings) {
    try {
      const requests = buildings.map((building, index) => ({
        file_id: `${fileId}_building_${index}`,
        building: {
          bbox: building.bbox,
          center: building.center,
          area: building.area,
          confidence: building.confidence,
          class_name: building.class || "building"
        },
        image_metadata: {
          file_id: fileId,
          building_index: index
        }
      }));

      const response = await apiClient.post('/geocoding/geocode-buildings', requests);
      return response.data;
    } catch (error) {
      console.error('Geocoding error:', error);
      // Возвращаем здания без координат в случае ошибки
      return {
        buildings: buildings.map(building => ({
          ...building,
          coordinates: null,
          address: null,
          geocoding_error: error.message
        }))
      };
    }
  },

  // Пакетная загрузка
  async uploadBatch(files) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    const response = await apiClient.post('/photo_upload/upload/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 300000 // 5 минут для пакетной загрузки
    })
    
    return response.data
  },

  // Обработка фото через CV сервис
  async processPhoto(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post(`/cv_processing/process-image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // Получение списка загруженных файлов
  async getUploadedFiles() {
    const response = await apiClient.get('/photo_upload/files')
    return response.data
  }
}

// Сервис для геокодирования
export const geocodingService = {
  // Геокодирование адреса
  async geocodeAddress(address) {
    const response = await apiClient.get('/geocoding/geocode', {
      params: { address }
    })
    return response.data
  },

  // Обратное геокодирование
  async reverseGeocode(lat, lng) {
    const response = await apiClient.get('/geocoding/reverse-geocode', {
      params: { lat, lng }
    })
    return response.data
  },

  async geocodeBuilding(fileId, buildingData) {
    const response = await apiClient.post('/geocoding/geocode-building', {
      file_id: fileId,
      building: buildingData
    })
    return response.data
  },

  // Получение высоты
  async getElevation(lat, lng) {
    const response = await apiClient.get('/geocoding/elevation', {
      params: { lat, lng }
    })
    return response.data
  }
}

// Сервис для работы с датасетами
export const datasetService = {
  // Получение списка датасетов
  async getDatasets() {
    const response = await apiClient.get('/datasets')
    return response.data
  },

  // Создание датасета
  async createDataset(name, description) {
    const response = await apiClient.post('/datasets', {
      name,
      description,
      source_type: 'upload'
    })
    return response.data
  }
}

// Сервис аутентификации
export const authService = {
  // Вход в систему
  async login(username, password) {
    const response = await apiClient.post('/auth/login', null, {
      params: { username, password }
    })
    return response.data
  },

  // Получение информации о текущем пользователе
  async getCurrentUser() {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  // Регистрация
  async register(username, email, password) {
    const response = await apiClient.post('/auth/register', null, {
      params: { username, email, password }
    })
    return response.data
  }
}

// Проверка здоровья сервисов
export const healthService = {
  async checkAllServices() {
    const response = await apiClient.get('/health')
    return response.data
  }
}

