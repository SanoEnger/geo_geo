<template>
  <div class="file-upload">
    <el-upload
      class="upload-demo"
      drag
      multiple
      :auto-upload="false"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :file-list="fileList"
      accept=".jpg,.jpeg,.png,.JPG,.JPEG,.PNG"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        Перетащите файлы сюда или <em>нажмите для выбора</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          Поддерживаются файлы jpg/png размером до 50MB
        </div>
      </template>
    </el-upload>

    <div v-if="fileList.length > 0" class="upload-actions">
      <el-button 
        type="primary" 
        :loading="uploading" 
        @click="handleUpload"
        :disabled="fileList.length === 0"
      >
        {{ uploading ? 'Загрузка...' : `Загрузить ${fileList.length} файлов` }}
      </el-button>
      <el-button @click="clearFiles">Очистить</el-button>
    </div>

    <div v-if="uploadProgress > 0" class="upload-progress">
      <el-progress 
        :percentage="uploadProgress" 
        :status="uploadStatus"
        :format="formatProgress"
      />
      <p class="progress-text">
        Обработано: {{ uploadedCount }} из {{ fileList.length }}
      </p>
    </div>
  </div>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import axios from 'axios'

export default {
  name: 'FileUpload',
  components: {
    UploadFilled
  },
  emits: ['upload-complete', 'photo-processed'],
  data() {
    return {
      fileList: [],
      uploading: false,
      uploadProgress: 0,
      uploadedCount: 0,
      uploadStatus: '', 
      client: axios.create({
        baseURL: import.meta.env.VITE_API_BASE_URL || '/api/photo_upload',
        timeout: 60000 
      })
    }
  },
  setup() {
    const appStore = useAppStore()
    return { appStore }
  },
  methods: {
    handleFileChange(file, fileList) {
      this.fileList = fileList.filter(f => f.raw.size <= 50 * 1024 * 1024)
      if (file.raw.size > 50 * 1024 * 1024) {
        ElMessage.error(`Файл ${file.name} превышает максимальный размер 50MB.`)
      }
    },

    handleFileRemove(file, fileList) {
      this.fileList = fileList
    },

    clearFiles() {
      this.fileList = []
      this.uploadProgress = 0
      this.uploadedCount = 0
      this.uploadStatus = ''
    },
    
    async handleUpload() {
      if (this.fileList.length === 0) {
        ElMessage.warning('Пожалуйста, выберите файлы для загрузки')
        return
      }

      this.uploading = true
      this.uploadProgress = 0
      this.uploadedCount = 0
      this.uploadStatus = 'uploading'
      
      const results = []

      try {
        const formData = new FormData()
        this.fileList.forEach(file => {
          formData.append('files', file.raw, file.name)
        })

        const response = await this.client.post('/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
        })
        
        let apiBatchResults = response.data.results; 

        // АВАРИЙНЫЙ МЕХАНИЗМ: Если ответ не является массивом, но содержит file_id
        if (!Array.isArray(apiBatchResults)) {
             if (response.data.file_id) {
                 // Оборачиваем одиночный результат в формат, который ожидает цикл:
                 apiBatchResults = [{ status: 'success', data: response.data, filename: response.data.filename }];
             } else {
                 apiBatchResults = []; 
                 ElMessage.error("Некорректный формат ответа от API Gateway.");
             }
        }
        
        // Перебираем результаты
        for (let i = 0; i < apiBatchResults.length; i++) {
          const result = apiBatchResults[i]
          
          if (result.status === 'success') {
            // result.data - это полный payload {"file_id":"...", "geocoding_result":{...}}
            this.$emit('photo-processed', result.data) 
          } else {
            ElMessage.error(`Ошибка при обработке ${result.filename || 'файла'}: ${result.error}`)
          }
          
          results.push(result)
          
          this.uploadedCount = i + 1
          this.uploadProgress = Math.round((this.uploadedCount / this.fileList.length) * 100)
        }

        // Итоги загрузки
        const successCount = results.filter(r => r.status === 'success').length
        if (successCount === this.fileList.length) {
          this.uploadStatus = 'success'
        } else {
          this.uploadStatus = 'exception'
        }

        this.$emit('upload-complete', results)

      } catch (error) {
        console.error("Upload error:", error)
        const errorMessage = error.response?.data?.detail || error.message || 'Неизвестная ошибка'
        ElMessage.error(`Ошибка загрузки: ${errorMessage}`)
        this.uploadStatus = 'exception'
      } finally {
        this.uploading = false
      }
    },
    
    formatProgress(percentage) {
      return `Загрузка: ${percentage}%`
    }
  }
}
</script>

<style scoped>
.file-upload {
  max-width: 800px;
  margin: 0 auto;
}

.upload-actions {
  margin-top: 20px;
  text-align: center;
}

.upload-progress {
  margin-top: 20px;
  padding: 20px;
  background: #f8f8f8;
  border-radius: 8px;
}

.progress-text {
  margin-top: 10px;
  text-align: center;
  color: #606266;
}
</style>