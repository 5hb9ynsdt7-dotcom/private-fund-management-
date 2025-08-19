<template>
  <el-dialog
    v-model="dialogVisible"
    title="批量编辑策略"
    width="500px"
    :before-close="handleClose"
    destroy-on-close
  >
    <div class="selected-strategies">
      <el-alert
        :title="`已选择 ${selectedStrategies.length} 个策略配置`"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <el-scrollbar max-height="120px">
            <div class="strategy-list">
              <el-tag
                v-for="strategy in selectedStrategies"
                :key="strategy.fund_code"
                size="small"
                style="margin: 2px 4px 2px 0;"
              >
                {{ strategy.fund_code }} - {{ strategy.fund_name }}
              </el-tag>
            </div>
          </el-scrollbar>
        </template>
      </el-alert>
    </div>
    
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      size="default"
      style="margin-top: 20px;"
    >
      <el-form-item>
        <el-text type="info" size="small">
          只有勾选的字段会被批量更新，未勾选的字段将保持原值不变
        </el-text>
      </el-form-item>
      
      <el-form-item>
        <el-checkbox v-model="updateFields.major_strategy" style="margin-bottom: 8px;">
          更新大类策略
        </el-checkbox>
        <el-select
          v-model="formData.major_strategy"
          placeholder="选择大类策略"
          style="width: 100%"
          :disabled="!updateFields.major_strategy"
          @change="handleMajorStrategyChange"
        >
          <el-option
            v-for="strategy in majorStrategies"
            :key="strategy.value"
            :label="strategy.label"
            :value="strategy.value"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item>
        <el-checkbox v-model="updateFields.sub_strategy" style="margin-bottom: 8px;">
          更新细分策略
        </el-checkbox>
        <el-select
          v-model="formData.sub_strategy"
          placeholder="选择细分策略"
          style="width: 100%"
          :disabled="!updateFields.sub_strategy || !formData.major_strategy"
          clearable
        >
          <el-option
            v-for="strategy in availableSubStrategies"
            :key="strategy.value"
            :label="strategy.label"
            :value="strategy.value"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item>
        <el-checkbox v-model="updateFields.is_qd" style="margin-bottom: 8px;">
          更新QD状态
        </el-checkbox>
        <el-radio-group 
          v-model="formData.is_qd" 
          :disabled="!updateFields.is_qd"
        >
          <el-radio :value="true">是QD</el-radio>
          <el-radio :value="false">非QD</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item>
        <el-checkbox v-model="updateFields.risk_level" style="margin-bottom: 8px;">
          更新风险等级
        </el-checkbox>
        <el-radio-group 
          v-model="formData.risk_level" 
          :disabled="!updateFields.risk_level"
        >
          <el-radio value="low">低风险</el-radio>
          <el-radio value="medium">中风险</el-radio>
          <el-radio value="high">高风险</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item>
        <el-checkbox v-model="updateFields.status" style="margin-bottom: 8px;">
          更新状态
        </el-checkbox>
        <el-radio-group 
          v-model="formData.status" 
          :disabled="!updateFields.status"
        >
          <el-radio value="active">
            <el-tag type="success" size="small">正常</el-tag>
          </el-radio>
          <el-radio value="inactive">
            <el-tag type="warning" size="small">暂停</el-tag>
          </el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item>
        <el-checkbox v-model="updateFields.fund_type" style="margin-bottom: 8px;">
          更新基金类型
        </el-checkbox>
        <el-select
          v-model="formData.fund_type"
          placeholder="选择基金类型"
          style="width: 100%"
          :disabled="!updateFields.fund_type"
          clearable
        >
          <el-option label="股票型" value="equity" />
          <el-option label="债券型" value="bond" />
          <el-option label="混合型" value="mixed" />
          <el-option label="货币型" value="money" />
        </el-select>
      </el-form-item>
      
      <el-divider />
      
      <el-form-item>
        <el-text type="warning" size="small">
          <el-icon><Warning /></el-icon>
          批量更新操作不可撤销，请确认后提交
        </el-text>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!hasUpdateFields"
          @click="handleSubmit"
        >
          {{ submitting ? '更新中...' : `批量更新 ${selectedStrategies.length} 项` }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { strategyAPI } from '@/api/strategy'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  selectedStrategies: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const submitting = ref(false)

// 对话框显示状态
const dialogVisible = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  }
})

// 要更新的字段标记
const updateFields = reactive({
  major_strategy: false,
  sub_strategy: false,
  is_qd: false,
  risk_level: false,
  status: false,
  fund_type: false
})

// 表单数据
const formData = reactive({
  major_strategy: '',
  sub_strategy: '',
  is_qd: true,
  risk_level: 'medium',
  status: 'active',
  fund_type: ''
})

