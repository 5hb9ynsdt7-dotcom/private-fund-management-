<template>
  <div class="single-product-container">
    <!-- 产品基础信息卡片 -->
    <el-card class="info-card">
      <div class="product-info-row">
        <div class="product-left">
          <span class="product-title">{{ productInfo.displayName }}</span>
          <span class="product-subtitle">（跟踪指数：{{ getIndexName(productInfo.trackingIndex) }}）</span>
        </div>
        <div class="product-right">
          <span class="product-nav-info">最新净值：{{ formatNumber(productInfo.latestNav, 4) }}</span>
          <span class="product-nav-info">净值日期：{{ productInfo.latestDate }}</span>
          <el-tag :type="productInfo.productType === '500指增' ? 'success' : 'primary'" size="large">
            {{ productInfo.productType }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 核心指标区 -->
    <el-card class="metrics-card">
      <template #header>
        <div class="card-header">
          <span>核心指标（成立以来）</span>
        </div>
      </template>

      <!-- 第一行：产品本身指标 -->
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">年化收益</div>
            <div class="metric-value" :class="getValueClass(coreMetrics.annualizedReturn)">
              {{ formatPercent(coreMetrics.annualizedReturn) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">最大回撤</div>
            <div class="metric-value loss-text">
              {{ formatPercent(coreMetrics.maxDrawdown) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">波动率</div>
            <div class="metric-value">
              {{ formatPercent(coreMetrics.volatility) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">正收益月份占比</div>
            <div class="metric-value">
              {{ formatPercent(coreMetrics.positiveMonthRate) }}%
            </div>
          </div>
        </el-col>
      </el-row>

      <el-divider />

      <!-- 第二行：超额指标 -->
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">年化超额</div>
            <div class="metric-value" :class="getValueClass(coreMetrics.annualizedExcess)">
              {{ formatPercent(coreMetrics.annualizedExcess) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">最大超额回撤</div>
            <div class="metric-value loss-text">
              {{ formatPercent(coreMetrics.maxExcessDrawdown) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">超额波动率</div>
            <div class="metric-value">
              {{ formatPercent(coreMetrics.excessVolatility) }}%
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-item">
            <div class="metric-label">超额胜率</div>
            <div class="metric-value">
              {{ formatPercent(coreMetrics.excessMonthlyWinRate) }}%
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图表展示区 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>业绩图表</span>
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button label="nav">净值曲线</el-radio-button>
            <el-radio-button label="excess">累计超额</el-radio-button>
            <el-radio-button label="drawdown">超额回撤</el-radio-button>
            <el-radio-button label="monthly">月度超额</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <div class="chart-container" v-loading="chartLoading">
        <!-- 净值曲线图 -->
        <div ref="navChartRef" class="single-chart" :class="{ 'chart-active': chartType === 'nav' }"></div>

        <!-- 累计超额曲线 -->
        <div ref="excessChartRef" class="single-chart" :class="{ 'chart-active': chartType === 'excess' }"></div>

        <!-- 超额回撤曲线 -->
        <div ref="drawdownChartRef" class="single-chart" :class="{ 'chart-active': chartType === 'drawdown' }"></div>

        <!-- 月度超额柱状图 -->
        <div ref="monthlyChartRef" class="single-chart" :class="{ 'chart-active': chartType === 'monthly' }"></div>
      </div>
    </el-card>

    <!-- 月度超额数据表 -->
    <el-card class="data-card">
      <template #header>
        <div class="card-header">
          <span>月度超额数据</span>
          <el-button type="primary" size="small" @click="handleExportData">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
      </template>

      <el-table
        ref="dataTableRef"
        :data="monthlyExcessData"
        stripe
        class="data-table-full"
        :border="true"
      >
        <el-table-column prop="year" label="年份" align="center" min-width="80" fixed />

        <el-table-column prop="yearTotal" label="年度累计超额" align="center" min-width="130">
          <template #default="{ row }">
            <span :class="getValueClass(row.yearTotal)" style="font-weight: bold">
              {{ formatPercent(row.yearTotal) }}%
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month1" label="1月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month1)">
              {{ row.month1 !== null ? formatPercent(row.month1) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month2" label="2月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month2)">
              {{ row.month2 !== null ? formatPercent(row.month2) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month3" label="3月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month3)">
              {{ row.month3 !== null ? formatPercent(row.month3) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month4" label="4月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month4)">
              {{ row.month4 !== null ? formatPercent(row.month4) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month5" label="5月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month5)">
              {{ row.month5 !== null ? formatPercent(row.month5) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month6" label="6月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month6)">
              {{ row.month6 !== null ? formatPercent(row.month6) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month7" label="7月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month7)">
              {{ row.month7 !== null ? formatPercent(row.month7) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month8" label="8月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month8)">
              {{ row.month8 !== null ? formatPercent(row.month8) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month9" label="9月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month9)">
              {{ row.month9 !== null ? formatPercent(row.month9) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month10" label="10月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month10)">
              {{ row.month10 !== null ? formatPercent(row.month10) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month11" label="11月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month11)">
              {{ row.month11 !== null ? formatPercent(row.month11) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="month12" label="12月" align="center" min-width="80">
          <template #default="{ row }">
            <span :class="getValueClass(row.month12)">
              {{ row.month12 !== null ? formatPercent(row.month12) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="winRate" label="胜率" align="center" min-width="80" fixed="right">
          <template #default="{ row }">
            <span style="font-weight: 600">
              {{ row.winRate !== null ? formatPercent(row.winRate) + '%' : '--' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'

const route = useRoute()
const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8003'

// 产品信息
const productInfo = ref({
  displayName: '',
  productCode: '',
  trackingIndex: '',
  productType: '',
  latestNav: 0,
  latestDate: ''
})

// 核心指标
const coreMetrics = ref({
  annualizedExcess: 0,
  maxExcessDrawdown: 0,
  excessSharpe: 0,
  excessVolatility: 0,
  excessMonthlyWinRate: 0,  // 超额月度胜率
  positiveMonthRate: 0,      // 正收益月份占比
  informationRatio: 0,
  trackingError: 0
})

// 图表相关
const chartType = ref('nav')
const chartLoading = ref(false)
const refreshing = ref(false)  // 数据刷新状态

// 图表引用
const navChartRef = ref(null)
const excessChartRef = ref(null)
const drawdownChartRef = ref(null)
const monthlyChartRef = ref(null)

// 图表实例
let navChart = null
let excessChart = null
let drawdownChart = null
let monthlyChart = null

// 表格引用
const dataTableRef = ref(null)

// 月度超额数据
const monthlyExcessData = ref([])

// 分红数据
const dividendData = ref([])

// 获取指数名称
const getIndexName = (indexCode) => {
  const indexMap = {
    '000905.SH': '中证500',
    '000300.SH': '沪深300',
    '000906.SH': '中证800',
    '000510.SH': '中证A500',
    '000852.SH': '中证1000',
    '932000.CSI': '中证2000',
    '000001.SH': '上证指数'
  }
  return indexMap[indexCode] || indexCode
}

// 格式化函数
const formatNumber = (value, decimals = 2) => {
  if (!value && value !== 0) return '--'
  return Number(value).toFixed(decimals)
}

const formatPercent = (value) => {
  if (!value && value !== 0) return '--'
  return Number(value).toFixed(2)
}

const getValueClass = (value) => {
  if (value === null || value === undefined) return ''
  return value > 0 ? 'profit-text' : value < 0 ? 'loss-text' : ''
}

// 加载产品数据
const loadProductData = async (forceRefresh = false) => {
  const productId = decodeURIComponent(route.params.productId)

  try {
    // 1. 获取产品基础信息（包含已计算好的基础指标）
    const analysisResponse = await axios.get(`${API_BASE}/api/product-analysis/${productId}`)
    const analysisData = analysisResponse.data.data

    // 2. 从localStorage读取跟踪指数和产品类型(优先使用保存的配置)
    const savedConfigs = localStorage.getItem('quantProductConfigs')
    const productConfigs = savedConfigs ? JSON.parse(savedConfigs) : {}
    let trackingIndex = productConfigs[productId]?.trackingIndex
    let productType = productConfigs[productId]?.productType || ''

    // 如果localStorage没有配置,降级使用API响应
    if (!trackingIndex) {
      try {
        const infoResponse = await axios.get(`${API_BASE}/api/quantitative/product/${productId}`)
        trackingIndex = infoResponse.data.trackingIndex
      } catch (error) {
        console.warn('无法从API获取跟踪指数:', error)
      }
    }

    console.log('产品跟踪指数:', trackingIndex, '(来源:', productConfigs[productId]?.trackingIndex ? 'localStorage' : 'API', ')')

    // 更新产品信息
    productInfo.value = {
      productName: analysisData.fund_name,
      displayName: analysisData.fund_name.replace("龙舟-", "").replace("私募证券投资基金", "").replace(/-$/, ""),
      productCode: productId,
      trackingIndex: trackingIndex,
      productType: productType,
      latestNav: 0,
      latestDate: ''
    }

    // 3. 从产品分析结果中提取已计算好的指标
    coreMetrics.value = {
      // 产品本身指标（从后端获取，不重新计算）
      annualizedReturn: analysisData.basic_metrics.annualized_return,
      maxDrawdown: analysisData.basic_metrics.max_drawdown,
      volatility: analysisData.basic_metrics.volatility,
      positiveMonthRate: analysisData.monthly_stats.win_rate,  // 正收益月份占比 = 月度胜率

      // 超额指标（稍后计算，如果没有跟踪指数则为0）
      annualizedExcess: 0,
      maxExcessDrawdown: 0,
      excessVolatility: 0,
      excessMonthlyWinRate: 0,  // 超额月胜率（稍后从月度超额数据计算）

      // 其他指标
      excessSharpe: 0,
      informationRatio: 0,
      trackingError: 0
    }

    // 4. 获取产品净值数据
    const navResponse = await axios.get(`${API_BASE}/api/quantitative/product-nav/${productId}`)
    const navData = navResponse.data

    // 更新产品信息的最新净值和日期
    if (navData && navData.length > 0) {
      const latestNav = navData[navData.length - 1]
      productInfo.value.latestNav = latestNav.value
      productInfo.value.latestDate = latestNav.date
    }

    // 5. 获取产品分红数据
    try {
      const dividendResponse = await axios.get(`${API_BASE}/api/quantitative/product-dividends/${productId}`)
      dividendData.value = dividendResponse.data
      console.log('产品分红数据:', dividendData.value)
    } catch (error) {
      console.warn('获取分红数据失败:', error)
      dividendData.value = []
    }

    // 6. 加载多年月度超额数据（从API获取，不重新计算）
    if (trackingIndex) {
      try {
        // 根据产品实际存续时间动态生成年份列表
        const currentYear = new Date().getFullYear()
        let inceptionYear = currentYear // 默认为当前年份

        // 从产品最早的净值日期获取成立年份
        if (navData && navData.length > 0) {
          const inceptionDate = new Date(navData[0].date)
          inceptionYear = inceptionDate.getFullYear()
        }

        // 生成从成立年份到当前年份的所有年份（升序）
        const years = []
        for (let year = inceptionYear; year <= currentYear; year++) {
          years.push(year)
        }

        console.log(`=== 产品存续时间 ===`)
        console.log(`成立年份: ${inceptionYear}`)
        console.log(`当前年份: ${currentYear}`)
        console.log(`存续年数: ${currentYear - inceptionYear + 1}年`)
        console.log(`加载年份列表:`, years)

        const yearlyData = []

        // 并行加载多年数据
        const promises = years.map(year =>
          axios.post(
            `${API_BASE}/api/quantitative/calculate-monthly-excess`,
            {
              year: year,
              productConfigs: productConfigs
            }
          ).catch(error => {
            console.warn(`获取${year}年月度超额数据失败:`, error)
            return null
          })
        )

        const responses = await Promise.all(promises)

        // 处理每年的数据
        for (let i = 0; i < responses.length; i++) {
          const response = responses[i]
          if (!response) continue

          const year = years[i]
          const allMonthlyData = response.data
          const currentProductData = allMonthlyData.find(p => p.fundCode === productId)

          if (currentProductData) {
            // 构建年度数据行
            const yearRow = {
              year: year,
              yearTotal: currentProductData.yearTotal || 0,
              winRate: currentProductData.winRate || 0,
              month1: currentProductData.month1,
              month2: currentProductData.month2,
              month3: currentProductData.month3,
              month4: currentProductData.month4,
              month5: currentProductData.month5,
              month6: currentProductData.month6,
              month7: currentProductData.month7,
              month8: currentProductData.month8,
              month9: currentProductData.month9,
              month10: currentProductData.month10,
              month11: currentProductData.month11,
              month12: currentProductData.month12
            }

            yearlyData.push(yearRow)
          }
        }

        // 按年份倒序排列（2025 -> 2024 -> 2023 ...）
        monthlyExcessData.value = yearlyData.sort((a, b) => b.year - a.year)

        // 根据所有年度的月度超额数据计算整体超额月胜率
        let totalMonths = 0
        let positiveMonths = 0

        for (const yearRow of yearlyData) {
          for (let m = 1; m <= 12; m++) {
            const monthKey = `month${m}`
            const monthValue = yearRow[monthKey]

            if (monthValue !== null && monthValue !== undefined) {
              totalMonths++
              if (monthValue > 0) {
                positiveMonths++
              }
            }
          }
        }

        // 计算超额月胜率（百分比）并更新核心指标
        if (totalMonths > 0) {
          const excessMonthlyWinRate = (positiveMonths / totalMonths) * 100
          coreMetrics.value.excessMonthlyWinRate = excessMonthlyWinRate

          console.log('=== 超额月胜率计算 ===')
          console.log('总月份数:', totalMonths)
          console.log('正超额月份数:', positiveMonths)
          console.log('超额月胜率:', excessMonthlyWinRate.toFixed(2) + '%')
        }
      } catch (error) {
        console.warn('获取月度超额数据失败:', error)
      }
    }

    // 6. 绘制图表和计算超额指标（如果有跟踪指数）
    if (trackingIndex) {
      // 有跟踪指数：获取指数数据并计算超额指标
      try {
        const indexResponse = await axios.get(`${API_BASE}/api/quantitative/index-data`, {
          params: {
            index_code: trackingIndex,
            start_date: navData[0]?.date,
            end_date: navData[navData.length - 1]?.date
          }
        })
        const indexData = indexResponse.data

        // 获取周度超额曲线数据（含分红调整）
        const weeklyExcessResponse = await axios.post(`${API_BASE}/api/quantitative/weekly-excess-curve`, {
          fundCode: productId,
          startDate: navData[0]?.date,
          endDate: navData[navData.length - 1]?.date,
          indexCode: trackingIndex,
          indexDataMap: { [trackingIndex]: indexData },
          forceRefresh: forceRefresh
        })
        const weeklyExcessData = weeklyExcessResponse.data
        console.log('周度超额数据:', weeklyExcessData)

        // 基于API返回的周度超额数据计算核心指标
        calculateExcessMetrics(weeklyExcessData)

        // 绘制图表
        await nextTick()
        await drawCharts(navData, indexData, weeklyExcessData)
      } catch (error) {
        console.error('获取指数数据失败:', error)
        await nextTick()
        await drawChartsWithoutIndex(navData)
      }
    } else {
      // 没有跟踪指数（量化选股产品）：绘制简化图表
      console.log('该产品无跟踪指数，仅显示产品基础指标')
      await nextTick()
      await drawChartsWithoutIndex(navData)
    }
  } catch (error) {
    console.error('加载产品数据失败:', error)
    ElMessage.error('加载产品数据失败：' + error.message)
  }
}

// 刷新数据
const handleRefreshData = async () => {
  try {
    refreshing.value = true
    ElMessage.info('正在刷新数据...')
    await loadProductData(true)  // 传入forceRefresh=true
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新数据失败：' + error.message)
  } finally {
    refreshing.value = false
  }
}

// 绘制图表（无指数数据版本）
const drawChartsWithoutIndex = async (navData) => {
  // 简化版图表，仅显示净值曲线
  // TODO: 实现简化版图表逻辑
  console.log('绘制简化版图表（仅净值曲线）')
}

// 计算超额指标（基于API返回的周度超额数据）
const calculateExcessMetrics = (weeklyExcessData) => {
  if (!weeklyExcessData || weeklyExcessData.length < 2) {
    console.warn('周度超额数据不足，无法计算超额指标')
    return
  }

  console.log('=== 基于API数据计算超额指标 ===')
  console.log('数据点数:', weeklyExcessData.length)

  // Step 1: 计算年化超额收益率
  const totalWeeks = weeklyExcessData.length - 1
  const finalCumExcess = weeklyExcessData[weeklyExcessData.length - 1].cumExcessReturn // 百分比
  const excessMultiple = 1 + finalCumExcess / 100 // 转换为倍数
  const annualizedExcess = (Math.pow(excessMultiple, 52 / totalWeeks) - 1) * 100

  // Step 2: 计算最大超额回撤
  let peak = 0 // 累计超额的最高点
  let maxExcessDrawdown = 0
  for (const point of weeklyExcessData) {
    const cumExcess = point.cumExcessReturn
    if (cumExcess > peak) {
      peak = cumExcess
    }
    const drawdown = cumExcess - peak // 已经是百分比
    if (drawdown < maxExcessDrawdown) {
      maxExcessDrawdown = drawdown
    }
  }

  // Step 3: 计算年化超额波动率（基于周度超额收益率）
  const weeklyExcessReturns = []
  for (let i = 1; i < weeklyExcessData.length; i++) {
    const prevCumExcess = weeklyExcessData[i - 1].cumExcessReturn
    const currCumExcess = weeklyExcessData[i].cumExcessReturn

    // 从累计超额计算周度超额收益率
    const prevMultiple = 1 + prevCumExcess / 100
    const currMultiple = 1 + currCumExcess / 100
    const weeklyExcessReturn = (currMultiple / prevMultiple) - 1

    weeklyExcessReturns.push(weeklyExcessReturn)
  }

  const weeklyStd = calculateStdDev(weeklyExcessReturns)
  const excessVolatility = weeklyStd * Math.sqrt(52) * 100

  // Step 4: 计算衍生指标
  const avgExcessReturn = weeklyExcessReturns.reduce((sum, r) => sum + r, 0) / weeklyExcessReturns.length
  const excessSharpe = excessVolatility > 0 ? (avgExcessReturn * 52 * 100) / excessVolatility : 0
  const informationRatio = excessVolatility > 0 ? annualizedExcess / excessVolatility : 0

  // Step 5: 更新指标
  coreMetrics.value.annualizedExcess = annualizedExcess
  coreMetrics.value.maxExcessDrawdown = maxExcessDrawdown
  coreMetrics.value.excessVolatility = excessVolatility
  coreMetrics.value.excessSharpe = excessSharpe
  coreMetrics.value.informationRatio = informationRatio
  coreMetrics.value.trackingError = excessVolatility

  console.log('总周数:', totalWeeks)
  console.log('期末累计超额:', finalCumExcess.toFixed(2) + '%')
  console.log('年化超额收益率:', annualizedExcess.toFixed(2) + '%')
  console.log('最大超额回撤:', maxExcessDrawdown.toFixed(2) + '%')
  console.log('年化超额波动率:', excessVolatility.toFixed(2) + '%')
  console.log('信息比率:', informationRatio.toFixed(2))
  console.log('超额夏普:', excessSharpe.toFixed(2))
}

// 将日度净值转换为周度净值（取每周最后一个交易日）
const convertToWeeklyNav = (dailyNavData) => {
  if (!dailyNavData || dailyNavData.length === 0) return []

  const weeklyNav = []
  const weekMap = {}

  for (const nav of dailyNavData) {
    const date = new Date(nav.date)
    const year = date.getFullYear()
    const weekNum = getWeekNumber(date)
    const weekKey = `${year}-W${String(weekNum).padStart(2, '0')}`

    if (!weekMap[weekKey]) {
      weekMap[weekKey] = []
    }

    weekMap[weekKey].push({
      date: nav.date,
      value: nav.value,
      dateObj: date
    })
  }

  // 每周取最后一个交易日
  const weeks = Object.keys(weekMap).sort()
  for (const week of weeks) {
    const weekData = weekMap[week].sort((a, b) => a.dateObj - b.dateObj)
    const lastDay = weekData[weekData.length - 1]
    weeklyNav.push({
      week: week,
      date: lastDay.date,
      value: lastDay.value
    })
  }

  return weeklyNav
}

// 获取ISO周数
const getWeekNumber = (date) => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const dayNum = d.getUTCDay() || 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum)
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  return Math.ceil((((d - yearStart) / 86400000) + 1) / 7)
}

// 对齐周度数据（确保策略和基准的周次一致）
const alignWeeklyData = (strategyWeekly, benchmarkWeekly) => {
  const strategyNav = []
  const benchmarkNav = []

  for (const strat of strategyWeekly) {
    const bench = benchmarkWeekly.find(b => b.week === strat.week)
    if (bench) {
      strategyNav.push(strat.value)
      benchmarkNav.push(bench.value)
    }
  }

  return { strategy: strategyNav, benchmark: benchmarkNav }
}

// 辅助函数：计算标准差（样本标准差）
const calculateStdDev = (values) => {
  if (values.length === 0) return 0
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length
  const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length
  return Math.sqrt(variance)
}

// 绘制图表
const drawCharts = async (navData, indexData, weeklyExcessData) => {
  chartLoading.value = true

  // 先切换到nav确保第一个图表激活
  chartType.value = 'nav'

  // 等待DOM更新
  await nextTick()

  // 销毁旧图表实例
  if (navChart) navChart.dispose()
  if (excessChart) excessChart.dispose()
  if (drawdownChart) drawdownChart.dispose()
  if (monthlyChart) monthlyChart.dispose()

  // 初始化所有图表（现在所有容器都在DOM中，可以正常获取尺寸）
  navChart = echarts.init(navChartRef.value)
  excessChart = echarts.init(excessChartRef.value)
  drawdownChart = echarts.init(drawdownChartRef.value)
  monthlyChart = echarts.init(monthlyChartRef.value)

  // 准备数据
  const dates = navData.map(d => d.date)
  const navValues = navData.map(d => d.value) // 单位净值
  const accumNavValues = navData.map(d => d.accumValue) // 累计净值
  const indexValues = []
  const excessCurve = []
  const drawdownCurve = []

  // 归一化指数到同一起点
  const startNav = navData[0].value
  const startIndex = indexData.find(idx => idx.date === navData[0].date)?.value || 1

  // 将周度超额数据转换为日度格式（前向填充）
  // API返回格式: [{date: "2024-01-05", cumExcessReturn: 1.23}, ...]
  const weeklyExcessMap = new Map()
  if (weeklyExcessData && weeklyExcessData.length > 0) {
    for (const weekData of weeklyExcessData) {
      weeklyExcessMap.set(weekData.date, weekData.cumExcessReturn)
    }
  }

  let lastWeeklyExcess = 0 // 最近一次的周度超额值（用于前向填充）
  let cumExcess = 1 // 用于回撤计算
  let maxCumExcess = 1

  for (let i = 0; i < navData.length; i++) {
    const nav = navData[i]
    const index = indexData.find(idx => idx.date === nav.date)

    if (index) {
      // 归一化指数
      const normalizedIndex = (index.value / startIndex) * startNav
      indexValues.push(normalizedIndex)

      // 使用API提供的周度超额数据（如果当天有周度数据则更新，否则使用上次的值）
      if (weeklyExcessMap.has(nav.date)) {
        lastWeeklyExcess = weeklyExcessMap.get(nav.date)
      }
      excessCurve.push(lastWeeklyExcess)

      // 计算累计超额倍数（用于回撤计算）
      cumExcess = 1 + lastWeeklyExcess / 100

      // 计算超额回撤
      maxCumExcess = Math.max(maxCumExcess, cumExcess)
      const drawdown = (1 - cumExcess / maxCumExcess) * 100
      drawdownCurve.push(drawdown)
    }
  }

  // 统一的grid配置 - 使用百分比让图表撑满容器
  const commonGrid = {
    left: '5%',
    right: '2%',
    top: '50px',
    bottom: '50px',
    containLabel: true
  }

  // 准备分红标记点数据（作为单独的散点系列，显示在单位净值上）
  const dividendScatterData = dividendData.value
    .filter(d => d.exDividendDate) // 只显示有除息日的分红
    .map(dividend => {
      // 找到除息日在dates中的索引
      const dateIndex = dates.findIndex(date => date === dividend.exDividendDate)
      if (dateIndex === -1) return null

      // 获取该日期的单位净值（分红标记显示在单位净值上）
      const navValue = navValues[dateIndex]

      return {
        value: [dividend.exDividendDate, navValue],
        dividend: {
          exDividendDate: dividend.exDividendDate,
          preDividendNav: dividend.preDividendNav,
          dividendPerShare: dividend.dividendPerShare,
          dividendDate: dividend.dividendDate
        }
      }
    })
    .filter(point => point !== null) // 过滤掉找不到对应日期的分红

  console.log('分红散点数据:', dividendScatterData)

  // 净值曲线图配置
  const navOption = {
    tooltip: {
      trigger: 'item',
      axisPointer: { type: 'cross' },
      formatter: function(params) {
        // 检查是否是分红散点
        if (params.seriesName === '分红') {
          const dividend = params.data.dividend
          return `<div style="font-weight: bold; margin-bottom: 5px; color: #F56C6C;">● 分红信息</div>
                  <div>基准日（除息日）: ${dividend.exDividendDate}</div>
                  <div>除权前净值: ${dividend.preDividendNav ? dividend.preDividendNav.toFixed(4) : '--'}</div>
                  <div>分红方案: ${dividend.dividendPerShare.toFixed(4)} 元/份</div>`
        }

        // 普通的净值和指数数据
        return params.marker + params.seriesName + ': ' + Number(params.value[1] || params.value).toFixed(4)
      }
    },
    legend: {
      data: ['单位净值', '累计净值', '指数（归一）', '分红'],
      top: 10,
      left: 'center',
      textStyle: {
        fontSize: 12
      }
    },
    grid: commonGrid,
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '净值',
      scale: true  // 不从0开始
    },
    series: [
      {
        name: '单位净值',
        type: 'line',
        data: navValues,
        smooth: true,
        lineStyle: { color: '#409EFF', width: 2 },
        showSymbol: false
      },
      {
        name: '累计净值',
        type: 'line',
        data: accumNavValues,
        smooth: true,
        lineStyle: { color: '#E6A23C', width: 2, type: 'dashed' },
        showSymbol: false
      },
      {
        name: '指数（归一）',
        type: 'line',
        data: indexValues,
        smooth: true,
        lineStyle: { color: '#909399', width: 1 },
        showSymbol: false
      },
      {
        name: '分红',
        type: 'scatter',
        data: dividendScatterData,
        symbolSize: 12,
        itemStyle: {
          color: '#F56C6C',
          borderColor: '#FFF',
          borderWidth: 2
        },
        emphasis: {
          itemStyle: {
            color: '#F56C6C',
            borderColor: '#FFF',
            borderWidth: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(245, 108, 108, 0.5)'
          }
        },
        z: 10  // 确保分红点显示在最上层
      }
    ]
  }

  // 累计超额曲线配置
  const excessOption = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return params[0].axisValue + '<br/>超额收益: ' + Number(params[0].value).toFixed(2) + '%'
      }
    },
    grid: commonGrid,
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '超额收益(%)',
      scale: true
    },
    series: [
      {
        type: 'line',
        data: excessCurve,
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        },
        lineStyle: { color: '#409EFF', width: 2 },
        showSymbol: false
      }
    ]
  }

  // 超额回撤曲线配置
  const drawdownOption = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return params[0].axisValue + '<br/>回撤: ' + Number(params[0].value).toFixed(2) + '%'
      }
    },
    grid: commonGrid,
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      name: '回撤(%)',
      inverse: true,
      scale: true
    },
    series: [
      {
        type: 'line',
        data: drawdownCurve,
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
            { offset: 1, color: 'rgba(103, 194, 58, 0.1)' }
          ])
        },
        lineStyle: { color: '#67C23A', width: 2 },
        showSymbol: false
      }
    ]
  }

  // 月度超额柱状图配置
  // 将API格式的月度超额数据转换为图表格式
  const monthlyData = convertMonthlyExcessDataForChart(monthlyExcessData.value)
  const monthlyOption = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return params[0].axisValue + '<br/>超额收益: ' + Number(params[0].value).toFixed(2) + '%'
      }
    },
    grid: commonGrid,
    xAxis: {
      type: 'category',
      data: monthlyData.months,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '超额收益(%)',
      scale: true
    },
    series: [
      {
        type: 'bar',
        data: monthlyData.values,
        itemStyle: {
          color: function(params) {
            return params.value > 0 ? '#F56C6C' : '#67C23A'
          }
        }
      }
    ]
  }

  // 设置图表
  navChart.setOption(navOption)
  excessChart.setOption(excessOption)
  drawdownChart.setOption(drawdownOption)
  monthlyChart.setOption(monthlyOption)

  // 调试：打印图表配置和DOM尺寸
  console.log('=== 图表配置调试 ===')
  console.log('commonGrid:', commonGrid)
  console.log('commonGrid详细:', JSON.stringify(commonGrid))
  console.log('navChart DOM height:', navChartRef.value?.clientHeight)
  console.log('excessChart DOM height:', excessChartRef.value?.clientHeight)
  console.log('drawdownChart DOM height:', drawdownChartRef.value?.clientHeight)
  console.log('monthlyChart DOM height:', monthlyChartRef.value?.clientHeight)
  console.log('navOption.grid === commonGrid:', navOption.grid === commonGrid)
  console.log('excessOption.grid === commonGrid:', excessOption.grid === commonGrid)
  console.log('drawdownOption.grid === commonGrid:', drawdownOption.grid === commonGrid)
  console.log('monthlyOption.grid === commonGrid:', monthlyOption.grid === commonGrid)
  console.log('navOption.grid:', JSON.stringify(navOption.grid))
  console.log('excessOption.grid:', JSON.stringify(excessOption.grid))
  console.log('drawdownOption.grid:', JSON.stringify(drawdownOption.grid))
  console.log('monthlyOption.grid:', JSON.stringify(monthlyOption.grid))

  chartLoading.value = false
}

// 将API格式的月度超额数据转换为图表格式
const convertMonthlyExcessDataForChart = (yearlyData) => {
  const months = []
  const values = []

  // 按年份升序排列（从旧到新）
  const sortedYears = [...yearlyData].sort((a, b) => a.year - b.year)

  for (const yearRow of sortedYears) {
    for (let m = 1; m <= 12; m++) {
      const monthKey = `month${m}`
      const monthValue = yearRow[monthKey]

      if (monthValue !== null && monthValue !== undefined) {
        months.push(`${yearRow.year}-${String(m).padStart(2, '0')}`)
        values.push(monthValue)
      }
    }
  }

  return { months, values }
}

// 计算月度超额数据
const calculateMonthlyExcess = (navData, indexData) => {
  const monthlyData = {}

  for (let i = 1; i < navData.length; i++) {
    const currNav = navData[i]
    const prevNav = navData[i - 1]

    const month = currNav.date.substring(0, 7)
    const prevMonth = prevNav.date.substring(0, 7)

    if (month !== prevMonth) {
      // 月末数据
      const currIndex = indexData.find(idx => idx.date === currNav.date)
      const prevIndex = indexData.find(idx => idx.date === prevNav.date)

      if (currIndex && prevIndex) {
        const productReturn = (currNav.value / prevNav.value - 1) * 100
        const indexReturn = (currIndex.value / prevIndex.value - 1) * 100
        monthlyData[month] = productReturn - indexReturn
      }
    }
  }

  return {
    months: Object.keys(monthlyData),
    values: Object.values(monthlyData)
  }
}

// 导出数据
const handleExportData = () => {
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.json_to_sheet(monthlyExcessData.value)
  XLSX.utils.book_append_sheet(wb, ws, '月度超额数据')

  XLSX.writeFile(wb, `${productInfo.value.displayName}_月度超额_${new Date().toLocaleDateString()}.xlsx`)
  ElMessage.success('数据导出成功')
}

// 监听图表类型切换
watch(chartType, async (newType) => {
  await nextTick()

  // 切换后立即resize对应的图表确保显示正确
  if (newType === 'nav' && navChart) {
    navChart.resize()
  } else if (newType === 'excess' && excessChart) {
    excessChart.resize()
  } else if (newType === 'drawdown' && drawdownChart) {
    drawdownChart.resize()
  } else if (newType === 'monthly' && monthlyChart) {
    monthlyChart.resize()
  }
})

// 监听路由变化
watch(() => route.params.productId, () => {
  if (route.params.productId) {
    loadProductData()
  }
})

// 初始化
onMounted(() => {
  loadProductData()

  // 同步表头和表体的横向滚动
  nextTick(() => {
    const table = dataTableRef.value
    if (table && table.$el) {
      const headerWrapper = table.$el.querySelector('.el-table__header-wrapper')
      const bodyWrapper = table.$el.querySelector('.el-table__body-wrapper')

      if (headerWrapper && bodyWrapper) {
        // 监听body滚动，同步到header
        bodyWrapper.addEventListener('scroll', () => {
          headerWrapper.scrollLeft = bodyWrapper.scrollLeft
        })
      }
    }
  })
})

// 监听数据变化，重新同步滚动
watch(monthlyExcessData, () => {
  nextTick(() => {
    const table = dataTableRef.value
    if (table && table.$el) {
      const headerWrapper = table.$el.querySelector('.el-table__header-wrapper')
      const bodyWrapper = table.$el.querySelector('.el-table__body-wrapper')

      if (headerWrapper && bodyWrapper) {
        headerWrapper.scrollLeft = bodyWrapper.scrollLeft
      }
    }
  })
})
</script>

<style scoped>
.single-product-container {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.info-card,
.metrics-card,
.chart-card {
  margin-bottom: 20px;
}

.data-card {
  margin-bottom: 20px;
  height: 400px;  /* 增加高度以适应多年数据 */
}

.data-card :deep(.el-card__body) {
  padding: 0 !important;
  margin: 0 !important;
  height: calc(100% - 56px) !important;  /* 减去header高度 */
  display: block !important;
  box-sizing: border-box;
  overflow: hidden !important;
}

.data-card :deep(.el-card__header) {
  height: 56px;
  padding: 16px 20px;
}

.data-table-full {
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  display: block !important;
  overflow: hidden !important;
}

.data-table-full :deep(.el-table__inner-wrapper) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

.data-table-full :deep(.el-table__header-wrapper) {
  flex-shrink: 0 !important;
  overflow-x: auto !important;  /* 支持横向滚动 */
  scrollbar-width: none;  /* Firefox隐藏滚动条 */
  -ms-overflow-style: none;  /* IE隐藏滚动条 */
}

.data-table-full :deep(.el-table__header-wrapper)::-webkit-scrollbar {
  display: none;  /* Chrome/Safari隐藏滚动条 */
}

.data-table-full :deep(.el-table__body-wrapper) {
  flex: 1 !important;
  overflow-y: auto !important;
  overflow-x: auto !important;  /* 支持横向滚动 */
  height: auto !important;
}

/* 同步表头和表体的横向滚动 */
.data-table-full :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
}

.data-table-full :deep(table) {
  width: 100% !important;  /* 表格宽度100% */
  min-width: 1250px !important;  /* 最小宽度确保内容不挤压 */
  table-layout: fixed !important;  /* 使用固定布局确保对齐 */
}

.data-table-full :deep(.el-table__header table),
.data-table-full :deep(.el-table__body table) {
  width: 100% !important;  /* 表格宽度100% */
  min-width: 1250px !important;  /* 最小宽度确保内容不挤压 */
  table-layout: fixed !important;  /* 使用固定布局确保对齐 */
}

.data-table-full :deep(.el-table__cell) {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

.chart-card :deep(.el-card__body) {
  padding: 10px;
  height: 600px !important;
  display: block;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 产品信息行样式 */
.product-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.product-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.product-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.product-subtitle {
  font-size: 14px;
  color: #909399;
  font-weight: 400;
}

.product-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.product-nav-info {
  font-size: 14px;
  color: #606266;
}

.info-item {
  margin-bottom: 12px;
}

.info-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.info-value {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.nav-value,
.date-cell {
  font-family: 'Inter', 'SF Pro Display', monospace;
}

.metric-item {
  text-align: center;
}

.metric-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 10px;
  font-weight: 400;
}

.metric-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', monospace;
  line-height: 1.4;
}

.chart-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: block;
}

.single-chart {
  position: absolute;
  top: 0;
  left: 0;
  width: 100% !important;
  height: 100% !important;
  display: block !important;
  opacity: 0;
  visibility: hidden;
  z-index: 1;
  transition: opacity 0.3s ease;
}

.single-chart.chart-active {
  opacity: 1;
  visibility: visible;
  z-index: 10;
}

.profit-text {
  color: #F56C6C;  /* 红色表示上涨 */
  font-weight: 600;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', monospace;
}

.loss-text {
  color: #67C23A;  /* 绿色表示下跌 */
  font-weight: 600;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', monospace;
}

/* 统计数字样式 */
:deep(.el-statistic__content) {
  font-family: 'Inter', 'SF Pro Display', monospace;
}

:deep(.el-statistic__number) {
  font-size: 28px;
}

/* 卡片样式 */
:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #EBEEF5;
}

:deep(.el-card__body) {
  padding: 20px;
}

/* 表格样式 */
:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table .el-table__cell) {
  padding: 10px 0;
}
</style>