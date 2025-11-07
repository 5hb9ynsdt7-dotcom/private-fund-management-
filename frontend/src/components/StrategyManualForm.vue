<template>
  <div class="strategy-manual-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="90px"
      size="default"
    >
      <el-form-item label="基金代码" prop="fund_code">
        <el-input
          v-model="formData.fund_code"
          placeholder="请输入6位基金代码（如：F00058）"
          clearable
          maxlength="6"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="基金名称" prop="fund_name">
        <el-input
          v-model="formData.fund_name"
          placeholder="请输入基金名称"
          clearable
        />
      </el-form-item>
      
      <el-form-item label="大类策略" prop="main_strategy">
        <el-select
          v-model="formData.main_strategy"
          placeholder="请选择大类策略"
          style="width: 100%"
          clearable
          @change="handleMajorStrategyChange"
        >
          <el-option label="成长配置" value="成长配置" />
          <el-option label="成长策略" value="成长策略" />
          <el-option label="底仓配置" value="底仓配置" />
          <el-option label="固收策略" value="固收策略" />
          <el-option label="尾部对冲" value="尾部对冲" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="细分策略" prop="sub_strategy">
        <el-select
          v-model="formData.sub_strategy"
          placeholder="请选择细分策略"
          style="width: 100%"
          clearable
          :disabled="!formData.main_strategy"
        >
          <el-option
            v-for="subStrategy in availableSubStrategies"
            :key="subStrategy"
            :label="subStrategy"
            :value="subStrategy"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="是否QD" prop="is_qd">
        <el-select
          v-model="formData.is_qd"
          placeholder="请选择"
          style="width: 100%"
        >
          <el-option label="是" :value="true" />
          <el-option label="否" :value="false" />
        </el-select>
      </el-form-item>
      
      <el-form-item>
        <el-space>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            <el-icon><Plus /></el-icon>
            {{ submitting ? '添加中...' : '添加策略' }}
          </el-button>
          
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-space>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { strategyAPI } from '@/api/strategy'

const emit = defineEmits(['success'])

const formRef = ref()
const submitting = ref(false)

// 策略分类映射（基于实际数据分析）
const strategyMapping = {
  '成长配置': ['主观多头', '多策略', '股债混合', '股票多头', '股票多空', '量化多头', '量化稳健'],
  '成长策略': ['量化多头'],
  '底仓配置': ['债券策略', '多策略', '稳健策略', '量化稳健'],
  '固收策略': ['债券投资'],
  '尾部对冲': ['CTA策略', '宏观策略']
}

// 表单数据
const formData = reactive({
  fund_code: '',
  fund_name: '',
  main_strategy: '',
  sub_strategy: '',
  is_qd: null
})

// 表单验证规则
const formRules = {
  fund_code: [
    { required: true, message: '请输入基金代码', trigger: 'blur' },
    { len: 6, message: '基金代码必须是6个字符', trigger: 'blur' },
    { 
      pattern: /^[A-Za-z0-9]+$/, 
      message: '基金代码只能包含字母和数字', 
      trigger: 'blur' 
    }
  ],
  fund_name: [
    { required: true, message: '请输入基金名称', trigger: 'blur' },
    { min: 2, max: 100, message: '基金名称长度在2到100个字符', trigger: 'blur' }
  ],
  main_strategy: [
    { required: true, message: '请选择大类策略', trigger: 'change' }
  ],
  sub_strategy: [
    { required: true, message: '请输入细分策略', trigger: 'blur' }
  ],
  is_qd: [
    { required: true, message: '请选择是否QD', trigger: 'change' }
  ]
}

// 根据大类策略获取可用的细分策略
const availableSubStrategies = computed(() => {
  if (!formData.main_strategy) return []
  return strategyMapping[formData.main_strategy] || []
})

// 处理大类策略变化
const handleMajorStrategyChange = (value) => {
  // 清空细分策略选择
  formData.sub_strategy = ''
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    const strategyData = {
      fund_code: formData.fund_code.trim(),
      fund_name: formData.fund_name.trim(),
      main_strategy: formData.main_strategy,
      sub_strategy: formData.sub_strategy.trim(),
      is_qd: formData.is_qd
    }
    
    const response = await strategyAPI.createOrUpdateStrategy(strategyData)
    
    // 后端直接返回 { action: 'created'/'updated', fund_code: 'L03126' }
    if (response.action) {
      const actionText = response.action === 'created' ? '创建' : '更新'
      ElMessage.success(`策略${actionText}成功`)
      emit('success', response)
      handleReset()
    }
  } catch (error) {
    console.error('添加策略失败:', error)
    ElMessage.error(error.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const handleReset = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  
  Object.assign(formData, {
    fund_code: '',
    fund_name: '',
    main_strategy: '',
    sub_strategy: '',
    is_qd: null
  })
}

// 暴露方法
defineExpose({
  reset: handleReset,
  submit: handleSubmit
})
</script>

<style scoped>
.strategy-manual-form {
  width: 100%;
}

/* 表单样式优化 */
.el-form-item {
  margin-bottom: 18px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .el-form {
    label-width: 80px !important;
  }
  
  .el-form-item {
    margin-bottom: 16px;
  }
}

@media (max-width: 480px) {
  .el-form {
    label-width: 70px !important;
  }
}
</style>