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

    <!-- Прогресс загрузки -->
    <div v-if="uploadProgress > 0" class="upload-progress">
      <el-progress 
        :percentage="uploadProgress" 
        :status="uploadStatus"
        :text-inside="true"
        :stroke-width="20"
      />
      <div class="progress-info">
        Загружено: {{ uploadedCount }} из {{ fileList.length }}
      </div>
    </div>
  </div>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { photoService } from '@/api/services'

export default {
  name: 'FileUpload',
  components: {
    UploadFilled
  },
  data() {
    return {
      fileList: [],
      uploading: false,
      uploadProgress: 0,
      uploadedCount: 0,
      uploadStatus: null
    }
  },
  methods: {
    handleFileChange(file, fileList) {
      this.fileList = fileList
    },

    handleFileRemove(file, fileList) {
      this.fileList = fileList
    },

    clearFiles() {
      this.fileList = []
      this.uploadProgress = 0
      this.uploadedCount = 0
    },

    async handleUpload() {
      if (this.fileList.length === 0) {
        ElMessage.warning('Выберите файлы для загрузки')
        return
      }

      this.uploading = true
      this.uploadProgress = 0
      this.uploadedCount = 0
      this.uploadStatus = null

      try {
        const results = []

        for (let i = 0; i < this.fileList.length; i++) {
          const file = this.fileList[i].raw
          
          try {
            // Используем исправленный сервис
            const result = await photoService.uploadPhoto(file)
            
            if (result.success) {
              results.push({
                file: file.name,
                status: 'success',
                data: result.data
              })
              
              // Сразу эмитим событие обработки - БЕЗ ДОПОЛНИТЕЛЬНОГО processPhoto!
              this.$emit('photo-processed', result.data)
              ElMessage.success(`${file.name}: Найдено ${result.data.buildings_detected} зданий`)
            } else {
              results.push({
                file: file.name,
                status: 'error',
                error: result.error
              })
              
              // Эмитим результат с ошибкой
              this.$emit('photo-processed', {
                file_id: result.data?.file_id || file.name,
                original_filename: file.name,
                status: 'failed',
                buildings_detected: 0,
                error: result.error
              })
              ElMessage.error(`${file.name}: ${result.error}`)
            }

          } catch (error) {
            console.error(`Upload error for ${file.name}:`, error)
            const errorResult = {
              file: file.name,
              status: 'error',
              error: error.message
            }
            results.push(errorResult)
            
            // Эмитим результат с ошибкой
            this.$emit('photo-processed', {
              file_id: file.name,
              original_filename: file.name,
              status: 'failed', 
              buildings_detected: 0,
              error: error.message
            })
            ElMessage.error(`${file.name}: ${error.message}`)
          }

          this.uploadedCount = i + 1
          this.uploadProgress = Math.round((this.uploadedCount / this.fileList.length) * 100)
        }

        // Итоги загрузки
        const successCount = results.filter(r => r.status === 'success').length
        if (successCount === this.fileList.length) {
          ElMessage.success(`Все файлы успешно загружены и обработаны`)
          this.uploadStatus = 'success'
        } else {
          ElMessage.warning(`Загружено ${successCount} из ${this.fileList.length} файлов`)
          this.uploadStatus = 'exception'
        }

        this.$emit('upload-complete', results)

      } catch (error) {
        ElMessage.error(`Ошибка загрузки: ${error.message}`)
        this.uploadStatus = 'exception'
      } finally {
        this.uploading = false
      }
    }
  }
  // УДАЛЕН метод processPhoto - он больше не нужен
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
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-info {
  text-align: center;
  margin-top: 10px;
  color: #666;
  font-size: 0.9em;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  border: 2px dashed #409eff;
  background: rgba(64, 158, 255, 0.05);
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}
</style>