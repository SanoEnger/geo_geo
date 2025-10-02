import axios from 'axios'

// Базовый клиент API
const apiClient = axios.create({
  baseURL: '/api',  // ← ИСПРАВИТЬ НА ПОЛНЫЙ URL
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Интерцептор для обработки ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    
    if (error.response) {
      // Сервер ответил с ошибкой
      const message = error.response.data?.detail || error.response.data?.message || 'Ошибка сервера'
      throw new Error(message)
    } else if (error.request) {
      // Запрос был сделан, но ответ не получен
      throw new Error('Сервер недоступен. Проверьте подключение к интернету.')
    } else {
      // Что-то пошло не так при настройке запроса
      throw new Error('Ошибка при выполнении запроса.')
    }
  }
)

export default apiClient