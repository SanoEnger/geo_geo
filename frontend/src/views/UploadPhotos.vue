<template>
  <div class="upload-photos">
    <div class="container">
      <div class="page-header">
        <h1>Загрузка фотографий</h1>
        <p>Загрузите фотографии для автоматического определения координат объектов</p>
      </div>

      <FileUpload 
        @upload-complete="handleUploadComplete"
        @photo-processed="handlePhotoProcessed"
      />

      <div v-if="processingResults.length > 0" class="results-section">
        <h2>Результаты обработки</h2>
        <div class="results-grid">
          <div 
            v-for="result in processingResults" 
            :key="result.file_id"
            class="result-card"
          >
            <div class="result-header">
              <h4>{{ result.original_filename }}</h4>
              <el-tag :type="getStatusType(result.status)">
                {{ getStatusText(result.status) }}
              </el-tag>
            </div>
            
            <div v-if="result.buildings_detected > 0" class="result-details">
              <p>🏢 Найдено зданий: {{ result.buildings_detected }}</p>
              <p v-if="result.coordinates">📍 Координаты: {{ result.coordinates.lat }}, {{ result.coordinates.lng }}</p>
              <p v-if="result.address">🏠 Адрес: {{ result.address }}</p>
              <p v-if="result.geocoding_note" class="note">ℹ️ **Нота:** {{ result.geocoding_note }}</p>
            </div>

            <div v-else class="no-buildings">
              <p>❌ Здания не обнаружены</p>
              <p v-if="result.geocoding_note"><small>Нота геокодирования: {{ result.geocoding_note }}</small></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
import FileUpload from '@/components/FileUpload.vue'
import { useAppStore } from '@/stores/app'

export default {
  name: 'UploadPhotos',
  components: {
    FileUpload
  },
  data() {
    return {
      processingResults: []
    }
  },
  setup() {
    const appStore = useAppStore()
    return { appStore }
  },
  methods: {
    handleUploadComplete(results) {
      console.log('Upload complete:', results)
      ElMessage.success(`Загрузка завершена! Обработано ${results.length} файлов`)
    },

    handlePhotoProcessed(apiResult) {
      const geocodingResult = apiResult.geocoding_result;
      
      // КРИТЕРИЙ УСПЕХА: Проверяем наличие объекта coordinates.
      const isBuildingGeocoded = geocodingResult 
          && geocodingResult.success === true 
          && geocodingResult.coordinates
          && typeof geocodingResult.coordinates.latitude === 'number'; // Дополнительная проверка типа
          
      const processedData = {
          file_id: apiResult.file_id,
          original_filename: apiResult.filename,
          status: 'completed', 
          
          buildings_detected: isBuildingGeocoded ? 1 : 0, 
          
          coordinates: isBuildingGeocoded ? { 
              lat: geocodingResult.coordinates.latitude.toFixed(4), 
              lng: geocodingResult.coordinates.longitude.toFixed(4) 
          } : null,
          
          address: geocodingResult.address || null,
          geocoding_note: geocodingResult.note || null, 
      };
      
      this.processingResults.unshift(processedData)
      this.appStore.addProcessingResult(processedData)
      
      ElMessage.success(`Фото обработано! Найдено ${processedData.buildings_detected} зданий`)
    },

    getStatusType(status) {
      const statusMap = {
        'completed': 'success',
        'processing': 'warning',
        'failed': 'danger',
        'pending': 'info'
      }
      return statusMap[status] || 'info'
    },

    getStatusText(status) {
      const statusMap = {
        'completed': 'Завершено',
        'processing': 'Обрабатывается',
        'failed': 'Ошибка',
        'pending': 'В ожидании'
      }
      return statusMap[status] || status
    }
  }
}
</script>

<style scoped>
.upload-photos {
  min-height: calc(100vh - 120px);
  padding: 40px 20px;
  background: rgba(255, 255, 255, 0.9);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 2.5em;
  color: #2c3e50;
  margin-bottom: 10px;
}

.page-header p {
  font-size: 1.2em;
  color: #7f8c8d;
}

.results-section {
  margin-top: 60px;
}

.results-section h2 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-size: 2em;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.result-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.result-header h4 {
  margin: 0;
  color: #2c3e50;
  flex: 1;
  margin-right: 15px;
  word-break: break-word;
}

.result-details p {
  margin: 8px 0;
  color: #555;
  font-size: 0.95em;
}

.no-buildings {
  text-align: center;
  padding: 20px;
  color: #999;
}

@media (max-width: 768px) {
  .results-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header h1 {
    font-size: 2em;
  }
}
</style>