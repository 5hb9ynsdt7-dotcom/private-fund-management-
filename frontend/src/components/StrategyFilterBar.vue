<template>
  <div class="strategy-filter-bar">
    <el-form 
      :model="localFilters" 
      inline 
      size="default"
      class="filter-form"
    >
      <el-form-item label="大类策略">
        <el-select
          v-model="localFilters.majorStrategy"
          placeholder="选择大类策略"
          clearable
          style="width: 140px"
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
      
      <el-form-item label="细分策略">
        <el-select
          v-model="localFilters.subStrategy"
          placeholder="选择细分策略"
          clearable
          style="width: 140px"
          :disabled="!localFilters.majorStrategy"
        >
          <el-option
            v-for="strategy in availableSubStrategies"
            :key="strategy.value"
            :label="strategy.label"
            :value="strategy.value"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="QD状态">
        <el-select
          v-model="localFilters.isQd"
          placeholder="选择QD状态"
          clearable
          style="width: 120px"
        >
          <el-option label="全部" :value="null" />
          <el-option label="是QD" :value="true" />
          <el-option label="非QD" :value="false" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="状态">
        <el-select
          v-model="localFilters.status"
          placeholder="选择状态"
          clearable
          style="width: 120px"
        >
          <el-option label="全部" value="" />
          <el-option label="正常" value="active" />
          <el-option label="暂停" value="inactive" />
        </el-select>
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
          <el-form-item label="基金类型">
            <el-select
              v-model="advancedFilters.fundType"
              placeholder="选择基金类型"
              clearable
              style="width: 140px"
            >
              <el-option label="全部" value="" />
              <el-option label="股票型" value="equity" />
              <el-option label="债券型" value="bond" />
              <el-option label="混合型" value="mixed" />
              <el-option label="货币型" value="money" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="风险等级">
            <el-select
              v-model="advancedFilters.riskLevel"
              placeholder="选择风险等级"
              clearable
              style="width: 120px"
            >
              <el-option label="全部" value="" />
              <el-option label="低风险" value="low" />
              <el-option label="中风险" value="medium" />
              <el-option label="高风险" value="high" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="创建时间">
            <el-date-picker
              v-model="advancedFilters.createDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 220px"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="更新时间">
            <el-date-picker
              v-model="advancedFilters.updateDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 220px"
              clearable
            />
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

const props = defineProps({
  filters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:filters', 'search', 'reset'])

const showAdvanced = ref(false)

// 本地筛选条件
const localFilters = reactive({
  majorStrategy: '',
  subStrategy: '',
  isQd: null,
  status: ''
})

// 高级筛选条件
const advancedFilters = reactive({
  fundType: '',
  riskLevel: '',
  createDateRange: null,
  updateDateRange: null
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
  if (!localFilters.majorStrategy) return []
  return subStrategiesMap[localFilters.majorStrategy] || []
})

// 监听外部filters变化
watch(() => props.filters, (newFilters) => {
  Object.assign(localFilters, {
    majorStrategy: newFilters.majorStrategy || '',
    subStrategy: newFilters.subStrategy || '',
    isQd: newFilters.isQd ?? null,
    status: newFilters.status || ''
  })
}, { immediate: true, deep: true })

// 处理大类策略变化
const handleMajorStrategyChange = (value) => {
  // 当大类策略变化时，清空细分策略
  if (!value || !subStrategiesMap[value]?.some(s => s.value === localFilters.subStrategy)) {
    localFilters.subStrategy = ''
  }
}

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
  
  if (localFilters.majorStrategy) {
    const major = majorStrategies.value.find(s => s.value === localFilters.majorStrategy)
    filters.majorStrategy = `大类策略: ${major?.label || localFilters.majorStrategy}`
  }
  
  if (localFilters.subStrategy) {
    const sub = availableSubStrategies.value.find(s => s.value === localFilters.subStrategy)
    filters.subStrategy = `细分策略: ${sub?.label || localFilters.subStrategy}`
  }
  
  if (localFilters.isQd !== null) {
    filters.isQd = `QD状态: ${localFilters.isQd ? '是QD' : '非QD'}`
  }
  
  if (localFilters.status) {
    const statusMap = { active: '正常', inactive: '暂停' }
    filters.status = `状态: ${statusMap[localFilters.status] || localFilters.status}`
  }
  
  if (advancedFilters.fundType) {
    const typeMap = { equity: '股票型', bond: '债券型', mixed: '混合型', money: '货币型' }
    filters.fundType = `基金类型: ${typeMap[advancedFilters.fundType]}`
  }
  
  if (advancedFilters.riskLevel) {
    const levelMap = { low: '低风险', medium: '中风险', high: '高风险' }
    filters.riskLevel = `风险等级: ${levelMap[advancedFilters.riskLevel]}`
  }
  
  if (advancedFilters.createDateRange && advancedFilters.createDateRange.length === 2) {
    filters.createDateRange = `创建时间: ${advancedFilters.createDateRange[0]} ~ ${advancedFilters.createDateRange[1]}`
  }
  
  if (advancedFilters.updateDateRange && advancedFilters.updateDateRange.length === 2) {
    filters.updateDateRange = `更新时间: ${advancedFilters.updateDateRange[0]} ~ ${advancedFilters.updateDateRange[1]}`
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
    majorStrategy: '',
    subStrategy: '',
    isQd: null,
    status: ''
  })
  
  Object.assign(advancedFilters, {
    fundType: '',
    riskLevel: '',
    createDateRange: null,
    updateDateRange: null
  })
  
  emit('update:filters', localFilters)
  emit('reset')
}

// 清除单个筛选条件
const clearSingleFilter = (filterKey) => {
  if (filterKey in localFilters) {
    if (filterKey === 'isQd') {
      localFilters[filterKey] = null
    } else {
      localFilters[filterKey] = ''
    }
  } else if (filterKey in advancedFilters) {
    if (filterKey.includes('DateRange')) {
      advancedFilters[filterKey] = null
    } else {
      advancedFilters[filterKey] = ''
    }
  }
  
  handleSearch()
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
  
  .advanced-form .el-form-item .el-select,
  .advanced-form .el-form-item .el-date-picker {
    width: 100% !important;
  }
}
</style>