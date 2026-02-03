<template>
  <div class="summary-analysis-container">
    <!-- 分析维度标签页 -->
    <el-tabs v-model="activeAnalysisTab" type="border-card">
      <!-- 月度超额分析 -->
      <el-tab-pane label="月度超额" name="monthly">
        <div class="analysis-header">
          <el-select v-model="selectedYear" placeholder="选择年份" @change="handleYearChange" style="width: 120px">
            <el-option v-for="year in yearOptions" :key="year" :label="`${year}年`" :value="year" />
          </el-select>
          <span class="analysis-subtitle">月度超额收益分析（单位：%）</span>
          <el-button type="primary" @click="handleCalculateMonthly" style="margin-left: auto">
            <el-icon><DataAnalysis /></el-icon>
            计算超额
          </el-button>
        </div>

        <!-- 按产品类型分组展示 -->
        <div v-for="(group, groupName) in groupedMonthlyData.groups" :key="groupName" class="product-group">
          <div class="group-header">
            <span>{{ getGroupDisplayName(groupName, groupedMonthlyData.trackingIndex[groupName]) }}</span>
            <el-button
              type="primary"
              size="small"
              @click="showGroupChart(groupName, group, groupedMonthlyData.trackingIndex[groupName])"
            >
              <el-icon><TrendCharts /></el-icon>
              查看超额曲线
            </el-button>
          </div>
          <el-table
            :data="group"
            v-loading="loading && groupName === Object.keys(groupedMonthlyData.groups)[0]"
            stripe
            :cell-class-name="getCellClassName"
          >
            <el-table-column prop="displayName" label="产品名称" min-width="200" fixed />

            <el-table-column
              v-for="month in 12"
              :key="month"
              :prop="`month${month}`"
              :label="`${month}月`"
              min-width="80"
              align="center"
            >
              <template #default="{ row }">
                <span :class="getValueClass(row[`month${month}`])">
                  {{ formatPercent(row[`month${month}`]) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="yearTotal" label="年度累计" min-width="100" align="center" fixed="right">
              <template #default="{ row }">
                <span :class="getValueClass(row.yearTotal)" style="font-weight: bold">
                  {{ formatPercent(row.yearTotal) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="winRate" label="胜率" min-width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.winRate"
                  :color="getWinRateColor(row.winRate)"
                  :stroke-width="6"
                  :show-text="false"
                />
                <div style="font-size: 12px; margin-top: 2px">{{ row.winRate }}%</div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 年度超额分析 -->
      <el-tab-pane label="年度超额" name="yearly">
        <div class="analysis-header">
          <span class="analysis-subtitle">年度超额收益对比（单位：%）</span>
          <el-button type="primary" @click="handleCalculateYearly" style="margin-left: auto">
            <el-icon><DataAnalysis /></el-icon>
            计算超额
          </el-button>
        </div>

        <!-- 按产品类型分组展示 -->
        <div v-for="(group, groupName) in groupedYearlyData.groups" :key="groupName" class="product-group">
          <div class="group-header">
            {{ getGroupDisplayName(groupName, groupedYearlyData.trackingIndex[groupName]) }}
          </div>
          <el-table
            :data="group"
            v-loading="loading && groupName === Object.keys(groupedYearlyData.groups)[0]"
            stripe
            :cell-class-name="getCellClassName"
          >
            <el-table-column prop="displayName" label="产品名称" min-width="200" fixed />

            <el-table-column
              v-for="year in yearColumns"
              :key="year"
              :prop="`year${year}`"
              :label="`${year}年`"
              min-width="100"
              align="center"
            >
              <template #default="{ row }">
                <span :class="getValueClass(row[`year${year}`])">
                  {{ formatPercent(row[`year${year}`]) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column prop="avgExcess" label="平均超额" min-width="100" align="center" fixed="right">
              <template #default="{ row }">
                <span :class="getValueClass(row.avgExcess)" style="font-weight: bold">
                  {{ formatPercent(row.avgExcess) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 区间超额分析 -->
      <el-tab-pane label="区间超额" name="period">
        <div class="analysis-header">
          <el-date-picker
            v-model="customDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 280px; margin-right: 10px"
          />
          <el-button type="primary" @click="handleCalculatePeriod">
            <el-icon><DataAnalysis /></el-icon>
            计算区间超额
          </el-button>
          <span class="analysis-subtitle" style="margin-left: 20px">区间超额收益分析</span>
        </div>

        <!-- 按产品类型分组展示 -->
        <div v-for="(group, groupName) in groupedPeriodData.groups" :key="groupName" class="product-group">
          <div class="group-header">
            {{ getGroupDisplayName(groupName, groupedPeriodData.trackingIndex[groupName]) }}
          </div>
          <el-table
            :data="group"
            v-loading="loading && groupName === Object.keys(groupedPeriodData.groups)[0]"
            stripe
            :cell-class-name="getCellClassName"
          >
            <el-table-column prop="displayName" label="产品名称" min-width="200" fixed />

            <!-- 区间表现 -->
            <el-table-column
              :label="`区间表现${customDateRange && customDateRange.length === 2 ? '（' + formatDateRange(customDateRange[0], customDateRange[1]) + '）' : ''}`"
              align="center"
            >
              <el-table-column prop="period.productReturn" label="产品收益" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.period?.productReturn)">
                    {{ formatPercent(row.period?.productReturn) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="period.indexReturn" label="指数表现" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.period?.indexReturn)">
                    {{ formatPercent(row.period?.indexReturn) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="period.excessReturn" label="超额情况" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.period?.excessReturn)" style="font-weight: bold">
                    {{ formatPercent(row.period?.excessReturn) }}
                  </span>
                </template>
              </el-table-column>
            </el-table-column>

            <!-- 今年以来 -->
            <el-table-column
              label="今年以来"
              align="center"
            >
              <el-table-column prop="ytd.productReturn" label="产品收益" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.ytd?.productReturn)">
                    {{ formatPercent(row.ytd?.productReturn) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="ytd.indexReturn" label="指数表现" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.ytd?.indexReturn)">
                    {{ formatPercent(row.ytd?.indexReturn) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="ytd.excessReturn" label="超额情况" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.ytd?.excessReturn)" style="font-weight: bold">
                    {{ formatPercent(row.ytd?.excessReturn) }}
                  </span>
                </template>
              </el-table-column>
            </el-table-column>

            <!-- 近3个月 -->
            <el-table-column label="近3个月" align="center">
              <el-table-column prop="recent3m.productReturn" label="产品收益" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.recent3m?.productReturn)">
                    {{ formatPercent(row.recent3m?.productReturn) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="recent3m.indexReturn" label="指数表现" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.recent3m?.indexReturn)">
                    {{ formatPercent(row.recent3m?.indexReturn) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="recent3m.excessReturn" label="超额情况" min-width="100" align="center">
                <template #default="{ row }">
                  <span :class="getValueClass(row.recent3m?.excessReturn)" style="font-weight: bold">
                    {{ formatPercent(row.recent3m?.excessReturn) }}
                  </span>
                </template>
              </el-table-column>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 超额曲线弹窗 -->
    <el-dialog
      v-model="chartDialogVisible"
      :title="chartDialogTitle"
      width="90%"
      top="2vh"
    >
      <div v-loading="chartLoading" class="chart-dialog-content">
        <!-- 图表类型切换按钮 -->
        <div class="chart-type-selector">
          <el-radio-group v-model="activeChartType" size="default">
            <el-radio-button label="nav">净值曲线对比</el-radio-button>
            <el-radio-button label="excess">累计超额收益曲线</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 净值曲线图 -->
        <div v-show="activeChartType === 'nav'" class="chart-section">
          <div ref="groupNavChartRef" class="group-chart"></div>
        </div>

        <!-- 超额曲线图 -->
        <div v-show="activeChartType === 'excess'" class="chart-section">
          <div ref="groupExcessChartRef" class="group-chart"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, TrendCharts } from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { fetchMultipleBenchmarks } from '@/utils/benchmarkData'

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000'

// 数据
const loading = ref(false)
const activeAnalysisTab = ref('monthly')
const selectedYear = ref(new Date().getFullYear())
const customDateRange = ref([])

// 数据表
const monthlyExcessData = ref([])
const yearlyExcessData = ref([])
const periodExcessData = ref([])

// 图表弹窗相关
const chartDialogVisible = ref(false)
const chartDialogTitle = ref('')
const chartLoading = ref(false)
const activeChartType = ref('nav')  // 默认显示净值曲线
const groupNavChartRef = ref(null)
const groupExcessChartRef = ref(null)
let groupNavChart = null
let groupExcessChart = null

// 指数代码映射到中文名称
const indexNameMap = {
  '000905.SH': '中证500',
  '000300.SH': '沪深300',
  '000852.SH': '中证1000',
  '000510.SH': '中证A500',
  '000906.SH': '中证800',
  '932000.CSI': '中证2000'
}

// 产品类型分组
const groupedMonthlyData = computed(() => {
  return groupByProductType(monthlyExcessData.value)
})

const groupedYearlyData = computed(() => {
  return groupByProductType(yearlyExcessData.value)
})

const groupedPeriodData = computed(() => {
  return groupByProductType(periodExcessData.value)
})

// 最新净值日期（从后端API获取）
const latestNavDateFull = ref('')

// 获取最新净值日期（用于表头显示，格式：YYYYMMDD）
const latestNavDate = computed(() => {
  if (!latestNavDateFull.value) {
    return ''
  }
  return latestNavDateFull.value.replace(/-/g, '')
})

// 从API获取最新净值日期
const fetchLatestNavDate = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/quantitative/latest-nav-date`)
    latestNavDateFull.value = response.data.latestNavDate || ''
  } catch (error) {
    console.error('获取最新净值日期失败:', error)
  }
}

// 格式化日期范围显示（如：1128-1205）
const formatDateRange = (startDate, endDate) => {
  if (!startDate || !endDate) return ''
  const start = startDate.replace(/-/g, '').substring(4) // 取MMDD
  const end = endDate.replace(/-/g, '').substring(4)
  return `${start}-${end}`
}

// 按产品类型分组
const groupByProductType = (data) => {
  const groups = {}
  const groupTrackingIndex = {} // 存储每个组别的跟踪指数
  const typeOrder = ['300指增', '500指增', 'A500指增', '1000指增', '小市值', '量化选股', '其他']

  data.forEach(item => {
    const type = item.productType || '其他'
    if (!groups[type]) {
      groups[type] = []
      // 记录该组别的跟踪指数（取第一个产品的跟踪指数）
      if (item.trackingIndex) {
        groupTrackingIndex[type] = item.trackingIndex
      }
    }
    groups[type].push(item)
  })

  // 按照预定义顺序排序
  const sortedGroups = {}
  typeOrder.forEach(type => {
    if (groups[type]) {
      sortedGroups[type] = groups[type]
    }
  })

  return { groups: sortedGroups, trackingIndex: groupTrackingIndex }
}

// 获取组别显示名称(包含跟踪指数)
const getGroupDisplayName = (groupType, trackingIndexCode) => {
  if (!trackingIndexCode) {
    return groupType
  }
  const indexName = indexNameMap[trackingIndexCode]
  if (indexName) {
    return `${groupType}（跟踪指数：${indexName}）`
  }
  return groupType
}

// 年份选项
const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= 2020; i--) {
    years.push(i)
  }
  return years
})

// 年度列
const yearColumns = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = 2020; i <= currentYear; i++) {
    years.push(i)
  }
  return years
})

// 格式化百分比
const formatPercent = (value) => {
  if (value === null || value === undefined) return '--'
  return value.toFixed(2)
}

// 获取值的样式类（红涨绿跌）
const getValueClass = (value) => {
  if (value === null || value === undefined) return ''
  return value > 0 ? 'profit-text' : value < 0 ? 'loss-text' : ''
}

// 获取单元格样式
const getCellClassName = ({ row, column }) => {
  if (!column.property) return ''
  if (!column.property.includes('month') && !column.property.includes('year')) return ''
  const value = row[column.property]
  if (value === null || value === undefined) return ''
  return value > 0 ? 'positive-cell' : value < 0 ? 'negative-cell' : ''
}

// 获取胜率颜色
const getWinRateColor = (rate) => {
  if (rate >= 70) return '#67C23A'
  if (rate >= 50) return '#E6A23C'
  return '#F56C6C'
}

// 计算月度超额收益
const handleCalculateMonthly = async () => {
  loading.value = true

  try {
    // 先获取所有需要的指数数据
    ElMessage.info('正在获取指数数据...')
    const indexCodes = ['000905.SH', '000300.SH', '000906.SH', '000510.SH', '000852.SH', '932000.CSI']
    const indexDataMap = await fetchMultipleBenchmarks(indexCodes)

    // 从localStorage读取产品配置
    const productConfigs = localStorage.getItem('quantProductConfigs')
    const configs = productConfigs ? JSON.parse(productConfigs) : {}

    // 调用计算API，传入指数数据和产品配置
    const response = await axios.post(`${API_BASE}/api/quantitative/calculate-monthly-excess`, {
      year: selectedYear.value,
      indexDataMap: indexDataMap,
      productConfigs: configs
    })

    monthlyExcessData.value = response.data

    // 保存计算结果到localStorage
    const cacheKey = `monthlyExcessCache_${selectedYear.value}`
    const cacheData = {
      data: response.data,
      timestamp: new Date().toISOString(),
      year: selectedYear.value
    }
    localStorage.setItem(cacheKey, JSON.stringify(cacheData))

    ElMessage.success('月度超额收益计算完成')
  } catch (error) {
    ElMessage.error('计算失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 计算年度超额收益
const handleCalculateYearly = async () => {
  loading.value = true

  try {
    // 先获取所有需要的指数数据
    ElMessage.info('正在获取指数数据...')
    const indexCodes = ['000905.SH', '000300.SH', '000906.SH', '000510.SH', '000852.SH', '932000.CSI']
    const indexDataMap = await fetchMultipleBenchmarks(indexCodes)

    // 从localStorage读取产品配置
    const productConfigs = localStorage.getItem('quantProductConfigs')
    const configs = productConfigs ? JSON.parse(productConfigs) : {}

    // 调用计算API，传入指数数据和产品配置
    const response = await axios.post(`${API_BASE}/api/quantitative/calculate-yearly-excess`, {
      startYear: 2020,
      endYear: new Date().getFullYear(),
      indexDataMap: indexDataMap,
      productConfigs: configs
    })

    yearlyExcessData.value = response.data

    // 保存计算结果到localStorage
    const cacheData = {
      data: response.data,
      timestamp: new Date().toISOString()
    }
    localStorage.setItem('yearlyExcessCache', JSON.stringify(cacheData))

    ElMessage.success('年度超额收益计算完成')
  } catch (error) {
    ElMessage.error('计算失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 计算区间超额收益
const handleCalculatePeriod = async () => {
  if (!customDateRange.value || customDateRange.value.length !== 2) {
    ElMessage.warning('请选择日期区间')
    return
  }

  loading.value = true

  try {
    // 获取最新净值日期
    await fetchLatestNavDate()
    if (!latestNavDateFull.value) {
      ElMessage.error('无法获取最新净值日期')
      return
    }

    // 先获取所有需要的指数数据
    ElMessage.info('正在获取指数数据...')
    const indexCodes = ['000905.SH', '000300.SH', '000906.SH', '000510.SH', '000852.SH', '932000.CSI']
    const indexDataMap = await fetchMultipleBenchmarks(indexCodes)

    // 从localStorage读取产品配置
    const productConfigs = localStorage.getItem('quantProductConfigs')
    const configs = productConfigs ? JSON.parse(productConfigs) : {}

    // 计算三个时间段（使用最新净值日期而不是today）
    const latestNavDay = latestNavDateFull.value // 格式：YYYY-MM-DD
    const currentYear = new Date(latestNavDay).getFullYear()

    // 1. 自定义区间
    const customStart = customDateRange.value[0]
    const customEnd = customDateRange.value[1]

    // 2. 今年以来 (YTD) - 使用最新净值日期
    const ytdStart = `${currentYear}-01-01`
    const ytdEnd = latestNavDay

    // 3. 近3个月 - 使用最新净值日期
    const recent3mEnd = latestNavDay
    const recent3mStartDate = new Date(latestNavDay)
    recent3mStartDate.setMonth(recent3mStartDate.getMonth() - 3)
    const recent3mStart = recent3mStartDate.toISOString().split('T')[0]

    // 并发请求三个时间段的数据
    const [customData, ytdData, recent3mData] = await Promise.all([
      axios.post(`${API_BASE}/api/quantitative/calculate-period-excess`, {
        startDate: customStart,
        endDate: customEnd,
        indexDataMap: indexDataMap,
        productConfigs: configs
      }),
      axios.post(`${API_BASE}/api/quantitative/calculate-period-excess`, {
        startDate: ytdStart,
        endDate: ytdEnd,
        indexDataMap: indexDataMap,
        productConfigs: configs
      }),
      axios.post(`${API_BASE}/api/quantitative/calculate-period-excess`, {
        startDate: recent3mStart,
        endDate: recent3mEnd,
        indexDataMap: indexDataMap,
        productConfigs: configs
      })
    ])

    // 合并数据
    const customResults = customData.data
    const ytdResults = ytdData.data
    const recent3mResults = recent3mData.data

    // 创建产品映射
    const productMap = {}

    customResults.forEach(item => {
      if (!productMap[item.fundCode]) {
        productMap[item.fundCode] = {
          fundCode: item.fundCode,
          productName: item.productName,
          displayName: item.displayName,
          productType: item.productType,
          trackingIndex: item.trackingIndex,
          period: null,
          ytd: null,
          recent3m: null
        }
      }
      productMap[item.fundCode].period = {
        productReturn: item.productReturn,
        indexReturn: item.indexReturn,
        excessReturn: item.excessReturn
      }
    })

    ytdResults.forEach(item => {
      if (!productMap[item.fundCode]) {
        productMap[item.fundCode] = {
          fundCode: item.fundCode,
          productName: item.productName,
          displayName: item.displayName,
          productType: item.productType,
          trackingIndex: item.trackingIndex,
          period: null,
          ytd: null,
          recent3m: null
        }
      }
      productMap[item.fundCode].ytd = {
        productReturn: item.productReturn,
        indexReturn: item.indexReturn,
        excessReturn: item.excessReturn
      }
    })

    recent3mResults.forEach(item => {
      if (!productMap[item.fundCode]) {
        productMap[item.fundCode] = {
          fundCode: item.fundCode,
          productName: item.productName,
          displayName: item.displayName,
          productType: item.productType,
          trackingIndex: item.trackingIndex,
          period: null,
          ytd: null,
          recent3m: null
        }
      }
      productMap[item.fundCode].recent3m = {
        productReturn: item.productReturn,
        indexReturn: item.indexReturn,
        excessReturn: item.excessReturn
      }
    })

    periodExcessData.value = Object.values(productMap)

    // 保存计算结果到localStorage（key包含日期范围）
    const dateKey = `${customDateRange.value[0]}_${customDateRange.value[1]}`
    const cacheKey = `periodExcessCache_${dateKey}`
    const cacheData = {
      data: Object.values(productMap),
      timestamp: new Date().toISOString(),
      dateRange: customDateRange.value
    }
    localStorage.setItem(cacheKey, JSON.stringify(cacheData))

    ElMessage.success('区间超额收益计算完成')
  } catch (error) {
    ElMessage.error('计算失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 处理年份变更
const handleYearChange = () => {
  // 切换年份时，尝试加载该年份的缓存数据
  const monthlyCacheKey = `monthlyExcessCache_${selectedYear.value}`
  const monthlyCache = localStorage.getItem(monthlyCacheKey)

  if (monthlyCache) {
    try {
      const cached = JSON.parse(monthlyCache)
      monthlyExcessData.value = cached.data || []
      console.log(`已加载${selectedYear.value}年度超额缓存数据 (${cached.timestamp})`)
    } catch (e) {
      console.error('加载月度超额缓存失败:', e)
      monthlyExcessData.value = []
    }
  } else {
    // 如果没有缓存，清空数据并提示用户计算
    monthlyExcessData.value = []
    ElMessage.info('年份已更改，请点击"计算超额"重新计算')
  }
}

// 显示分组图表
const showGroupChart = async (groupName, groupProducts, trackingIndexCode) => {
  chartDialogTitle.value = `${groupName} - 超额曲线分析（跟踪指数：${indexNameMap[trackingIndexCode] || trackingIndexCode}）`
  chartDialogVisible.value = true
  chartLoading.value = true
  activeChartType.value = 'nav'  // 重置为净值曲线

  try {
    // 获取该组所有产品的净值数据
    const fundCodes = groupProducts.map(p => p.fundCode)

    // 获取净值数据（使用复权累计净值）
    const navPromises = fundCodes.map(code =>
      axios.get(`${API_BASE}/api/nav/fund/${code}/with-adjusted-nav`, {
        params: {
          limit: 10000
        }
      })
    )
    const navResponses = await Promise.all(navPromises)

    // 提取复权累计净值数据
    const navDataArrays = navResponses.map((response, idx) => {
      if (response.data && response.data.data && response.data.data.nav_records) {
        // 使用复权累计净值：adjusted_accum_nav
        const navData = response.data.data.nav_records.map(record => ({
          date: record.nav_date,
          value: parseFloat(record.adjusted_accum_nav)
        }))
        // 按日期升序排序（从早到晚）
        return navData.sort((a, b) => a.date.localeCompare(b.date))
      }
      return []
    })

    // 获取指数数据
    const indexCodes = [trackingIndexCode]
    const indexDataMap = await fetchMultipleBenchmarks(indexCodes)
    const indexData = indexDataMap[trackingIndexCode] || []

    // 调用后端API获取周度累计超额曲线数据
    console.log('开始获取周度超额曲线数据...')
    const excessDataPromises = groupProducts.map(product => {
      // 确定时间范围（使用该产品的净值数据范围）
      const navData = navDataArrays[groupProducts.indexOf(product)]
      if (!navData || navData.length === 0) {
        return Promise.resolve([])
      }

      const startDate = navData[0].date
      const endDate = navData[navData.length - 1].date

      // 调用后端API获取周度超额曲线
      return axios.post(`${API_BASE}/api/quantitative/weekly-excess-curve`, {
        fundCode: product.fundCode,
        startDate: startDate,
        endDate: endDate,
        indexCode: trackingIndexCode,
        indexDataMap: { [trackingIndexCode]: indexData }
      }).then(response => {
        console.log(`${product.displayName} 周度超额数据:`, response.data)
        return response.data
      }).catch(error => {
        console.error(`获取 ${product.displayName} 周度超额数据失败:`, error)
        return []
      })
    })

    const excessDataArrays = await Promise.all(excessDataPromises)
    console.log('周度超额曲线数据获取完成', excessDataArrays)

    // 等待DOM更新
    await nextTick()

    // 绘制图表
    drawGroupCharts(groupProducts, navDataArrays, indexData, trackingIndexCode, excessDataArrays)
  } catch (error) {
    console.error('加载图表数据详细错误:', error)
    ElMessage.error('加载图表数据失败：' + error.message)
  } finally {
    chartLoading.value = false
  }
}

// 绘制分组图表
const drawGroupCharts = (products, navDataArrays, indexData, trackingIndexCode, excessDataArrays) => {
  // 初始化图表
  if (groupNavChart) groupNavChart.dispose()
  if (groupExcessChart) groupExcessChart.dispose()

  groupNavChart = echarts.init(groupNavChartRef.value)
  groupExcessChart = echarts.init(groupExcessChartRef.value)

  // 准备数据
  const productNavSeries = []
  const productExcessSeries = []
  const productColors = ['#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4']

  // ==================== 净值曲线部分 ====================
  // 找到所有净值日期的并集
  const allNavDates = new Set()
  navDataArrays.forEach((navData) => {
    navData.forEach(item => allNavDates.add(item.date))
  })
  indexData.forEach(item => allNavDates.add(item.date))

  const sortedNavDates = Array.from(allNavDates).sort()

  // 处理每个产品的净值数据
  products.forEach((product, index) => {
    const navData = navDataArrays[index]

    if (!navData || navData.length === 0) {
      return
    }

    // 创建日期到净值的映射
    const navMap = {}
    navData.forEach(item => {
      navMap[item.date] = item.value
    })

    // 创建日期到指数的映射
    const indexMap = {}
    indexData.forEach(item => {
      indexMap[item.date] = item.value
    })

    // 归一化起点
    const firstDate = sortedNavDates.find(date => navMap[date] && indexMap[date])
    if (!firstDate) {
      return
    }

    const startNav = navMap[firstDate]
    const startIndex = indexMap[firstDate]

    // 计算归一化净值
    const normalizedNavValues = []

    sortedNavDates.forEach(date => {
      if (navMap[date] && indexMap[date]) {
        normalizedNavValues.push(navMap[date])
      } else {
        normalizedNavValues.push(null)
      }
    })

    // 添加产品净值曲线
    productNavSeries.push({
      name: product.displayName || product.productName,
      type: 'line',
      data: normalizedNavValues,
      smooth: true,
      connectNulls: true,
      lineStyle: { width: 2, color: productColors[index % productColors.length] },
      showSymbol: false
    })
  })

  // ==================== 超额曲线部分 ====================
  // 找到超额数据的所有日期
  const allExcessDates = new Set()
  excessDataArrays.forEach((excessData) => {
    if (excessData && excessData.length > 0) {
      excessData.forEach(item => allExcessDates.add(item.date))
    }
  })

  const sortedExcessDates = Array.from(allExcessDates).sort()

  // 处理每个产品的超额数据
  products.forEach((product, index) => {
    const excessData = excessDataArrays[index]

    if (!excessData || excessData.length === 0) {
      return
    }

    // 创建日期到超额的映射
    const excessMap = {}
    excessData.forEach(item => {
      excessMap[item.date] = item.cumExcessReturn
    })

    // 使用统一的时间轴
    const excessValues = sortedExcessDates.map(date => {
      if (excessMap[date] !== undefined) {
        return excessMap[date]
      }
      return null
    })

    productExcessSeries.push({
      name: product.displayName || product.productName,
      type: 'line',
      data: excessValues,
      smooth: true,
      connectNulls: true,
      lineStyle: { width: 2, color: productColors[index % productColors.length] },
      showSymbol: false
    })
  })

  // 添加归一化的指数曲线
  if (indexData.length > 0) {
    const indexMap = {}
    indexData.forEach(item => {
      indexMap[item.date] = item.value
    })

    const firstDate = sortedNavDates.find(date => indexMap[date])
    if (firstDate) {
      const startIndex = indexMap[firstDate]

      // 找到第一个有效的产品净值作为归一化起点
      let startNav = 1
      for (const navData of navDataArrays) {
        const firstNav = navData.find(n => n.date === firstDate)
        if (firstNav) {
          startNav = firstNav.value
          break
        }
      }

      const normalizedIndexValues = sortedNavDates.map(date => {
        if (indexMap[date]) {
          return (indexMap[date] / startIndex) * startNav
        }
        return null
      })

      productNavSeries.push({
        name: `${indexNameMap[trackingIndexCode] || trackingIndexCode}（归一）`,
        type: 'line',
        data: normalizedIndexValues,
        smooth: true,
        connectNulls: true,
        lineStyle: { width: 2.5, color: '#606266' },
        showSymbol: false,
        emphasis: {
          lineStyle: { width: 3 }
        }
      })
    }
  }


  // 净值曲线图配置
  const navOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: productNavSeries.map(s => s.name),
      top: 10,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '50px',
      top: '60px',
      containLabel: true
    },
    dataZoom: [
      {
        type: 'slider',
        show: true,
        xAxisIndex: [0],
        start: 0,
        end: 100,
        height: 20,
        bottom: 5,
        borderColor: '#ddd',
        fillerColor: 'rgba(64, 158, 255, 0.15)',
        handleStyle: {
          color: '#409EFF',
          borderColor: '#409EFF'
        },
        moveHandleStyle: {
          color: '#409EFF'
        },
        textStyle: {
          color: '#606266'
        }
      },
      {
        type: 'inside',  // 内置缩放（鼠标滚轮）
        xAxisIndex: [0],
        start: 0,
        end: 100
      }
    ],
    xAxis: {
      type: 'category',
      data: sortedNavDates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '净值'
    },
    series: productNavSeries
  }

  // 超额曲线图配置
  const excessOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: function(params) {
        if (params.length === 0) return ''
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          if (param.value !== null && param.value !== undefined) {
            result += `${param.marker}${param.seriesName}: ${parseFloat(param.value).toFixed(2)}%<br/>`
          }
        })
        return result
      }
    },
    legend: {
      data: productExcessSeries.map(s => s.name),
      top: 10,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '50px',
      top: '60px',
      containLabel: true
    },
    dataZoom: [
      {
        type: 'slider',
        show: true,
        xAxisIndex: [0],
        start: 0,
        end: 100,
        height: 20,
        bottom: 5,
        borderColor: '#ddd',
        fillerColor: 'rgba(64, 158, 255, 0.15)',
        handleStyle: {
          color: '#409EFF',
          borderColor: '#409EFF'
        },
        moveHandleStyle: {
          color: '#409EFF'
        },
        textStyle: {
          color: '#606266'
        }
      },
      {
        type: 'inside',
        xAxisIndex: [0],
        start: 0,
        end: 100
      }
    ],
    xAxis: {
      type: 'category',
      data: sortedExcessDates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '累计超额收益 (%)',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: productExcessSeries
  }

  // 设置图表
  groupNavChart.setOption(navOption)
  groupExcessChart.setOption(excessOption)
}

// 监听图表类型切换，重新调整图表大小
watch(activeChartType, async (newType) => {
  await nextTick()
  if (newType === 'nav' && groupNavChart) {
    groupNavChart.resize()
  } else if (newType === 'excess' && groupExcessChart) {
    groupExcessChart.resize()
  }
})

// 计算上上周五到上周五的日期范围
const getLastTwoFridays = () => {
  const today = new Date()
  const dayOfWeek = today.getDay() // 0=周日, 5=周五

  // 计算距离今天最近的上周五（不包括今天）
  let daysToLastFriday
  if (dayOfWeek === 5) {
    // 如果今天是周五，上周五是7天前
    daysToLastFriday = 7
  } else if (dayOfWeek < 5) {
    // 如果今天是周一到周四，上周五是 (dayOfWeek + 2) 天前
    daysToLastFriday = dayOfWeek + 2
  } else {
    // 如果今天是周六(6)或周日(0)，上周五是 (dayOfWeek - 5) 天前
    daysToLastFriday = dayOfWeek === 6 ? 1 : 2
  }

  const lastFriday = new Date(today)
  lastFriday.setDate(today.getDate() - daysToLastFriday)

  // 上上周五是上周五的7天前
  const lastLastFriday = new Date(lastFriday)
  lastLastFriday.setDate(lastFriday.getDate() - 7)

  // 格式化为 YYYY-MM-DD
  const formatDate = (date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  return [formatDate(lastLastFriday), formatDate(lastFriday)]
}

// 加载缓存的计算结果
const loadCachedResults = () => {
  // 加载月度超额缓存
  const monthlyCacheKey = `monthlyExcessCache_${selectedYear.value}`
  const monthlyCache = localStorage.getItem(monthlyCacheKey)
  if (monthlyCache) {
    try {
      const cached = JSON.parse(monthlyCache)
      monthlyExcessData.value = cached.data || []
      console.log(`已加载月度超额缓存数据 (${cached.timestamp})`)
    } catch (e) {
      console.error('加载月度超额缓存失败:', e)
    }
  }

  // 加载年度超额缓存
  const yearlyCache = localStorage.getItem('yearlyExcessCache')
  if (yearlyCache) {
    try {
      const cached = JSON.parse(yearlyCache)
      yearlyExcessData.value = cached.data || []
      console.log(`已加载年度超额缓存数据 (${cached.timestamp})`)
    } catch (e) {
      console.error('加载年度超额缓存失败:', e)
    }
  }

  // 加载区间超额缓存（基于日期范围）
  if (customDateRange.value && customDateRange.value.length === 2) {
    const dateKey = `${customDateRange.value[0]}_${customDateRange.value[1]}`
    const cacheKey = `periodExcessCache_${dateKey}`
    const periodCache = localStorage.getItem(cacheKey)
    if (periodCache) {
      try {
        const cached = JSON.parse(periodCache)
        periodExcessData.value = cached.data || []
        console.log(`已加载区间超额缓存数据 (${cached.timestamp}, 日期: ${cached.dateRange})`)
      } catch (e) {
        console.error('加载区间超额缓存失败:', e)
      }
    }
  }
}

// 初始化
onMounted(() => {
  // 设置区间超额的默认日期为上上周五到上周五
  customDateRange.value = getLastTwoFridays()

  // 加载缓存的计算结果
  loadCachedResults()

  // 移除自动计算月度超额，改为手动点击计算
  // handleCalculateMonthly()
})
</script>

<style scoped>
.summary-analysis-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.analysis-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 20px;
}

.analysis-subtitle {
  font-size: 14px;
  color: #606266;
}

.product-group {
  margin-bottom: 30px;
}

.group-header {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  padding: 12px 16px;
  background: linear-gradient(90deg, #f5f7fa 0%, #ffffff 100%);
  border-left: 4px solid #409EFF;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 数值样式 - 红涨绿跌 */
.profit-text {
  color: #F56C6C;  /* 红色表示上涨 */
  font-weight: 500;
}

.loss-text {
  color: #67C23A;  /* 绿色表示下跌 */
  font-weight: 500;
}

.drawdown-text {
  color: #909399;  /* 回撤用灰色 */
  font-weight: 500;
}

/* 单元格背景色 - 红涨绿跌 */
:deep(.positive-cell) {
  background-color: rgba(245, 108, 108, 0.08) !important;  /* 浅红色背景 */
}

:deep(.negative-cell) {
  background-color: rgba(103, 194, 58, 0.08) !important;  /* 浅绿色背景 */
}

/* 表格样式优化 */
:deep(.el-table) {
  width: 100%;
  font-size: 13px;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0;
}

:deep(.el-table__footer-wrapper .el-table__cell) {
  background-color: #fafafa;
  font-weight: bold;
}

:deep(.el-tabs--border-card) {
  border: 1px solid #DCDFE6;
  box-shadow: none;
}

:deep(.el-tabs__content) {
  padding: 20px;
}

/* 进度条样式 */
:deep(.el-progress__text) {
  font-size: 12px !important;
}

/* 图表对话框样式 */
.chart-dialog-content {
  min-height: 85vh;
}

.chart-type-selector {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
  padding: 16px 0;
  border-bottom: 1px solid #EBEEF5;
}

.chart-type-selector :deep(.el-radio-button__inner) {
  padding: 10px 24px;
  font-size: 14px;
}

.chart-section {
  margin-bottom: 30px;
}

.chart-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 3px solid #409EFF;
}

.group-chart {
  width: 100%;
  height: 75vh;
}
</style>
