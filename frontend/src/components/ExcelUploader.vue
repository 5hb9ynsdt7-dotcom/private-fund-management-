<template>
  <div class="excel-uploader">
    <el-upload
      ref="uploadRef"
      class="upload-demo"
      drag
      action="#"
      :multiple="multiple"
      :auto-upload="false"
      :show-file-list="true"
      :accept="accept"
      :before-upload="beforeUpload"
      :on-change="handleFileChange"
      :on-remove="handleFileRemove"
      :file-list="fileList"
    >
      <div class="upload-content">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p class="upload-title">点击或拖拽文件到此处上传</p>
          <p class="upload-subtitle">
            支持{{ acceptText }}格式文件
            <span v-if="multiple">，可同时上传多个文件</span>
          </p>
        </div>
      </div>
      
      <template #tip>
        <div class="upload-tip">
          <el-text size="small" type="info">
            文件大小不超过{{ maxSizeText }}
            <el-link 
              v-if="templateUrl" 
              type="primary" 
              :href="templateUrl" 
              target="_blank"
            >
              下载模板
            </el-link>
          </el-text>
        </div>
      </template>
    </el-upload>
    
    <!-- 上传结果展示 -->
    <div v-if="uploadResult" class="upload-result">
      <el-alert
        :title="uploadResult.title"
        :type="uploadResult.type"
        :description="uploadResult.description"
        show-icon
        :closable="false"
      />
      
      <!-- 详细结果 -->
      <div v-if="uploadResult.details" class="result-details">
        <el-collapse v-model="activeResultTab">
          <el-collapse-item title="查看详细结果" name="details">
            <div class="result-stats">
              <el-row :gutter="16">
                <el-col :span="6">
                  <el-statistic title="成功" :value="uploadResult.details.success_count" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="失败" :value="uploadResult.details.failed_count" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="新增" :value="uploadResult.details.created_count" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="更新" :value="uploadResult.details.updated_count" />
                </el-col>
              </el-row>
            </div>
            
            <!-- 错误列表 -->
            <div v-if="uploadResult.details.errors?.length" class="error-list">
              <h4>错误详情：</h4>
              <ul>
                <li v-for="(error, index) in uploadResult.details.errors" :key="index">
                  {{ error }}
                </li>
              </ul>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="upload-actions">
      <el-space>
        <el-button 
          type="primary" 
          :loading="uploading"
          :disabled="!fileList.length"
          @click="handleUpload"
        >
          <el-icon><Upload /></el-icon>
          {{ uploading ? '上传中...' : '开始上传' }}
        </el-button>
        
        <el-button 
          :disabled="!fileList.length"
          @click="clearFiles"
        >
          清空文件
        </el-button>
        
        <el-button 
          v-if="showPreview && selectedFile"
          @click="previewFile"
        >
          <el-icon><View /></el-icon>
          预览数据
        </el-button>
      </el-space>
    </div>
    
    <!-- 文件预览对话框 -->
    <el-dialog
      v-model="previewVisible"
      title="文件预览"
      width="80%"
      top="5vh"
    >
      <div v-if="previewData" class="file-preview">
        <el-alert
          title="仅显示前5行数据"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        />
        
        <el-table
          :data="previewData.slice(0, 5)"
          border
          stripe
          max-height="400"
        >
          <el-table-column
            v-for="(column, index) in previewColumns"
            :key="index"
            :prop="column"
            :label="column"
            min-width="120"
          />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { formatFileSize, validateFileType } from '@/utils'

