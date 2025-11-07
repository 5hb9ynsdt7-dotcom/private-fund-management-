<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="isEdit ? '编辑资产配置' : '新增资产配置'"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
      label-position="left"
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <h4 class="section-title">基本信息</h4>
        
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="formData.project_name" disabled />
        </el-form-item>
        
        <el-form-item label="月份" prop="month" required>
          <el-date-picker
            v-model="formData.month"
            type="month"
            placeholder="选择月份"
            value-format="YYYY-MM-DD"
            :default-value="defaultMonth"
            :disabled="isEdit"
            style="width: 100%"
          />
        </el-form-item>
      </div>

      <!-- 股票市场配置 -->
      <div class="form-section">
        <h4 class="section-title">股票市场配置</h4>
        
        <div class="ratio-grid">
          <el-form-item label="A股比例" prop="a_share_ratio">
            <el-input-number
              v-model="formData.a_share_ratio"
              :min="0"
              :max="100"
              :precision="2"
              controls-position="right"
              placeholder="0.00"
              class="ratio-input"
            />
            <span class="input-suffix">%</span>
          </el-form-item>
          
          <el-form-item label="H股比例" prop="h_share_ratio">
            <el-input-number
              v-model="formData.h_share_ratio"
              :min="0"
              :max="100"
              :precision="2"
              controls-position="right"
              placeholder="0.00"
              class="ratio-input"
            />
            <span class="input-suffix">%</span>
          </el-form-item>
          
          <el-form-item label="美股比例" prop="us_share_ratio">
            <el-input-number
              v-model="formData.us_share_ratio"
              :min="0"
              :max="100"
              :precision="2"
              controls-position="right"
              placeholder="0.00"
              class="ratio-input"
            />
            <span class="input-suffix">%</span>
          </el-form-item>
          
          <el-form-item label="其他市场比例" prop="other_market_ratio">
            <el-input-number
              v-model="formData.other_market_ratio"
              :min="0"
              :max="100"
              :precision="2"
              controls-position="right"
              placeholder="0.00"
              class="ratio-input"
            />
            <span class="input-suffix">%</span>
          </el-form-item>
        </div>

        <!-- 股票总仓位显示 -->
        <el-form-item label="股票总仓位">
          <el-tag type="success" size="large" class="total-ratio-tag">
            {{ (stockTotalRatio || 0).toFixed(2) }}%
          </el-tag>
          <span class="help-text">(自动计算)</span>
        </el-form-item>
      </div>

      <!-- 其他资产配置 -->
      <div class="form-section">
        <h4 class="section-title">其他资产配置</h4>
        
        <div class="ratio-grid">
          <el-form-item label="全球债券比例" prop="global_bond_ratio">
            <el-input-number
              v-model="formData.global_bond_ratio"
              :min="0"
              :max="100"
              :precision="2"
              controls-position="right"
              placeholder="0.00"
              class="ratio-input"
            />
            <span class="input-suffix">%</span>
          </el-form-item>
          
          <el-form-item label="可转债比例" prop="convertible_bond_ratio">
            <el-input-number
              v-model="formData.convertible_bond_ratio"
              :min="0"
              :max="100"
              :precision="2"
              controls-position="right"
              placeholder="0.00"
              class="ratio-input"
            />
            <span class="input-suffix">%</span>
          </el-form-item>
          
          <el-form-item label="其他比例" prop="other_ratio">
            <el-input-number
              v-model="formData.other_ratio"
              :min="0"
              :max="100"
              :precision="2"
              controls-position="right"
              placeholder="0.00"
              class="ratio-input"
            />
            <span class="input-suffix">%</span>
          </el-form-item>
        </div>

        <!-- 总比例验证提示 -->
        <div class="validation-hint">
          <el-alert
            v-if="totalRatio > 100"
            title="警告：所有比例总和超过100%"
            type="warning"
            :closable="false"
            show-icon
          />
          <el-alert
            v-else-if="totalRatio < 95"
            title="提示：比例总和较低，请检查数据完整性"
            type="info"
            :closable="false"
            show-icon
          />
          <div v-else class="total-info">
            <el-icon color="#67c23a"><SuccessFilled /></el-icon>
            <span>总比例: {{ (totalRatio || 0).toFixed(2) }}%</span>
          </div>
        </div>
      </div>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
        >
          {{ isEdit ? '更新' : '保存' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { SuccessFilled } from '@element-plus/icons-vue'
import projectHoldingAPI from '@/api/project-holding'

// Props
const props = defineProps({
  modelValue: Boolean,
  projectName: String,
  editData: Object
})

// Emits
const emit = defineEmits(['update:modelValue', 'success'])

// 表单引用
const formRef = ref()

// 响应式数据
const submitting = ref(false)

// 是否编辑模式（基于是否有真实的ID判断）
const isEdit = computed(() => !!(props.editData && props.editData.id))

// 默认月份（上个月）
const defaultMonth = computed(() => {
  const now = new Date()
  const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  return lastMonth.toISOString().split('T')[0]
})

// 表单数据
const formData = ref({
  project_name: '',
  month: '',
  a_share_ratio: null,
  h_share_ratio: null,
  us_share_ratio: null,
  other_market_ratio: null,
  global_bond_ratio: null,
  convertible_bond_ratio: null,
  other_ratio: null
})

// 表单验证规则
const formRules = {
  month: [
    { required: true, message: '请选择月份', trigger: 'change' }
  ]
}

// 数值安全转换函数
const safeNumber = (value) => {
  const num = Number(value)
  return isNaN(num) ? 0 : num
}

// 计算股票总仓位
const stockTotalRatio = computed(() => {
  const a = safeNumber(formData.value.a_share_ratio)
  const h = safeNumber(formData.value.h_share_ratio)
  const us = safeNumber(formData.value.us_share_ratio)
  const other = safeNumber(formData.value.other_market_ratio)
  return a + h + us + other
})

// 计算总比例
const totalRatio = computed(() => {
  const stock = safeNumber(stockTotalRatio.value)
  const bond = safeNumber(formData.value.global_bond_ratio)
  const convertible = safeNumber(formData.value.convertible_bond_ratio)
  const other = safeNumber(formData.value.other_ratio)
  const total = stock + bond + convertible + other
  return isNaN(total) ? 0 : total
})

// 重置表单
const resetForm = () => {
  formData.value = {
    project_name: props.projectName,
    month: defaultMonth.value,
    a_share_ratio: null,
    h_share_ratio: null,
    us_share_ratio: null,
    other_market_ratio: null,
    global_bond_ratio: null,
    convertible_bond_ratio: null,
    other_ratio: null
  }
}

// 监听编辑数据变化
watch(() => props.editData, (newData) => {
  if (newData) {
    formData.value = {
      ...newData,
      month: newData.month ? new Date(newData.month).toISOString().split('T')[0] : ''
    }
  }
}, { immediate: true, deep: true })

// 监听对话框显示状态
watch(() => props.modelValue, (show) => {
  console.log('AssetConfigDialog modelValue 变化:', show)
  console.log('props.editData:', props.editData)
  if (show && !props.editData) {
    resetForm()
  }
})

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
  if (formRef.value) {
    formRef.value.resetFields()
  }
  nextTick(() => {
    // 总是重置表单，确保状态清理
    resetForm()
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    // 格式化提交数据，确保数据格式正确
    const submitData = {
      project_name: props.projectName,
      month: formData.value.month,
      a_share_ratio: formData.value.a_share_ratio,
      h_share_ratio: formData.value.h_share_ratio,
      us_share_ratio: formData.value.us_share_ratio,
      other_market_ratio: formData.value.other_market_ratio,
      global_bond_ratio: formData.value.global_bond_ratio,
      convertible_bond_ratio: formData.value.convertible_bond_ratio,
      other_ratio: formData.value.other_ratio
    }
    
    if (isEdit.value) {
      // 更新记录
      await projectHoldingAPI.updateAssetRecord(props.editData.id, submitData)
      ElMessage.success('资产配置更新成功')
    } else {
      // 新增记录
      await projectHoldingAPI.createAssetRecord(props.projectName, submitData)
      ElMessage.success('资产配置创建成功')
    }
    
    emit('success')
    emit('update:modelValue', false) // 直接关闭对话框
    
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-section {
  margin-bottom: 32px;
}

.section-title {
  margin: 0 0 16px 0;
  padding: 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  border-bottom: 2px solid #e4e7ed;
}

.ratio-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.ratio-input {
  width: calc(100% - 20px);
}

.input-suffix {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.total-ratio-tag {
  font-size: 16px;
  font-weight: 600;
  padding: 8px 16px;
  margin-right: 12px;
}

.help-text {
  color: #909399;
  font-size: 12px;
}

.validation-hint {
  margin-top: 16px;
}

.total-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  color: #67c23a;
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
}

:deep(.el-alert) {
  margin-bottom: 0;
}
</style>