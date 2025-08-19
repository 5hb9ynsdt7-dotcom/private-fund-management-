<template>
  <div class="nav-filter-bar">
    <el-form 
      :model="localFilters" 
      inline 
      size="default"
      class="filter-form"
    >
      <el-form-item label="基金代码">
        <el-input
          v-model="localFilters.fundCode"
          placeholder="输入基金代码"
          clearable
          style="width: 160px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      
      <el-form-item label="净值日期">
        <el-date-picker
          v-model="localFilters.navDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 160px"
          clearable
        />
      </el-form-item>
      
      <el-form-item label="日期范围">
        <el-date-picker
          v-model="localFilters.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 240px"
          clearable
        />
      </el-form-item>
      
      <el-form-item>
        <el-space>
          <el-button 
            type="primary" 
            @click="handleSearch"
          >
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          
          <el-button 
            text 
            type="info"
            @click="toggleAdvanced"
          >
            <el-icon>
              <ArrowDown v-if="!showAdvanced" />
              <ArrowUp v-else />
            </el-icon>
            {{ showAdvanced ? '收起' : '高级筛选' }}
          </el-button>
        </el-space>
      </el-form-item>
    </el-form>
    
    <!-- 高级筛选 -->
    <el-collapse-transition>
      <div v-show="showAdvanced" class="advanced-filters">
        <el-divider content-position="left">
          <span class="divider-text">高级筛选</span>
        </el-divider>
        
        <el-form 
          :model="advancedFilters" 
          inline 
          size="default"
          class="advanced-form"
        >
          <el-form-item label="基金名称">
            <el-input
              v-model="advancedFilters.fundName"
              placeholder="输入基金名称"
              clearable
              style="width: 200px"
            />
          </el-form-item>
          
          <el-form-item label="净值范围">
            <el-input
              v-model="advancedFilters.minNav"
              placeholder="最小值"
              type="number"
              step="0.01"
              style="width: 100px"
            />
            <span style="margin: 0 8px">-</span>
            <el-input
              v-model="advancedFilters.maxNav"
              placeholder="最大值"
              type="number"
              step="0.01"
              style="width: 100px"
            />
          </el-form-item>
          
          <el-form-item label="数据状态">
            <el-select
              v-model="advancedFilters.dataStatus"
              placeholder="选择状态"
              clearable
              style="width: 120px"
            >
              <el-option label="全部" value="" />
              <el-option label="正常" value="normal" />
              <el-option label="异常" value="abnormal" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="快速日期">
            <el-select
              v-model="quickDateRange"
              placeholder="选择时间范围"
              clearable
              style="width: 120px"
              @change="handleQuickDateChange"
            >
              <el-option label="今天" value="today" />
              <el-option label="昨天" value="yesterday" />
              <el-option label="本周" value="thisWeek" />
              <el-option label="本月" value="thisMonth" />
              <el-option label="上月" value="lastMonth" />
              <el-option label="近7天" value="last7Days" />
              <el-option label="近30天" value="last30Days" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
    </el-collapse-transition>
    
    <!-- 筛选结果统计 -->
    <div v-if="hasActiveFilters" class="filter-summary">
      <el-alert
        :title="filterSummaryText"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <el-space wrap>
            <el-tag
              v-for="(filter, key) in activeFiltersDisplay"
              :key="key"
              closable
              @close="clearSingleFilter(key)"
            >
              {{ filter }}
            </el-tag>
            <el-button
              size="small"
              text
              type="danger"
              @click="clearAllFilters"
            >
              清除所有筛选
            </el-button>
          </el-space>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { formatDate } from '@/utils'

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:filters', 'search', 'reset'])

const showAdvanced = ref(false)
const quickDateRange = ref('')

// 本地筛选条件
const localFilters = reactive({
  fundCode: '',
  navDate: null,
  dateRange: null
})

// 高级筛选条件
const advancedFilters = reactive({
  fundName: '',
  minNav: '',
  maxNav: '',
  dataStatus: ''
})

// 监听外部filters变化
watch(() => props.filters, (newFilters) => {
  Object.assign(localFilters, {
    fundCode: newFilters.fundCode || '',
    navDate: newFilters.navDate || null,
    dateRange: newFilters.dateRange || null
  })
}, { immediate: true, deep: true })

// 是否有激活的筛选条件
const hasActiveFilters = computed(() => {
  return Object.values(localFilters).some(value => 
    value !== null && value !== undefined && value !== ''
  ) || Object.values(advancedFilters).some(value => 
    value !== null && value !== undefined && value !== ''
  )
})

