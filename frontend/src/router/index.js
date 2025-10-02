import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import UploadPhotos from '../views/UploadPhotos.vue'
import Results from '../views/Results.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: 'Главная - Geo Photo Analyzer' }
  },
  {
    path: '/upload',
    name: 'UploadPhotos',
    component: UploadPhotos,
    meta: { title: 'Загрузка фото - Geo Photo Analyzer' }
  },
  {
    path: '/results',
    name: 'Results',
    component: Results,
    meta: { title: 'Результаты - Geo Photo Analyzer' }
  } 
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Динамическое изменение title страницы
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Geo Photo Analyzer'
  next()
})

export default router