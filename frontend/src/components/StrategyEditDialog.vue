<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="600px"
    :before-close="handleClose"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      size="default"
    >
      <el-form-item label="基金代码" prop="fund_code">
        <FundSelector
          v-model="formData.fund_code"
          :disabled="mode === 'edit'"
          placeholder="选择基金"
          @change="handleFundChange"
        />
      </el-form-item>
      
      <el-form-item label="基金名称">
        <el-input
          v-model="fundInfo.fund_name"
          placeholder="基金名称"
          readonly
        />
      </el-form-item>
      
      <el-form-item label="大类策略" prop="major_strategy">
        <el-select
          v-model="formData.major_strategy"
          placeholder="选择大类策略"
          style="width: 100%"
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
      
      <el-form-item label="细分策略" prop="sub_strategy">
        <el-select
          v-model="formData.sub_strategy"
          placeholder="选择细分策略"
          style="width: 100%"
          :disabled="!formData.major_strategy"
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
      
      <el-form-item label="QD状态" prop="is_qd">
        <el-switch
          v-model="formData.is_qd"
          active-text="是QD"
          inactive-text="非QD"
          active-color="#67c23a"
          inactive-color="#dcdfe6"
        />
        <el-text size="small" type="info" style="margin-left: 12px">
          QD策略将单独统计和管理
        </el-text>
      </el-form-item>
      
      <el-form-item label="风险等级" prop="risk_level">
        <el-radio-group v-model="formData.risk_level">
          <el-radio value="low">
            <el-icon color="#67c23a"><Star /></el-icon>
            低风险
          </el-radio>
          <el-radio value="medium">
            <el-icon color="#e6a23c"><Star /></el-icon>
            <el-icon color="#e6a23c"><Star /></el-icon>
            中风险
          </el-radio>
          <el-radio value="high">
            <el-icon color="#f56c6c"><Star /></el-icon>
            <el-icon color="#f56c6c"><Star /></el-icon>
            <el-icon color="#f56c6c"><Star /></el-icon>
            高风险
          </el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="formData.status">
          <el-radio value="active">
            <el-tag type="success" size="small">正常</el-tag>
          </el-radio>
          <el-radio value="inactive">
            <el-tag type="warning" size="small">暂停</el-tag>
          </el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item label="策略描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入策略描述（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
      
      <!-- 高级配置 -->
      <el-divider content-position="left">高级配置</el-divider>
      
      <el-form-item label="基金类型">
        <el-select
          v-model="formData.fund_type"
          placeholder="选择基金类型"
          style="width: 100%"
          clearable
        >
          <el-option label="股票型" value="equity" />
          <el-option label="债券型" value="bond" />
          <el-option label="混合型" value="mixed" />
          <el-option label="货币型" value="money" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="投资限制">
        <el-checkbox-group v-model="formData.investment_restrictions">
          <el-checkbox value="no_leverage">禁止杠杆</el-checkbox>
          <el-checkbox value="no_derivatives">禁止衍生品</el-checkbox>
          <el-checkbox value="sector_limit">行业限制</el-checkbox>
          <el-checkbox value="position_limit">仓位限制</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      
      <el-form-item label="风控参数">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-input
              v-model="formData.max_drawdown"
              placeholder="最大回撤%"
              type="number"
              step="0.1"
              min="0"
              max="100"
            >
              <template #append>%</template>
            </el-input>
          </el-col>
          <el-col :span="8">
            <el-input
              v-model="formData.max_position"
              placeholder="最大仓位%"
              type="number"
              step="0.1"
              min="0"
              max="100"
            >
              <template #append>%</template>
            </el-input>
          </el-col>
          <el-col :span="8">
            <el-input
              v-model="formData.stop_loss"
              placeholder="止损线%"
              type="number"
              step="0.1"
              min="0"
              max="100"
            >
              <template #append>%</template>
            </el-input>
          </el-col>
        </el-row>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ submitting ? '保存中...' : '确定' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import FundSelector from '@/components/FundSelector.vue'
import { strategyAPI } from '@/api/strategy'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  strategyData: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create' // create | edit
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const submitting = ref(false)
const fundInfo = ref({})

// 对话框显示状态
const dialogVisible = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    emit('update:modelValue', value)
  }
})

// 对话框标题
const dialogTitle = computed(() => {
  return props.mode === 'create' ? '新增策略' : '编辑策略'
})