// 激活筛选条件的显示
const activeFiltersDisplay = computed(() => {
  const filters = {}
  
  if (localFilters.fundCode) {
    filters.fundCode = `基金代码: ${localFilters.fundCode}`
  }
  
  if (localFilters.navDate) {
    filters.navDate = `净值日期: ${localFilters.navDate}`
  }
  
  if (localFilters.dateRange && localFilters.dateRange.length === 2) {
    filters.dateRange = `日期范围: ${localFilters.dateRange[0]} ~ ${localFilters.dateRange[1]}`
  }
  
  if (advancedFilters.fundName) {
    filters.fundName = `基金名称: ${advancedFilters.fundName}`
  }
  
  if (advancedFilters.minNav || advancedFilters.maxNav) {
    const min = advancedFilters.minNav || '不限'
    const max = advancedFilters.maxNav || '不限'
    filters.navRange = `净值范围: ${min} ~ ${max}`
  }
  
  if (advancedFilters.dataStatus) {
    const statusMap = { normal: '正常', abnormal: '异常' }
    filters.dataStatus = `状态: ${statusMap[advancedFilters.dataStatus]}`
  }
  
  return filters
})

// 筛选结果统计文本
const filterSummaryText = computed(() => {
  const count = Object.keys(activeFiltersDisplay.value).length
  return `当前有 ${count} 个筛选条件`
})

// 切换高级筛选
const toggleAdvanced = () => {
  showAdvanced.value = !showAdvanced.value
}

// 处理搜索
const handleSearch = () => {
  const allFilters = {
    ...localFilters,
    ...advancedFilters
  }
  
  emit('update:filters', allFilters)
  emit('search')
}

// 处理重置
const handleReset = () => {
  // 重置所有筛选条件
  Object.assign(localFilters, {
    fundCode: '',
    navDate: null,
    dateRange: null
  })
  
  Object.assign(advancedFilters, {
    fundName: '',
    minNav: '',
    maxNav: '',
    dataStatus: ''
  })
  
  quickDateRange.value = ''
  
  emit('update:filters', localFilters)
  emit('reset')
}

// 清除单个筛选条件
const clearSingleFilter = (filterKey) => {
  if (filterKey in localFilters) {
    if (filterKey === 'dateRange') {
      localFilters[filterKey] = null
    } else {
      localFilters[filterKey] = ''
    }
  } else if (filterKey in advancedFilters) {
    advancedFilters[filterKey] = ''
  }
  
  // 特殊处理净值范围
  if (filterKey === 'navRange') {
    advancedFilters.minNav = ''
    advancedFilters.maxNav = ''
  }
  
  handleSearch()
}

// 清除所有筛选条件
const clearAllFilters = () => {
  handleReset()
}

// 处理快速日期选择
const handleQuickDateChange = (value) => {
  if (!value) {
    localFilters.dateRange = null
    return
  }
  
  const today = new Date()
  let startDate, endDate
  
  switch (value) {
    case 'today':
      startDate = endDate = today
      break
    case 'yesterday':
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      startDate = endDate = yesterday
      break
    case 'thisWeek':
      const startOfWeek = new Date(today)
      startOfWeek.setDate(today.getDate() - today.getDay())
      startDate = startOfWeek
      endDate = today
      break
    case 'thisMonth':
      startDate = new Date(today.getFullYear(), today.getMonth(), 1)
      endDate = today
      break
    case 'lastMonth':
      const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0)
      startDate = lastMonth
      endDate = lastMonthEnd
      break
    case 'last7Days':
      const last7Days = new Date(today)
      last7Days.setDate(today.getDate() - 6)
      startDate = last7Days
      endDate = today
      break
    case 'last30Days':
      const last30Days = new Date(today)
      last30Days.setDate(today.getDate() - 29)
      startDate = last30Days
      endDate = today
      break
  }
  
  if (startDate && endDate) {
    localFilters.dateRange = [
      formatDate(startDate),
      formatDate(endDate)
    ]
  }
}
</script>

<style scoped>
.nav-filter-bar {
  margin-bottom: 16px;
}

.filter-form {
  margin-bottom: 0;
}

.advanced-filters {
  background-color: #fafafa;
  padding: 16px;
  border-radius: 6px;
  margin-top: 8px;
}

.divider-text {
  font-size: 12px;
  color: #909399;
}

.advanced-form {
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
  
  .advanced-form .el-form-item {
    margin-bottom: 8px;
  }
}

@media (max-width: 768px) {
  .nav-filter-bar {
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
  
  .filter-form .el-form-item .el-input,
  .filter-form .el-form-item .el-date-picker,
  .filter-form .el-form-item .el-select {
    width: 100% !important;
  }
  
  .advanced-filters {
    padding: 12px;
  }
  
  .advanced-form {
    display: block;
  }
  
  .advanced-form .el-form-item {
    display: block;
    margin-right: 0;
    margin-bottom: 12px;
  }
}
</style>