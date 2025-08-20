<template>
  <div class="position-detail">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>{{ getPageTitle() }}</h2>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
    </div>
    
    <!-- 收益概览卡片 -->
    <el-row :gutter="24" class="revenue-overview" v-loading="loading">
      <el-col :span="6">
        <el-card class="overview-card">
          <el-statistic
            title="总投资金额"
            :value="positionData.revenue_overview?.total_investment || 0"
            :precision="0"
            suffix="元"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><Money /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <el-statistic
            title="总持仓市值"
            :value="positionData.revenue_overview?.total_market_value || 0"
            :precision="0"
            suffix="元"
          >
            <template #prefix>
              <el-icon style="color: #67c23a"><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <el-statistic
            title="累计盈亏"
            :value="positionData.revenue_overview?.total_pnl || 0"
            :precision="0"
            suffix="元"
          >
            <template #prefix>
              <el-icon :style="`color: ${getPnlColor(positionData.revenue_overview?.total_pnl)}`">
                <DataAnalysis />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="overview-card">
          <el-statistic
            title="今年以来收益"
            :value="positionData.revenue_overview?.ytd_return || 0"
            :precision="0"
            suffix="元"
          >
            <template #prefix>
              <el-icon :style="`color: ${getPnlColor(positionData.revenue_overview?.ytd_return)}`">
                <Calendar />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 策略分布图表 -->
    <el-row :gutter="24" class="charts-section">
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>持仓分布</span>
          </template>
          <div ref="holdingChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>大类策略分布</span>
          </template>
          <div ref="majorStrategyChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>细分策略分布</span>
          </template>
          <div ref="subStrategyChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 持仓明细表格 -->
    <el-card class="position-table-card">
      <template #header>
        <div class="table-header">
          <span>持仓明细</span>
          <div class="table-controls">
            <div class="period-filter">
              <span>阶段收益计算：</span>
              <el-date-picker
                v-model="periodRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handlePeriodChange"
                size="small"
                style="width: 240px; margin-right: 12px;"
              />
            </div>
            <el-select v-model="sortBy" @change="sortTable" size="small">
              <el-option label="按策略分组" value="strategy" />
              <el-option label="按买入时间" value="date" />
              <el-option label="按持仓市值" value="value" />
            </el-select>
          </div>
        </div>
      </template>
      
      <!-- 按策略分组显示 -->
      <div v-if="sortBy === 'strategy'">
        <!-- 统一表格显示所有分组 -->
        <el-table
          :data="getGroupedTableData()"
          stripe
          border
          size="small"
          class="position-table"
          :row-class-name="getRowClassName"
          style="width: 100%"
        >
          <el-table-column prop="fund_name" label="基金名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="sub_strategy" label="细分策略" width="90" align="center">
            <template #default="{ row }">
              <div v-if="row.rowType === 'data'" class="strategy-cell">
                <span>{{ row.sub_strategy }}</span>
                <el-tag v-if="row.is_qd" type="danger" size="small" class="qd-tag">QD</el-tag>
              </div>
              <span v-else>{{ row.sub_strategy }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="first_buy_date" label="买入日期" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType === 'data'">{{ formatDate(row.first_buy_date) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="cost_with_fee" label="买入金额" width="110" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType !== 'header'" :class="row.rowType === 'summary' ? 'summary-text' : ''">
                {{ formatMoney(row.cost_with_fee) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="shares" label="持仓份额" width="110" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType === 'data'">{{ formatShares(row.shares) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="buy_nav" label="买入净值" width="90" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType === 'data'">{{ formatNav(row.buy_nav) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="latest_nav" label="最新净值" width="90" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType === 'data'">{{ formatNav(row.latest_nav) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="latest_nav_date" label="净值日期" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType === 'data'">{{ formatDate(row.latest_nav_date) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="holding_return" label="持有收益" width="110" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType !== 'header'" 
                    :class="[getPnlClass(row.holding_return), row.rowType === 'summary' ? 'summary-text' : '']">
                {{ formatMoney(row.holding_return) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="holding_return_rate" label="持有收益率" width="100" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType !== 'header'" 
                    :class="[getPnlClass(row.holding_return_rate), row.rowType === 'summary' ? 'summary-text' : '']">
                {{ formatPercent(row.holding_return_rate) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="period_return" label="阶段收益" width="110" align="center">
            <template #default="{ row }">
              <span v-if="row.rowType !== 'header'" 
                    :class="[getPnlClass(row.period_return), row.rowType === 'summary' || row.rowType === 'total' ? 'summary-text' : '']">
                {{ row.period_return !== null && row.period_return !== undefined ? formatMoney(row.period_return) : '--' }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 其他排序方式的表格 -->
      <el-table
        v-else
        :data="getSortedPositions()"
        stripe
        border
        class="position-table"
        style="width: 100%"
      >
        <el-table-column prop="fund_name" label="基金名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="major_strategy" label="大类策略" width="90" align="center" />
        <el-table-column prop="sub_strategy" label="细分策略" width="90" align="center">
          <template #default="{ row }">
            <div class="strategy-cell">
              <span>{{ row.sub_strategy }}</span>
              <el-tag v-if="row.is_qd" type="danger" size="small" class="qd-tag">QD</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="first_buy_date" label="买入日期" width="100" align="center">
          <template #default="{ row }">
            {{ formatDate(row.first_buy_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="cost_with_fee" label="买入金额" width="110" align="center">
          <template #default="{ row }">
            {{ formatMoney(row.cost_with_fee) }}
          </template>
        </el-table-column>
        <el-table-column prop="shares" label="持仓份额" width="110" align="center">
          <template #default="{ row }">
            {{ formatShares(row.shares) }}
          </template>
        </el-table-column>
        <el-table-column prop="buy_nav" label="买入净值" width="90" align="center">
          <template #default="{ row }">
            {{ formatNav(row.buy_nav) }}
          </template>
        </el-table-column>
        <el-table-column prop="latest_nav" label="最新净值" width="90" align="center">
          <template #default="{ row }">
            {{ formatNav(row.latest_nav) }}
          </template>
        </el-table-column>
        <el-table-column prop="latest_nav_date" label="净值日期" width="100" align="center">
          <template #default="{ row }">
            {{ formatDate(row.latest_nav_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="holding_return" label="持有收益" width="110" align="center">
          <template #default="{ row }">
            <span :class="getPnlClass(row.holding_return)">
              {{ formatMoney(row.holding_return) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="holding_return_rate" label="持有收益率" width="100" align="center">
          <template #default="{ row }">
            <span :class="getPnlClass(row.holding_return_rate)">
              {{ formatPercent(row.holding_return_rate) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="period_return" label="阶段收益" width="110" align="center">
          <template #default="{ row }">
            <span :class="getPnlClass(row.period_return)">
              {{ row.period_return !== null ? formatMoney(row.period_return) : '--' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { positionAPI } from '@/api/position'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const sortBy = ref('strategy')
const periodRange = ref(null)
const positionData = ref({
  client_info: {},
  positions: [],
  revenue_overview: {},
  grouped_positions: {},
  holding_distribution: [],
  major_strategy_distribution: [],
  sub_strategy_distribution: []
})

// 图表引用
const holdingChartRef = ref()
const majorStrategyChartRef = ref()
const subStrategyChartRef = ref()

// 获取页面标题
const getPageTitle = () => {
  const clientName = positionData.value.client_info?.client_name || '客户'
  const latestUpdate = positionData.value.client_info?.latest_update
  const clientSurname = clientName.split('*')[0] || clientName
  
  if (latestUpdate) {
    return `${clientSurname}总的二级持仓分析（存量时间：${latestUpdate}）`
  }
  return `${clientSurname}总的二级持仓分析`
}

// 加载持仓详情数据
const loadPositionDetail = async () => {
  const groupId = route.params.groupId
  if (!groupId) {
    ElMessage.error('客户ID不能为空')
    return
  }
  
  loading.value = true
  try {
    const startDate = periodRange.value ? periodRange.value[0] : null
    const endDate = periodRange.value ? periodRange.value[1] : null
    const response = await positionAPI.getClientPositionDetail(groupId, null, startDate, endDate)
    positionData.value = response
    
    // 渲染图表
    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('加载持仓详情失败:', error)
    ElMessage.error('加载持仓详情失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}

// 格式化金额显示（去掉小数点，添加千分位分隔符）
const formatChartValue = (value) => {
  const num = Math.round(parseFloat(value))
  return num.toLocaleString('zh-CN')
}

// 定义饼图颜色配置
const chartColors = {
  // 持仓分布 - 蓝紫色系，柔和且专业
  holding: [
    '#5B8FF9', '#5AD8A6', '#5D7092', '#F6BD16', '#E86452',
    '#6DC8EC', '#945FB9', '#FF9845', '#1E9493', '#FF99C3',
    '#BDD2FD', '#BDEFDB', '#C2C8D5', '#FFE0B3', '#FFCCC7'
  ],
  // 大类策略 - 绿蓝色系，清晰区分
  majorStrategy: [
    '#2E8B57', '#4682B4', '#CD853F', '#8B4513', '#4169E1',
    '#228B22', '#6495ED', '#D2691E', '#A0522D', '#1E90FF'
  ],
  // 细分策略 - 暖色系，温和不刺眼
  subStrategy: [
    '#8B7355', '#CD919E', '#8FBC8F', '#DDA0DD', '#F0E68C',
    '#D2B48C', '#DEB887', '#98FB98', '#F5DEB3', '#FFE4E1',
    '#E6E6FA', '#FFF8DC', '#FFEFD5', '#F0F8FF', '#FFFACD'
  ]
}

// 渲染图表
const renderCharts = () => {
  // 持仓分布饼图
  if (holdingChartRef.value && positionData.value.holding_distribution?.length > 0) {
    const chart = echarts.init(holdingChartRef.value)
    const option = {
      color: chartColors.holding,
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const formattedValue = formatChartValue(params.value)
          return `${params.seriesName} <br/>${params.name}: ¥${formattedValue} (${params.percent}%)`
        }
      },
      series: [
        {
          name: '持仓分布',
          type: 'pie',
          radius: ['30%', '80%'],
          center: ['50%', '50%'],
          label: {
            show: true,
            position: 'outside',
            formatter: (params) => {
              const formattedValue = formatChartValue(params.value)
              return `${params.name}\n${params.percent}%\n¥${formattedValue}`
            },
            fontSize: 11,
            color: '#666'
          },
          labelLine: {
            show: true,
            length: 15,
            length2: 10
          },
          data: positionData.value.holding_distribution.map(item => ({
            value: parseFloat(item.total_market_value),
            name: item.strategy_name
          }))
        }
      ]
    }
    chart.setOption(option)
  }
  
  // 大类策略分布饼图
  if (majorStrategyChartRef.value && positionData.value.major_strategy_distribution?.length > 0) {
    const chart = echarts.init(majorStrategyChartRef.value)
    const option = {
      color: chartColors.majorStrategy,
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const formattedValue = formatChartValue(params.value)
          return `${params.seriesName} <br/>${params.name}: ¥${formattedValue} (${params.percent}%)`
        }
      },
      series: [
        {
          name: '大类策略',
          type: 'pie',
          radius: '75%',
          center: ['50%', '50%'],
          label: {
            show: true,
            position: 'outside',
            formatter: (params) => {
              const formattedValue = formatChartValue(params.value)
              return `${params.name}\n${params.percent}%\n¥${formattedValue}`
            },
            fontSize: 12,
            color: '#666'
          },
          labelLine: {
            show: true,
            length: 20,
            length2: 15
          },
          data: positionData.value.major_strategy_distribution.map(item => ({
            value: parseFloat(item.total_market_value),
            name: item.strategy_name
          }))
        }
      ]
    }
    chart.setOption(option)
  }
  
  // 细分策略分布饼图
  if (subStrategyChartRef.value && positionData.value.sub_strategy_distribution?.length > 0) {
    const chart = echarts.init(subStrategyChartRef.value)
    const option = {
      color: chartColors.subStrategy,
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          const formattedValue = formatChartValue(params.value)
          return `${params.seriesName} <br/>${params.name}: ¥${formattedValue} (${params.percent}%)`
        }
      },
      series: [
        {
          name: '细分策略',
          type: 'pie',
          radius: '75%',
          center: ['50%', '50%'],
          label: {
            show: true,
            position: 'outside',
            formatter: (params) => {
              const formattedValue = formatChartValue(params.value)
              return `${params.name}\n${params.percent}%\n¥${formattedValue}`
            },
            fontSize: 12,
            color: '#666'
          },
          labelLine: {
            show: true,
            length: 20,
            length2: 15
          },
          data: positionData.value.sub_strategy_distribution.map(item => ({
            value: parseFloat(item.total_market_value),
            name: item.strategy_name
          }))
        }
      ]
    }
    chart.setOption(option)
  }
}

// 获取分组表格数据（包含小计行）
const getGroupedTableData = () => {
  const positions = [...positionData.value.positions]
  const tableData = []
  
  // 定义策略排序优先级
  const strategyOrder = ['成长配置', '稳健配置', '尾部对冲', '底仓配置']
  
  // 按策略分组
  const groupedPositions = {}
  positions.forEach(pos => {
    const strategy = pos.major_strategy || '未分类'
    if (!groupedPositions[strategy]) {
      groupedPositions[strategy] = []
    }
    groupedPositions[strategy].push({...pos, rowType: 'data'})
  })
  
  // 按策略顺序排列
  strategyOrder.forEach(strategy => {
    if (groupedPositions[strategy]) {
      // 添加策略分组头
      tableData.push({
        fund_name: strategy,
        rowType: 'header'
      })
      
      // 添加该策略下的持仓
      const groupPositions = groupedPositions[strategy]
      tableData.push(...groupPositions)
      
      // 计算该策略小计
      const subtotal = calculateGroupSubtotal(groupPositions)
      tableData.push({
        fund_name: `${strategy}小计`,
        cost_with_fee: subtotal.totalCost,
        holding_return: subtotal.totalReturn,
        holding_return_rate: subtotal.returnRate,
        period_return: subtotal.totalPeriodReturn,
        rowType: 'summary'
      })
    }
  })
  
  // 添加总计行
  const grandTotal = calculateGrandTotal(positions)
  tableData.push({
    fund_name: '合计',
    cost_with_fee: grandTotal.totalCost,
    holding_return: grandTotal.totalReturn,
    holding_return_rate: grandTotal.returnRate,
    period_return: grandTotal.totalPeriodReturn,
    rowType: 'total'
  })
  
  return tableData
}

// 计算分组小计
const calculateGroupSubtotal = (positions) => {
  let totalCost = 0
  let totalReturn = 0
  let totalPeriodReturn = 0
  
  positions.forEach(pos => {
    if (pos.cost_with_fee) totalCost += parseFloat(pos.cost_with_fee)
    if (pos.holding_return) totalReturn += parseFloat(pos.holding_return)
    if (pos.period_return) totalPeriodReturn += parseFloat(pos.period_return)
  })
  
  const returnRate = totalCost > 0 ? (totalReturn / totalCost) * 100 : 0
  
  return {
    totalCost,
    totalReturn,
    returnRate,
    totalPeriodReturn
  }
}

// 计算总计
const calculateGrandTotal = (positions) => {
  let totalCost = 0
  let totalReturn = 0
  let totalPeriodReturn = 0
  
  positions.forEach(pos => {
    if (pos.cost_with_fee) totalCost += parseFloat(pos.cost_with_fee)
    if (pos.holding_return) totalReturn += parseFloat(pos.holding_return)
    if (pos.period_return) totalPeriodReturn += parseFloat(pos.period_return)
  })
  
  const returnRate = totalCost > 0 ? (totalReturn / totalCost) * 100 : 0
  
  return {
    totalCost,
    totalReturn,
    returnRate,
    totalPeriodReturn
  }
}

// 获取行样式类名
const getRowClassName = ({ row }) => {
  if (row.rowType === 'header') return 'group-header-row'
  if (row.rowType === 'summary') return 'group-summary-row'
  if (row.rowType === 'total') return 'grand-total-row'
  return ''
}

// 获取排序后的持仓列表
const getSortedPositions = () => {
  const positions = [...positionData.value.positions]
  
  if (sortBy.value === 'date') {
    return positions.sort((a, b) => new Date(a.first_buy_date) - new Date(b.first_buy_date))
  } else if (sortBy.value === 'value') {
    return positions.sort((a, b) => (b.current_market_value || 0) - (a.current_market_value || 0))
  }
  
  return positions
}

// 排序表格
const sortTable = () => {
  // 重新渲染表格
}

// 处理阶段收益时间范围变化
const handlePeriodChange = () => {
  loadPositionDetail()
}

// 刷新数据
const refreshData = () => {
  loadPositionDetail()
}

// 返回列表
const goBack = () => {
  router.push('/position')
}

// 格式化函数
const formatMoney = (amount) => {
  if (amount == null || amount === '') return '--'
  const num = parseFloat(amount)
  return '¥' + num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatShares = (shares) => {
  if (shares == null || shares === '') return '--'
  const num = parseFloat(shares)
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 6
  })
}

const formatNav = (nav) => {
  if (nav == null || nav === '') return '--'
  const num = parseFloat(nav)
  return num.toFixed(4)
}

const formatPercent = (ratio) => {
  if (ratio == null || ratio === '') return '--'
  const num = parseFloat(ratio)
  return num.toFixed(2) + '%'
}

const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleDateString('zh-CN')
}

const getPnlColor = (value) => {
  if (value == null || value === '') return '#909399'
  const num = parseFloat(value)
  return num >= 0 ? '#f56c6c' : '#67c23a'  // 正收益红色，负收益绿色
}

const getPnlClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  return num >= 0 ? 'profit-text' : 'loss-text'
}

// 生命周期
onMounted(() => {
  loadPositionDetail()
})
</script>

<style scoped>
.position-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  color: #303133;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.revenue-overview {
  margin-bottom: 24px;
}

.overview-card {
  text-align: center;
  transition: all 0.3s;
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.charts-section {
  margin-bottom: 24px;
}

.chart-card {
  height: 400px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.position-table-card {
  margin-bottom: 24px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.period-filter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-right: 16px;
}

.period-filter span {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.strategy-group {
  margin-bottom: 24px;
}

.strategy-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.strategy-group-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.group-summary {
  color: #909399;
  font-size: 14px;
}

.position-table {
  margin-bottom: 16px;
}

/* 表格行样式 */
:deep(.group-header-row) {
  background-color: #e8f4fd !important;
  font-weight: 600;
  color: #1890ff;
}

:deep(.group-summary-row) {
  background-color: #f7f7f7 !important;
  font-weight: 600;
  color: #666;
}

:deep(.grand-total-row) {
  background-color: #fff2e8 !important;
  font-weight: 700;
  color: #fa8c16;
  border-top: 2px solid #fa8c16;
}

/* QD标识样式 */
.strategy-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  position: relative;
}

.qd-tag {
  position: absolute;
  top: -6px;
  right: -6px;
  font-size: 8px;
  padding: 1px 3px;
  line-height: 1;
  border-radius: 2px;
  transform: scale(0.8);
}

/* 小计样式 */
.summary-text {
  font-weight: 600;
  color: #666;
}

/* 收益颜色样式 */
.profit-text {
  color: #f56c6c;  /* 正收益红色 */
  font-weight: 500;
}

.loss-text {
  color: #67c23a;  /* 负收益绿色 */
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-section .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .position-detail {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .revenue-overview .el-col {
    margin-bottom: 12px;
  }
  
  .charts-section .el-col {
    margin-bottom: 16px;
  }
  
  .strategy-group-header {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}
</style>