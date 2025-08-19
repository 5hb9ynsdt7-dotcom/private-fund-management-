<template>
  <el-select
    v-model="selectedFund"
    placeholder="请选择或搜索基金"
    filterable
    remote
    reserve-keyword
    :remote-method="searchFunds"
    :loading="loading"
    clearable
    style="width: 100%"
    @change="handleChange"
  >
    <template #prefix>
      <el-icon><Search /></el-icon>
    </template>
    
    <el-option
      v-for="fund in fundOptions"
      :key="fund.fund_code"
      :label="`${fund.fund_code} - ${fund.fund_name}`"
      :value="fund.fund_code"
    >
      <div class="fund-option">
        <div class="fund-info">
          <span class="fund-code">{{ fund.fund_code }}</span>
          <span class="fund-name">{{ fund.fund_name }}</span>
        </div>
        <div class="fund-meta" v-if="fund.strategy">
          <el-tag size="small" type="info">{{ fund.strategy }}</el-tag>
        </div>
      </div>
    </el-option>
    
    <template #empty>
      <div class="empty-data">
        <el-icon><DocumentCopy /></el-icon>
        <p>{{ searchQuery ? '未找到匹配的基金' : '请输入基金代码或名称搜索' }}</p>
      </div>
    </template>
  </el-select>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { navAPI } from '@/api/nav'
import { debounce } from '@/utils'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  showStrategy: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectedFund = ref(props.modelValue)
const fundOptions = ref([])
const loading = ref(false)
const searchQuery = ref('')

// 防抖搜索
const searchFunds = debounce(async (query) => {
  if (!query) {
    await loadDefaultFunds()
    return
  }
  
  searchQuery.value = query
  loading.value = true
  
  try {
    const response = await navAPI.getFundsWithNav()
    if (response.success && response.data?.funds) {
      // 根据查询条件过滤基金
      fundOptions.value = response.data.funds.filter(fund => 
        fund.fund_code.toLowerCase().includes(query.toLowerCase()) ||
        fund.fund_name.toLowerCase().includes(query.toLowerCase())
      )
    }
  } catch (error) {
    console.error('搜索基金失败:', error)
    fundOptions.value = []
  } finally {
    loading.value = false
  }
}, 300)

// 加载默认基金列表
const loadDefaultFunds = async () => {
  loading.value = true
  try {
    const response = await navAPI.getFundsWithNav()
    if (response.success && response.data?.funds) {
      fundOptions.value = response.data.funds.slice(0, 20) // 默认显示前20个
    }
  } catch (error) {
    console.error('加载基金列表失败:', error)
    fundOptions.value = []
  } finally {
    loading.value = false
  }
}

// 处理选择变化
const handleChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value, fundOptions.value.find(f => f.fund_code === value))
}

// 初始化
onMounted(() => {
  loadDefaultFunds()
})

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  selectedFund.value = newVal
})
</script>

<style scoped>
.fund-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.fund-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.fund-code {
  font-weight: 600;
  color: #409EFF;
  font-size: 13px;
}

.fund-name {
  color: #606266;
  font-size: 12px;
  line-height: 1.2;
}

.fund-meta {
  display: flex;
  gap: 4px;
}

.empty-data {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.empty-data .el-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.empty-data p {
  margin: 0;
  font-size: 12px;
}
</style>