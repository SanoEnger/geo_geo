import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    // Состояние загрузки
    loading: false,
    
    // Уведомления
    notifications: [],
    
    // Данные пользователя
    user: null,
    
    // Текущий выбранный датасет
    currentDataset: null,
    
    // Результаты обработки
    processingResults: [],
    
    // Настройки
    settings: {
      autoProcess: true,
      confidenceThreshold: 0.5,
      maxFileSize: 50 * 1024 * 1024 // 50MB
    }
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
    hasResults: (state) => state.processingResults.length > 0,
    totalProcessed: (state) => state.processingResults.length
  },

  actions: {
    setLoading(loading) {
      this.loading = loading
    },

    addNotification(notification) {
      this.notifications.push({
        id: Date.now(),
        type: 'info',
        ...notification
      })
    },

    removeNotification(id) {
      this.notifications = this.notifications.filter(n => n.id !== id)
    },

    setUser(user) {
      this.user = user
    },

    setCurrentDataset(dataset) {
      this.currentDataset = dataset
    },

    addProcessingResult(result) {
      this.processingResults.unshift(result)
    },

    clearResults() {
      this.processingResults = []
    },

    updateSettings(newSettings) {
      this.settings = { ...this.settings, ...newSettings }
    }
  }
})