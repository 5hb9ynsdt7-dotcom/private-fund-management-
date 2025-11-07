<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="isEdit ? '编辑行业配置' : '新增行业配置'"
    width="700px"
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

      <!-- 比例计算方式 -->
      <div class="form-section">
        <h4 class="section-title">比例计算方式</h4>
        
        <el-form-item label="计算方式" prop="ratio_type" required>
          <el-radio-group v-model="formData.ratio_type" class="ratio-type-group">
            <el-radio value="based_on_stock" class="ratio-radio">
              <div class="radio-content">
                <div class="radio-title">基于股票仓位</div>
                <div class="radio-desc">行业比例基于股票总仓位计算，后续会自动转换为占总仓位的实际比例</div>
              </div>
            </el-radio>
            <el-radio value="based_on_total" class="ratio-radio">
              <div class="radio-content">
                <div class="radio-title">基于总仓位</div>
                <div class="radio-desc">行业比例直接表示占总仓位的比例，无需额外计算</div>
              </div>
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 计算方式说明 -->
        <el-alert
          v-if="formData.ratio_type === 'based_on_stock'"
          title="基于股票仓位计算"
          type="warning"
          :closable="false"
          class="calc-hint"
        >
          <template #default>
            <p>选择此方式时，输入的行业比例将基于股票总仓位进行计算。</p>
            <p><strong>计算公式：</strong>行业实际占比 = 行业比例 × 股票总仓位比例</p>
            <p>例如：医疗行业30%，股票总仓位70% → 医疗行业实际占总仓位：21%</p>
          </template>
        </el-alert>
        
        <el-alert
          v-else-if="formData.ratio_type === 'based_on_total'"
          title="基于总仓位计算"
          type="info"
          :closable="false"
          class="calc-hint"
        >
          <template #default>
            <p>选择此方式时，输入的行业比例直接表示该行业占总仓位的比例。</p>
            <p>例如：医疗行业30% → 医疗行业占总仓位：30%</p>
          </template>
        </el-alert>
      </div>

      <!-- 行业持仓配置 -->
      <div class="form-section">
        <h4 class="section-title">行业持仓配置</h4>
        
        <div class="industry-grid">
          <template v-for="i in 5" :key="i">
            <div class="industry-row">
              <el-form-item 
                :label="`第${getChineseNumber(i)}持仓行业`"
                :prop="`industry${i}`"
                class="industry-name-item"
              >
                <el-input
                  v-model="formData[`industry${i}`]"
                  placeholder="请输入行业名称"
                  clearable
                />
              </el-form-item>
              
              <el-form-item 
                :label="`比例`"
                :prop="`industry${i}_ratio`"
                class="industry-ratio-item"
                :rules="getIndustryRatioRules(i)"
              >
                <el-input-number
                  v-model="formData[`industry${i}_ratio`]"
                  :precision="2"
                  controls-position="right"
                  placeholder="0.00"
                  :disabled="!formData[`industry${i}`]"
                  class="ratio-input"
                />
                <span class="input-suffix">%</span>
              </el-form-item>
            </div>
          </template>
        </div>

        <!-- 总比例统计 -->
        <div class="ratio-summary">
          <el-card shadow="never" class="summary-card">
            <div class="summary-content">
              <div class="summary-item">
                <span class="summary-label">行业比例总和：</span>
                <el-tag :type="getRatioSummaryType()" size="large" class="summary-value">
                  {{ (totalIndustryRatio || 0).toFixed(2) }}%
                </el-tag>
              </div>
              
              <div v-if="formData.ratio_type === 'based_on_stock'" class="summary-note">
                <el-icon><InfoFilled /></el-icon>
                <span>基于股票仓位模式：支持空头仓位，允许负值和超过100%</span>
              </div>
              
              <div v-else class="summary-note">
                <el-icon><InfoFilled /></el-icon>
                <span>基于总仓位模式：比例总和代表行业配置覆盖的总仓位</span>
              </div>
            </div>
          </el-card>
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
import { InfoFilled } from '@element-plus/icons-vue'
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
  ratio_type: 'based_on_stock',
  industry1: '',
  industry1_ratio: null,
  industry2: '',
  industry2_ratio: null,
  industry3: '',
  industry3_ratio: null,
  industry4: '',
  industry4_ratio: null,
  industry5: '',
  industry5_ratio: null
})

// 表单验证规则
const formRules = {
  month: [
    { required: true, message: '请选择月份', trigger: 'change' }
  ],
  ratio_type: [
    { required: true, message: '请选择比例计算方式', trigger: 'change' }
  ]
}

// 数值安全转换函数
const safeNumber = (value) => {
  const num = Number(value)
  return isNaN(num) ? 0 : num
}

// 计算行业比例总和
const totalIndustryRatio = computed(() => {
  let total = 0
  for (let i = 1; i <= 5; i++) {
    const ratio = safeNumber(formData.value[`industry${i}_ratio`])
    total += ratio
  }
  return isNaN(total) ? 0 : total
})

