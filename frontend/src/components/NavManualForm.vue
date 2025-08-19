<template>
  <div class="nav-manual-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="80px"
      size="default"
    >
      <el-form-item label="基金" prop="fund_code">
        <FundSelector
          v-model="formData.fund_code"
          placeholder="选择或搜索基金"
          @change="handleFundChange"
        />
      </el-form-item>
      
      <el-form-item label="净值日期" prop="nav_date">
        <el-date-picker
          v-model="formData.nav_date"
          type="date"
          placeholder="选择净值日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="单位净值" prop="unit_nav">
        <el-input
          v-model="formData.unit_nav"
          placeholder="请输入单位净值"
          type="number"
          step="0.0001"
          min="0"
        >
          <template #append>元</template>
        </el-input>
      </el-form-item>
      
      <el-form-item label="累计净值" prop="accum_nav">
        <el-input
          v-model="formData.accum_nav"
          placeholder="请输入累计净值"
          type="number"
          step="0.0001"
          min="0"
        >
          <template #append>元</template>
        </el-input>
      </el-form-item>
      
      <el-form-item>
        <el-space>
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            <el-icon><Plus /></el-icon>
            {{ submitting ? '添加中...' : '添加净值' }}
          </el-button>
          
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          
          <el-button
            v-if="showQuickFill"
            type="info"
            text
            @click="handleQuickFill"
          >
            <el-icon><Magic /></el-icon>
            快速填充
          </el-button>
        </el-space>
      </el-form-item>
    </el-form>
    
    <!-- 快速操作提示 -->
    <div v-if="lastNav" class="quick-tip">
      <el-alert
        :title="`上次 ${lastNav.fund_code} 净值：${lastNav.unit_nav}`"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>上次净值：单位 {{ lastNav.unit_nav }}，累计 {{ lastNav.accum_nav }}</p>
          <el-button
            size="small"
            text
            type="primary"
            @click="copyLastNav"
          >
            复制上次数据
          </el-button>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import FundSelector from '@/components/FundSelector.vue'
import { navAPI } from '@/api/nav'
import { formatDate } from '@/utils'

const emit = defineEmits(['success'])

const formRef = ref()
const submitting = ref(false)
const lastNav = ref(null)

// 表单数据
const formData = reactive({
  fund_code: '',
  nav_date: formatDate(new Date()),
  unit_nav: '',
  accum_nav: ''
})

// 表单验证规则
const formRules = {
  fund_code: [
    { required: true, message: '请选择基金', trigger: 'change' }
  ],
  nav_date: [
    { required: true, message: '请选择净值日期', trigger: 'change' }
  ],
  unit_nav: [
    { required: true, message: '请输入单位净值', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value && (isNaN(value) || Number(value) <= 0)) {
          callback(new Error('单位净值必须大于0'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ],
  accum_nav: [
    { required: true, message: '请输入累计净值', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value && (isNaN(value) || Number(value) <= 0)) {
          callback(new Error('累计净值必须大于0'))
        } else if (formData.unit_nav && value && Number(value) < Number(formData.unit_nav)) {
          callback(new Error('累计净值不能小于单位净值'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

// 是否显示快速填充
const showQuickFill = computed(() => {
  return formData.fund_code && formData.nav_date
})

// 监听基金变化，获取最新净值
watch(() => formData.fund_code, async (newFundCode) => {
  if (newFundCode) {
    await loadLastNav(newFundCode)
  } else {
    lastNav.value = null
  }
})

// 处理基金选择
const handleFundChange = (fundCode, fundInfo) => {
  console.log('选择基金:', fundCode, fundInfo)
  // 基金变化时清空净值数据
  formData.unit_nav = ''
  formData.accum_nav = ''
}

// 加载最新净值
const loadLastNav = async (fundCode) => {
  try {
    const response = await navAPI.getLatestNav(fundCode)
    if (response.success && response.data) {
      lastNav.value = response.data
    }
  } catch (error) {
    console.error('获取最新净值失败:', error)
    lastNav.value = null
  }
}

// 复制上次净值数据
const copyLastNav = () => {
  if (lastNav.value) {
    formData.unit_nav = lastNav.value.unit_nav
    formData.accum_nav = lastNav.value.accum_nav
    ElMessage.success('已复制上次净值数据')
  }
}

// 快速填充（基于历史数据智能预测）
const handleQuickFill = async () => {
  try {
    const response = await navAPI.predictNav({
      fund_code: formData.fund_code,
      nav_date: formData.nav_date
    })
    
    if (response.success && response.data) {
      formData.unit_nav = response.data.predicted_unit_nav
      formData.accum_nav = response.data.predicted_accum_nav
      ElMessage.success('已自动填充预测净值')
    }
  } catch (error) {
    console.error('智能填充失败:', error)
    ElMessage.error('智能填充功能暂时不可用')
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return
    
    submitting.value = true
    
    const navData = {
      fund_code: formData.fund_code,
      nav_date: formData.nav_date,
      unit_nav: Number(formData.unit_nav),
      accum_nav: Number(formData.accum_nav)
    }
    
    const response = await navAPI.createNavManual(navData)
    
    if (response.success) {
      ElMessage.success('净值添加成功')
      emit('success', response.data)
      handleReset()
    }
  } catch (error) {
    console.error('添加净值失败:', error)
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
  
  // 保持当前日期
  formData.nav_date = formatDate(new Date())
  lastNav.value = null
}

// 暴露方法
defineExpose({
  reset: handleReset,
  submit: handleSubmit
})
</script>

<style scoped>
.nav-manual-form {
  width: 100%;
}

.quick-tip {
  margin-top: 16px;
}

.quick-tip p {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
}

/* 表单样式优化 */
.el-form-item {
  margin-bottom: 18px;
}

.el-input-number {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .el-form {
    label-width: 70px !important;
  }
  
  .el-form-item {
    margin-bottom: 16px;
  }
}

@media (max-width: 480px) {
  .el-form {
    label-width: 60px !important;
  }
  
  .quick-tip {
    margin-top: 12px;
  }
}
</style>