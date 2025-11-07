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
      
      <el-form-item label="大类策略" prop="main_strategy">
        <el-select
          v-model="formData.main_strategy"
          placeholder="选择大类策略"
          style="width: 100%"
          @change="handleMajorStrategyChange"
        >
          <el-option label="成长策略" value="成长配置" />
          <el-option label="底仓策略" value="底仓配置" />
          <el-option label="尾部对冲" value="尾部对冲" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="细分策略" prop="sub_strategy">
        <el-select
          v-model="formData.sub_strategy"
          placeholder="选择细分策略"
          style="width: 100%"
          :disabled="!formData.main_strategy"
          clearable
        >
          <el-option
            v-for="strategy in availableSubStrategies"
            :key="strategy"
            :label="strategy"
            :value="strategy"
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
  main_strategy: '',
  sub_strategy: '',
  is_qd: false
})

// 表单验证规则
const formRules = {
  fund_code: [
    { required: true, message: '请选择基金', trigger: 'change' }
  ],
  main_strategy: [
    { required: true, message: '请选择大类策略', trigger: 'change' }
  ],
  sub_strategy: [
    { required: true, message: '请选择细分策略', trigger: 'change' }
  ]
}

// 细分策略映射（与手动表单组件保持一致）
const strategyMapping = {
  '成长配置': ['主观多头', '多策略', '股债混合', '股票多头', '股票多空', '量化多头', '量化稳健'],
  '底仓配置': ['债券策略', '多策略', '稳健策略', '量化稳健'],
  '尾部对冲': ['CTA策略', '宏观策略']
}

// 根据大类策略获取可用的细分策略
const availableSubStrategies = computed(() => {
  if (!formData.main_strategy) return []
  return strategyMapping[formData.main_strategy] || []
})

// 监听策略数据变化
watch(() => props.strategyData, (newData) => {
  if (newData && props.mode === 'edit') {
    // 编辑模式，填充现有数据
    Object.assign(formData, {
      fund_code: newData.fund_code,
      main_strategy: newData.main_strategy,
      sub_strategy: newData.sub_strategy,
      is_qd: newData.is_qd
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
  formData.sub_strategy = ''
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  Object.assign(formData, {
    fund_code: '',
    main_strategy: '',
    sub_strategy: '',
    is_qd: false
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
      main_strategy: formData.main_strategy,
      sub_strategy: formData.sub_strategy,
      is_qd: formData.is_qd
    }
    
    const response = await strategyAPI.createOrUpdateStrategy(strategyData)
    
    // 后端直接返回 { action: 'created'/'updated', fund_code: 'L03126' }
    if (response.action) {
      emit('success', response)
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