const props = defineProps({
  // 是否支持多文件上传
  multiple: {
    type: Boolean,
    default: true
  },
  // 接受的文件类型
  accept: {
    type: String,
    default: '.xlsx,.xls'
  },
  // 最大文件大小（MB）
  maxSize: {
    type: Number,
    default: 10
  },
  // 上传API函数
  uploadApi: {
    type: Function,
    required: true
  },
  // 模板下载链接
  templateUrl: {
    type: String,
    default: ''
  },
  // 是否显示预览功能
  showPreview: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['success', 'error', 'progress'])

const uploadRef = ref()
const fileList = ref([])
const uploading = ref(false)
const uploadResult = ref(null)
const activeResultTab = ref('')

// 预览相关
const previewVisible = ref(false)
const previewData = ref([])
const previewColumns = ref([])
const selectedFile = ref(null)

// 计算属性
const acceptText = computed(() => {
  return props.accept.replace(/\./g, '').toUpperCase()
})

const maxSizeText = computed(() => {
  return `${props.maxSize}MB`
})

// 文件上传前检查
const beforeUpload = (file) => {
  // 检查文件类型
  const allowedTypes = props.accept.split(',').map(type => type.trim().replace('.', ''))
  if (!validateFileType(file, allowedTypes)) {
    ElMessage.error(`文件格式不正确，请上传${acceptText.value}格式文件`)
    return false
  }
  
  // 检查文件大小
  const maxSizeBytes = props.maxSize * 1024 * 1024
  if (file.size > maxSizeBytes) {
    ElMessage.error(`文件大小不能超过${maxSizeText.value}`)
    return false
  }
  
  return false // 阻止自动上传
}

// 文件列表变化
const handleFileChange = (file, files) => {
  fileList.value = files
  selectedFile.value = file
  uploadResult.value = null
}

// 移除文件
const handleFileRemove = (file, files) => {
  fileList.value = files
  if (selectedFile.value === file) {
    selectedFile.value = files[0] || null
  }
  uploadResult.value = null
}

// 清空文件
const clearFiles = () => {
  uploadRef.value.clearFiles()
  fileList.value = []
  selectedFile.value = null
  uploadResult.value = null
}

// 开始上传
const handleUpload = async () => {
  if (!fileList.value.length) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  uploading.value = true
  uploadResult.value = null
  
  try {
    // 提取原始文件对象
    const files = fileList.value.map(item => item.raw)
    
    emit('progress', { uploading: true })
    
    // 调用上传API
    const result = await props.uploadApi(files)
    
    // 处理结果
    const successCount = result.data?.success_count || result.success_count || 0
    const failedCount = result.data?.failed_count || result.failed_count || 0
    const totalCount = successCount + failedCount
    
    if (successCount === totalCount) {
      // 全部成功
      uploadResult.value = {
        type: 'success',
        title: '上传成功',
        description: `成功处理 ${successCount} 条记录`,
        details: result.data || result
      }
      ElMessage.success('文件上传成功')
      emit('success', result)
    } else if (successCount > 0) {
      // 部分成功
      uploadResult.value = {
        type: 'warning',
        title: '部分成功',
        description: `成功 ${successCount} 条，失败 ${failedCount} 条`,
        details: result.data || result
      }
      ElMessage.warning('文件上传部分成功，请查看详细结果')
      emit('success', result)
    } else {
      // 全部失败
      uploadResult.value = {
        type: 'error',
        title: '上传失败',
        description: `所有记录处理失败`,
        details: result.data || result
      }
      ElMessage.error('文件上传失败')
      emit('error', result)
    }
    
    // 自动展开结果详情
    if (uploadResult.value.details) {
      activeResultTab.value = 'details'
    }
    
  } catch (error) {
    console.error('上传失败:', error)
    uploadResult.value = {
      type: 'error',
      title: '上传失败',
      description: error.message || '网络错误，请重试'
    }
    ElMessage.error('文件上传失败')
    emit('error', error)
  } finally {
    uploading.value = false
    emit('progress', { uploading: false })
  }
}

// 预览文件
const previewFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  try {
    // 这里应该调用后端接口预览文件
    // 简化处理，只是显示预览对话框
    previewVisible.value = true
    
    // 模拟预览数据
    previewData.value = [
      { fund_code: 'L03126', nav_date: '2025-07-01', unit_nav: 1.2580, accum_nav: 1.2580 },
      { fund_code: 'L03127', nav_date: '2025-07-01', unit_nav: 1.1820, accum_nav: 1.3420 }
    ]
    previewColumns.value = ['fund_code', 'nav_date', 'unit_nav', 'accum_nav']
    
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('文件预览失败')
  }
}

// 暴露方法给父组件
defineExpose({
  clearFiles,
  handleUpload
})
</script>

<style scoped>
.excel-uploader {
  width: 100%;
}

.upload-demo {
  width: 100%;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}

.upload-icon {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
}

.upload-title {
  font-size: 16px;
  color: #606266;
  margin: 0 0 8px 0;
}

.upload-subtitle {
  font-size: 12px;
  color: #909399;
  margin: 0;
}

.upload-tip {
  text-align: center;
  margin-top: 8px;
}

.upload-actions {
  margin-top: 16px;
  text-align: center;
}

.upload-result {
  margin-top: 16px;
}

.result-details {
  margin-top: 16px;
}

.result-stats {
  margin-bottom: 16px;
}

.error-list h4 {
  color: #F56C6C;
  margin-bottom: 8px;
}

.error-list ul {
  margin: 0;
  padding-left: 20px;
}

.error-list li {
  color: #F56C6C;
  margin-bottom: 4px;
  line-height: 1.4;
}

.file-preview {
  max-height: 600px;
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-content {
    padding: 20px 10px;
  }
  
  .upload-icon {
    font-size: 36px;
  }
  
  .upload-title {
    font-size: 14px;
  }
  
  .upload-subtitle {
    font-size: 11px;
  }
}
</style>