// 获取中文数字
const getChineseNumber = (num) => {
  const numbers = ['', '一', '二', '三', '四', '五']
  return numbers[num]
}

// 获取行业比例验证规则
const getIndustryRatioRules = (index) => {
  return [
    {
      validator: (rule, value, callback) => {
        const industryName = formData.value[`industry${index}`]
        
        // 如果有行业名称但没有比例
        if (industryName && (value === null || value === undefined)) {
          callback(new Error('请设置行业比例'))
          return
        }
        
        // 如果有比例但没有行业名称
        if (!industryName && (value !== null && value !== undefined)) {
          callback(new Error('请先填写行业名称'))
          return
        }
        
        callback()
      },
      trigger: 'blur'
    }
  ]
}

// 获取比例总和状态类型
const getRatioSummaryType = () => {
  const total = totalIndustryRatio.value
  if (formData.value.ratio_type === 'based_on_stock') {
    if (total > 100) return 'danger'
    if (total > 90) return 'warning'
    return 'success'
  } else {
    if (total > 100) return 'warning'
    return 'info'
  }
}

// 重置表单
const resetForm = () => {
  formData.value = {
    project_name: props.projectName,
    month: defaultMonth.value,
    ratio_type: 'based_on_stock',
    industry1: '',
    industry1_ratio: null,
    industry2: '',
    industry2_ratio: null,
    industry3: '',
    industry3_ratio: null,
    industry4: '',
    industry4_ratio: null,
    industry5: '',
    industry5_ratio: null
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
  console.log('IndustryConfigDialog modelValue 变化:', show)
  console.log('props.editData:', props.editData)
  if (show && !props.editData) {
    resetForm()
  }
})

// 监听行业名称变化，自动清空对应比例
watch(() => formData.value, (newData) => {
  for (let i = 1; i <= 5; i++) {
    const industryName = newData[`industry${i}`]
    const industryRatio = newData[`industry${i}_ratio`]
    
    // 如果行业名称被清空，同时清空比例
    if (!industryName && (industryRatio !== null && industryRatio !== undefined)) {
      formData.value[`industry${i}_ratio`] = null
    }
  }
}, { deep: true })

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
    
    // 验证至少有一个行业配置
    let hasIndustry = false
    for (let i = 1; i <= 5; i++) {
      if (formData.value[`industry${i}`] && (formData.value[`industry${i}_ratio`] !== null && formData.value[`industry${i}_ratio`] !== undefined)) {
        hasIndustry = true
        break
      }
    }
    
    if (!hasIndustry) {
      ElMessage.warning('请至少配置一个行业')
      return
    }
    
    // 注意：已移除100%上限限制，支持空头仓位和负值
    // 基于股票仓位模式支持总和超过100%，以适应空头仓位等复杂策略
    
    submitting.value = true
    
    // 格式化提交数据
    const submitData = {
      project_name: props.projectName,
      month: formData.value.month,
      ratio_type: formData.value.ratio_type,
      industry1: formData.value.industry1,
      industry1_ratio: formData.value.industry1_ratio,
      industry2: formData.value.industry2,
      industry2_ratio: formData.value.industry2_ratio,
      industry3: formData.value.industry3,
      industry3_ratio: formData.value.industry3_ratio,
      industry4: formData.value.industry4,
      industry4_ratio: formData.value.industry4_ratio,
      industry5: formData.value.industry5,
      industry5_ratio: formData.value.industry5_ratio
    }
    
    if (isEdit.value) {
      // 更新记录
      await projectHoldingAPI.updateIndustryRecord(props.editData.id, submitData)
      ElMessage.success('行业配置更新成功')
    } else {
      // 新增记录
      await projectHoldingAPI.createIndustryRecord(props.projectName, submitData)
      ElMessage.success('行业配置创建成功')
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

.ratio-type-group {
  width: 100%;
}

.ratio-radio {
  display: block;
  width: 100%;
  margin: 0 0 16px 0;
  padding: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  transition: all 0.3s;
}

.ratio-radio:hover {
  border-color: #409eff;
  background-color: #f5f9ff;
}

.ratio-radio.is-checked {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.radio-content {
  margin-left: 20px;
}

.radio-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
  margin-bottom: 4px;
}

.radio-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
}

.calc-hint {
  margin-bottom: 16px;
}

.industry-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.industry-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  align-items: end;
}

.industry-name-item {
  margin-bottom: 0;
}

.industry-ratio-item {
  margin-bottom: 0;
  position: relative;
}

.ratio-input {
  width: calc(100% - 20px);
}

.input-suffix {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

.ratio-summary {
  margin-top: 24px;
}

.summary-card {
  background-color: #fafbfc;
  border: 1px solid #e4e7ed;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-label {
  font-weight: 500;
  color: #606266;
}

.summary-value {
  font-size: 16px;
  font-weight: 600;
  padding: 8px 16px;
}

.summary-note {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #909399;
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

:deep(.el-radio__label) {
  width: 100%;
  padding-left: 0;
}

:deep(.el-alert__content) {
  line-height: 1.5;
}

:deep(.el-alert p) {
  margin: 4px 0;
}
</style>