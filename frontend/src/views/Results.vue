<template>
  <div class="results">
    <div class="container">
      <div class="page-header">
        <h1>Результаты анализа</h1>
        <p>Просмотр результатов обработки фотографий</p>
      </div>

      <div v-if="processingResults.length === 0" class="no-results">
        <el-empty description="Нет результатов для отображения">
          <el-button type="primary" @click="$router.push('/upload')">
            Загрузить фото
          </el-button>
        </el-empty>
      </div>

      <div v-else class="results-content">
        <div class="results-stats">
          <el-statistic title="Всего обработано" :value="processingResults.length" />
          <el-statistic title="Успешных обработок" :value="successfulResults" />
          <el-statistic title="Обнаружено зданий" :value="totalBuildings" />
        </div>

        <div class="results-list">
          <div 
            v-for="result in processingResults" 
            :key="result.file_id"
            class="result-item"
          >
            <div class="result-header">
              <h3>{{ result.original_filename }}</h3>
              <el-tag :type="getStatusType(result.status)">
                {{ getStatusText(result.status) }}
              </el-tag>
            </div>
            
            <div class="result-body">
              <div v-if="result.buildings_detected > 0" class="building-info">
                <p><strong>🏢 Найдено зданий:</strong> {{ result.buildings_detected }}</p>
                <p v-if="result.coordinates">
                  <strong>📍 Координаты:</strong> 
                  {{ result.coordinates.lat.toFixed(6) }}, {{ result.coordinates.lng.toFixed(6) }}
                </p>
                <p v-if="result.address">
                  <strong>🏠 Адрес:</strong> {{ result.address }}
                </p>
              </div>
              
              <div v-else class="no-buildings">
                <p>❌ Здания не обнаружены</p>
              </div>
            </div>

            <div class="result-footer">
              <small>Обработано: {{ formatDate(result.processed_at) }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useAppStore } from '@/stores/app'

export default {
  name: 'Results',
  setup() {
    const appStore = useAppStore()
    return { appStore }
  },
  computed: {
    processingResults() {
      return this.appStore.processingResults
    },
    successfulResults() {
      return this.processingResults.filter(r => r.status === 'completed').length
    },
    totalBuildings() {
      return this.processingResults.reduce((total, result) => {
        return total + (result.buildings_detected || 0)
      }, 0)
    }
  },
  methods: {
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
    },

    formatDate(dateString) {
      if (!dateString) return 'Неизвестно'
      return new Date(dateString).toLocaleString('ru-RU')
    }
  }
}
</script>

<style scoped>
.results {
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

.no-results {
  text-align: center;
  padding: 60px 20px;
}

.results-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-item {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
  transition: transform 0.2s ease;
}

.result-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 16px;
}

.result-header h3 {
  margin: 0;
  color: #2c3e50;
  flex: 1;
  margin-right: 15px;
  word-break: break-word;
}

.result-body {
  margin-bottom: 16px;
}

.building-info p {
  margin: 8px 0;
  color: #555;
  line-height: 1.5;
}

.no-buildings {
  text-align: center;
  padding: 20px;
  color: #999;
  font-style: italic;
}

.result-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
  text-align: right;
}

.result-footer small {
  color: #888;
  font-size: 0.85em;
}

@media (max-width: 768px) {
  .results-stats {
    grid-template-columns: 1fr;
  }
  
  .result-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .page-header h1 {
    font-size: 2em;
  }
}
</style>