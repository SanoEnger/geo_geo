<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- Хедер -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <h1>📷 Geo Photo Analyzer</h1>
            <span class="subtitle">Определение координат объектов по фотографиям</span>
          </div>
          <nav class="navigation">
            <router-link to="/" class="nav-link">
              <el-icon><HomeFilled /></el-icon>
              Главная
            </router-link>
            <router-link to="/upload" class="nav-link">
              <el-icon><UploadFilled /></el-icon>
              Загрузка фото
            </router-link>
            <router-link to="/results" class="nav-link">
              <el-icon><DataAnalysis /></el-icon>
              Результаты
            </router-link>
          </nav>
        </div>
      </el-header>

      <!-- Основной контент -->
      <el-main class="app-main">
        <router-view />
      </el-main>

      <!-- Футер -->
      <el-footer class="app-footer">
        <div class="footer-content">
          <span>Geo Photo Analyzer &copy; 2024</span>
          <span>Система определения координат объектов</span>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
import { HomeFilled, UploadFilled, DataAnalysis } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    HomeFilled,
    UploadFilled,
    DataAnalysis
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.layout-container {
  min-height: 100vh;
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e0e0e0;
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.logo h1 {
  color: #2c3e50;
  margin: 0;
  font-size: 1.8em;
}

.subtitle {
  color: #7f8c8d;
  font-size: 0.9em;
  margin-left: 10px;
}

.navigation {
  display: flex;
  gap: 30px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: #2c3e50;
  font-weight: 500;
  padding: 10px 15px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.nav-link:hover {
  background: #f8f9fa;
  color: #667eea;
}

.nav-link.router-link-active {
  background: #667eea;
  color: white;
}

.app-main {
  padding: 0;
  background: transparent;
}

.app-footer {
  background: rgba(255, 255, 255, 0.9);
  border-top: 1px solid #e0e0e0;
  padding: 20px;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  color: #7f8c8d;
  font-size: 0.9em;
}
</style>