// 表单验证规则
const formRules = computed(() => {
  const rules = {}
  
  if (updateFields.major_strategy) {
    rules.major_strategy = [
      { required: true, message: '请选择大类策略', trigger: 'change' }
    ]
  }
  
  if (updateFields.risk_level) {
    rules.risk_level = [
      { required: true, message: '请选择风险等级', trigger: 'change' }
    ]
  }
  
  if (updateFields.status) {
    rules.status = [
      { required: true, message: '请选择状态', trigger: 'change' }
    ]
  }
  
  return rules
})

// 是否有需要更新的字段
const hasUpdateFields = computed(() => {
  return Object.values(updateFields).some(value => value)
})

// 策略选项配置
const majorStrategies = ref([
  { label: '成长策略', value: 'growth' },
  { label: '固收策略', value: 'fixed_income' },
  { label: '宏观策略', value: 'macro' },
  { label: '其他策略', value: 'other' }
])

// 细分策略映射
const subStrategiesMap = {
  growth: [
    { label: '成长股投资', value: 'growth_stock' },
    { label: '中小盘成长', value: 'small_cap_growth' },
    { label: '科技成长', value: 'tech_growth' }
  ],
  fixed_income: [
    { label: '纯债策略', value: 'pure_bond' },
    { label: '信用债策略', value: 'credit_bond' },
    { label: '可转债策略', value: 'convertible_bond' }
  ],
  macro: [
    { label: '宏观对冲', value: 'macro_hedge' },
    { label: '商品期货', value: 'commodity_futures' },
    { label: '外汇策略', value: 'forex' }
  ],
  other: [
    { label: '市场中性', value: 'market_neutral' },
    { label: '事件驱动', value: 'event_driven' },
    { label: '套利策略', value: 'arbitrage' }
  ]
}

// 根据大类策略获取可用的细分策略
const availableSubStrategies = computed(() => {
  if (!formData.major_strategy) return []
  return subStrategiesMap[formData.major_strategy] || []
})

// 监听对话框显示状态
watch(() => props.modelValue, (visible) => {
  if (visible) {
    resetForm()
  }
})

// 处理大类策略变化
const handleMajorStrategyChange = (value) => {
  // 当大类策略变化时，清空细分策略
  if (!value || !subStrategiesMap[value]?.some(s => s.value === formData.sub_strategy)) {
    formData.sub_strategy = ''
  }
}

// 重置表单
const resetForm = () => {
  // 重置更新字段标记
  Object.keys(updateFields).forEach(key => {
    updateFields[key] = false
  })
  
  // 重置表单数据
  Object.assign(formData, {
    major_strategy: '',
    sub_strategy: '',
    is_qd: true,
    risk_level: 'medium',
    status: 'active',
    fund_type: ''
  })
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    // 确认操作
    await ElMessageBox.confirm(
      `确定要批量更新 ${props.selectedStrategies.length} 个策略配置吗？此操作不可撤销。`,
      '批量更新确认',
      {
        confirmButtonText: '确定更新',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const valid = await formRef.value.validate()
    if (!valid) return
    
    if (!hasUpdateFields.value) {
      ElMessage.warning('请至少选择一个要更新的字段')
      return
    }
    
    submitting.value = true
    
    // 构建更新数据
    const updateData = {}
    Object.keys(updateFields).forEach(key => {
      if (updateFields[key]) {
        updateData[key] = formData[key]
      }
    })
    
    // 获取基金代码列表
    const fundCodes = props.selectedStrategies.map(s => s.fund_code)
    
    const response = await strategyAPI.batchUpdateStrategy({
      fund_codes: fundCodes,
      update_data: updateData
    })
    
    if (response.success) {
      emit('success', response.data)
      handleClose()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量更新失败:', error)
      ElMessage.error(error.message || '批量更新失败')
    }
  } finally {
    submitting.value = false
  }
}

// 处理关闭
const handleClose = () => {
  if (submitting.value) return
  
  emit('update:modelValue', false)
  
  // 延迟重置表单，避免关闭动画时显示重置状态
  setTimeout(() => {
    resetForm()
  }, 300)
}
</script>

<style scoped>
.selected-strategies {
  margin-bottom: 20px;
}

.strategy-list {
  padding: 8px 0;
}

.dialog-footer {
  text-align: right;
}

.el-checkbox {
  margin-bottom: 8px;
  font-weight: 500;
}

.el-radio-group .el-radio {
  margin-right: 16px;
  margin-bottom: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .el-dialog {
    width: 90% !important;
    margin: 5vh auto !important;
  }
  
  .el-form {
    label-width: 80px !important;
  }
  
  .el-radio-group .el-radio {
    margin-right: 12px;
    margin-bottom: 12px;
  }
}
</style>