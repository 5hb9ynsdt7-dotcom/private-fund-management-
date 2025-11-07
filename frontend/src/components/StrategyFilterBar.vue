<template>
  <div class="strategy-filter-bar">
    <!-- 暂时隐藏所有筛选功能 -->
  </div>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:filters', 'search', 'reset'])

// 本地筛选条件
const localFilters = reactive({
  fundCode: '',
  fundName: ''
})

// 监听外部filters变化
watch(() => props.filters, (newFilters) => {
  Object.assign(localFilters, {
    fundCode: newFilters.fundCode || '',
    fundName: newFilters.fundName || ''
  })
}, { immediate: true, deep: true })

// 是否有激活的筛选条件
const hasActiveFilters = computed(() => {
  return (localFilters.fundCode && localFilters.fundCode.trim() !== '') || 
         (localFilters.fundName && localFilters.fundName.trim() !== '')
})

// 筛选结果统计文本
const filterSummaryText = computed(() => {
  const filters = []
  if (localFilters.fundCode) filters.push('基金代码')
  if (localFilters.fundName) filters.push('基金名称')
  return `正在按${filters.join('、')}筛选`
})

// 处理筛选（实时筛选）
const handleFilter = () => {
  emit('update:filters', localFilters)
  emit('search')
}

// 处理重置
const handleReset = () => {
  // 重置所有筛选条件
  Object.assign(localFilters, {
    fundCode: '',
    fundName: ''
  })
  
  emit('update:filters', localFilters)
  emit('reset')
}

// 清除基金代码筛选
const clearFundCode = () => {
  localFilters.fundCode = ''
  handleFilter()
}

// 清除基金名称筛选
const clearFundName = () => {
  localFilters.fundName = ''
  handleFilter()
}

// 清除所有筛选条件
const clearAllFilters = () => {
  handleReset()
}
</script>

<style scoped>
.strategy-filter-bar {
  margin-bottom: 16px;
}

.filter-form {
  margin-bottom: 0;
}

.filter-summary {
  margin-top: 12px;
}

.filter-summary .el-alert {
  background-color: #f0f9ff;
  border-color: #409eff;
}

/* 表单项间距调整 */
.el-form-item {
  margin-bottom: 12px;
  margin-right: 16px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .filter-form .el-form-item {
    margin-bottom: 8px;
  }
}

@media (max-width: 768px) {
  .strategy-filter-bar {
    margin-bottom: 12px;
  }
  
  .filter-form {
    display: block;
  }
  
  .filter-form .el-form-item {
    display: block;
    margin-right: 0;
    margin-bottom: 12px;
  }
  
  .filter-form .el-form-item .el-input {
    width: 100% !important;
  }
}
</style>