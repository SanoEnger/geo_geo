<template>
  <div class="home">
    <!-- Герой секция -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">Определение координат объектов по фотографиям</h1>
        <p class="hero-subtitle">
          Автоматическая система для анализа фотографий и определения географических координат зданий с использованием искусственного интеллекта
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="$router.push('/upload')">
            <el-icon><UploadFilled /></el-icon>
            Начать анализ
          </el-button>
          <el-button size="large" @click="$router.push('/results')">
            <el-icon><DataAnalysis /></el-icon>
            Посмотреть результаты
          </el-button>
        </div>
      </div>
    </section>

    <!-- Особенности -->
    <section class="features-section">
      <div class="container">
        <h2 class="section-title">Как это работает</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">📷</div>
            <h3>Загрузите фотографии</h3>
            <p>Загружайте фотографии зданий и сооружений в формате JPG или PNG</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h3>Автоматический анализ</h3>
            <p>Система с помощью YOLO определяет здания на фотографиях и извлекает метаданные</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🗺️</div>
            <h3>Определение координат</h3>
            <p>Автоматическое определение географических координат и адресов объектов</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>Экспорт результатов</h3>
            <p>Скачайте результаты в формате Excel для дальнейшего анализа</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Статистика -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ stats.processedPhotos || 0 }}</div>
            <div class="stat-label">Обработано фото</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.detectedBuildings || 0 }}</div>
            <div class="stat-label">Обнаружено зданий</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.successRate || '100%' }}</div>
            <div class="stat-label">Успешных обработок</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { UploadFilled, DataAnalysis } from '@element-plus/icons-vue'
import { healthService } from '@/api/services'

export default {
  name: 'Home',
  components: {
    UploadFilled,
    DataAnalysis
  },
  data() {
    return {
      stats: {
        processedPhotos: 0,
        detectedBuildings: 0,
        successRate: '100%'
      }
    }
  },
  async mounted() {
    await this.checkServicesHealth()
  },
  methods: {
    async checkServicesHealth() {
      try {
        const health = await healthService.checkAllServices()
        console.log('Services health:', health)
      } catch (error) {
        console.error('Health check failed:', error)
      }
    }
  }
}
</script>

<style scoped>
.home {
  min-height: calc(100vh - 120px);
}

.hero-section {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.8) 100%);
  backdrop-filter: blur(10px);
  padding: 80px 20px;
  text-align: center;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 3em;
  color: #2c3e50;
  margin-bottom: 20px;
  font-weight: 700;
}

.hero-subtitle {
  font-size: 1.3em;
  color: #7f8c8d;
  margin-bottom: 40px;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.features-section {
  padding: 80px 20px;
  background: white;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  text-align: center;
  font-size: 2.5em;
  color: #2c3e50;
  margin-bottom: 60px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 40px;
}

.feature-card {
  text-align: center;
  padding: 40px 20px;
  border-radius: 12px;
  background: #f8f9fa;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 3em;
  margin-bottom: 20px;
}

.feature-card h3 {
  color: #2c3e50;
  margin-bottom: 15px;
  font-size: 1.4em;
}

.feature-card p {
  color: #7f8c8d;
  line-height: 1.6;
}

.stats-section {
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 40px;
  text-align: center;
}

.stat-item {
  padding: 30px 20px;
}

.stat-number {
  font-size: 3em;
  font-weight: 700;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 1.1em;
  opacity: 0.9;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2em;
  }
  
  .hero-subtitle {
    font-size: 1.1em;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .section-title {
    font-size: 2em;
  }
}
</style>