// 表单数据
const formData = reactive({
  fund_code: '',
  major_strategy: '',
  sub_strategy: '',
  is_qd: false,
  risk_level: 'medium',
  status: 'active',
  description: '',
  fund_type: '',
  investment_restrictions: [],
  max_drawdown: '',
  max_position: '',
  stop_loss: ''
})

// 表单验证规则
const formRules = {
  fund_code: [
    { required: true, message: '请选择基金', trigger: 'change' }
  ],
  major_strategy: [
    { required: true, message: '请选择大类策略', trigger: 'change' }
  ],
  risk_level: [
    { required: true, message: '请选择风险等级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

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

// 监听策略数据变化
watch(() => props.strategyData, (newData) => {
  if (newData && props.mode === 'edit') {
    // 编辑模式，填充现有数据
    Object.assign(formData, {
      fund_code: newData.fund_code,
      major_strategy: newData.major_strategy,
      sub_strategy: newData.sub_strategy,
      is_qd: newData.is_qd,
      risk_level: newData.risk_level || 'medium',
      status: newData.status || 'active',
      description: newData.description || '',
      fund_type: newData.fund_type || '',
      investment_restrictions: newData.investment_restrictions || [],
      max_drawdown: newData.max_drawdown || '',
      max_position: newData.max_position || '',
      stop_loss: newData.stop_loss || ''
    })
    
    fundInfo.value = {
      fund_name: newData.fund_name
    }
  }
}, { immediate: true, deep: true })

// 监听对话框显示状态
watch(() => props.modelValue, (visible) => {
  if (visible && props.mode === 'create') {
    // 新增模式，重置表单
    resetForm()
  }
})

// 处理基金选择
const handleFundChange = async (fundCode, fund) => {
  if (fund) {
    fundInfo.value = fund
  } else if (fundCode) {
    // 如果只有基金代码，需要获取基金信息
    try {
      // const response = await fundAPI.getFundInfo(fundCode)
      // fundInfo.value = response.data || {}
      fundInfo.value = { fund_name: '加载中...' }
    } catch (error) {
      console.error('获取基金信息失败:', error)
    }
  }
}

// 处理大类策略变化
const handleMajorStrategyChange = (value) => {
  // 当大类策略变化时，清空细分策略
  if (!value || !subStrategiesMap[value]?.some(s => s.value === formData.sub_strategy)) {
    formData.sub_strategy = ''
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  Object.assign(formData, {
    fund_code: '',
    major_strategy: '',
    sub_strategy: '',
    is_qd: false,
    risk_level: 'medium',
    status: 'active',
    description: '',
    fund_type: '',
    investment_restrictions: [],
    max_drawdown: '',
    max_position: '',
    stop_loss: ''
  })
  
  fundInfo.value = {}
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    const strategyData = {
      fund_code: formData.fund_code,
      major_strategy: formData.major_strategy,
      sub_strategy: formData.sub_strategy || null,
      is_qd: formData.is_qd,
      risk_level: formData.risk_level,
      status: formData.status,
      description: formData.description || null,
      fund_type: formData.fund_type || null,
      investment_restrictions: formData.investment_restrictions.length ? formData.investment_restrictions : null,
      max_drawdown: formData.max_drawdown ? Number(formData.max_drawdown) : null,
      max_position: formData.max_position ? Number(formData.max_position) : null,
      stop_loss: formData.stop_loss ? Number(formData.stop_loss) : null
    }
    
    const response = await strategyAPI.createOrUpdateStrategy(strategyData)
    
    if (response.success) {
      const action = response.data.action || (props.mode === 'create' ? 'created' : 'updated')
      emit('success', { ...response.data, action })
      handleClose()
    }
  } catch (error) {
    console.error('保存策略失败:', error)
    ElMessage.error(error.message || '保存失败')
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
    if (props.mode === 'create') {
      resetForm()
    }
  }, 300)
}
</script>

<style scoped>
.dialog-footer {
  text-align: right;
}

.el-checkbox-group .el-checkbox {
  margin-right: 16px;
  margin-bottom: 8px;
}

.el-radio-group .el-radio {
  margin-right: 24px;
  margin-bottom: 8px;
}

.el-radio-group .el-radio .el-icon {
  margin-right: 4px;
}

/* 风控参数输入框样式 */
.el-input-group__append {
  background-color: #f5f7fa;
  border-left: 1px solid #dcdfe6;
  color: #909399;
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
  
  .el-checkbox-group .el-checkbox {
    margin-right: 12px;
    margin-bottom: 12px;
  }
}
</style>