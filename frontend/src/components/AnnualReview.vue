<template>
  <div class="annual-review">
    <!-- 年份选择 -->
    <el-card class="year-selector-card">
      <div class="selector-wrapper">
        <span class="selector-label">选择复盘年份：</span>
        <el-select v-model="selectedYear" @change="loadAnnualData" placeholder="请选择年份">
          <el-option
            v-for="year in availableYears"
            :key="year"
            :label="`${year}年`"
            :value="year"
          />
        </el-select>
        <el-button type="primary" :loading="loading" @click="loadAnnualData" :disabled="!selectedYear">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 年度数据展示 -->
    <div v-else-if="annualData">
      <!-- 年度汇总卡片 -->
      <el-card class="summary-card">
        <template #header>
          <div class="card-header">
            <span>{{ selectedYear }}年度投资汇总</span>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="6">
            <div class="summary-item">
              <div class="label">年度总收益</div>
              <div class="value" :class="getPnlClass(annualData.annual_summary.total_return)">
                {{ formatMoney(annualData.annual_summary.total_return) }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="label">表现最佳季度</div>
              <div class="value">
                {{ annualData.annual_summary.best_quarter }}
                <span class="sub-value" :class="getPnlClass(annualData.annual_summary.best_quarter_return)">
                  ({{ formatMoney(annualData.annual_summary.best_quarter_return) }})
                </span>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="label">表现最差季度</div>
              <div class="value">
                {{ annualData.annual_summary.worst_quarter }}
                <span class="sub-value" :class="getPnlClass(annualData.annual_summary.worst_quarter_return)">
                  ({{ formatMoney(annualData.annual_summary.worst_quarter_return) }})
                </span>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="label">年初市值</div>
              <div class="value">
                {{ formatMoney(annualData.annual_summary.year_start_value) }}
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 季度收益与累计收益图表 -->
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>{{ selectedYear }}年度投资复盘 | 季度收益与累计收益</span>
          </div>
        </template>

        <div ref="chartRef" class="chart-container"></div>
      </el-card>

      <!-- 持仓变动分析 -->
      <el-card class="holdings-change-card" v-loading="holdingsLoading">
        <template #header>
          <div class="card-header">
            <span>持仓变动分析</span>
            <el-button
              type="primary"
              size="small"
              @click="analyzeHoldingsChange"
              :loading="holdingsLoading"
            >
              <el-icon><Refresh /></el-icon>
              生成分析
            </el-button>
          </div>
        </template>

        <div v-if="holdingsAnalysis" class="holdings-analysis-content" v-html="holdingsAnalysis"></div>
        <el-empty v-else description="点击生成分析按钮查看持仓变动分析" />
      </el-card>

      <!-- 年度收益分析图表 -->
      <el-card class="contribution-charts-card" v-if="contributionData">
        <template #header>
          <div class="card-header">
            <span>年度收益分析</span>
          </div>
        </template>

        <el-row :gutter="24">
          <!-- 左侧：策略收益贡献饼图 -->
          <el-col :span="10">
            <div class="chart-container">
              <h4 class="chart-title">策略收益贡献分布</h4>
              <div ref="strategyChartRef" class="chart" style="height: 400px;"></div>
            </div>
          </el-col>

          <!-- 右侧：产品收益柱状图 -->
          <el-col :span="14">
            <div class="chart-container">
              <div ref="waterfallChartRef" class="chart" style="height: 540px;"></div>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 季度产品明细表 -->
      <el-card class="details-card">
        <template #header>
          <div class="card-header">
            <span>季度产品收益明细</span>
          </div>
        </template>

        <el-collapse v-model="activeQuarters" accordion>
          <el-collapse-item
            v-for="quarter in annualData.quarterly_performance"
            :key="quarter.quarter"
            :name="quarter.quarter"
          >
            <template #title>
              <div class="quarter-title">
                <span class="quarter-name">{{ quarter.quarter_label }}</span>
                <span class="quarter-stats">
                  季度收益:
                  <span :class="getPnlClass(quarter.total_return)">
                    {{ formatMoney(quarter.total_return) }}
                  </span>
                  | 累计收益:
                  <span :class="getPnlClass(quarter.cumulative_return)">
                    {{ formatMoney(quarter.cumulative_return) }}
                  </span>
                </span>
              </div>
            </template>

            <el-table
              :data="quarter.products"
              style="width: 100%"
              stripe
              border
            >
              <el-table-column
                prop="fund_name"
                label="产品名称"
                min-width="200"
                align="left"
                show-overflow-tooltip
              />

              <el-table-column
                prop="main_strategy"
                label="主策略"
                width="120"
                align="center"
              >
                <template #default="{ row }">
                  <el-tag size="small">{{ row.main_strategy || '--' }}</el-tag>
                </template>
              </el-table-column>

              <el-table-column
                prop="sub_strategy"
                label="细分策略"
                width="120"
                align="center"
              >
                <template #default="{ row }">
                  <el-tag size="small" type="info">{{ row.sub_strategy || '--' }}</el-tag>
                </template>
              </el-table-column>

              <el-table-column
                prop="start_market_value"
                label="期初市值"
                width="130"
                align="center"
              >
                <template #default="{ row }">
                  <span class="money-text">{{ formatMoney(row.start_market_value) }}</span>
                </template>
              </el-table-column>

              <el-table-column
                prop="end_market_value"
                label="期末市值"
                width="130"
                align="center"
              >
                <template #default="{ row }">
                  <span class="money-text">{{ formatMoney(row.end_market_value) }}</span>
                </template>
              </el-table-column>

              <el-table-column
                prop="period_cashflow"
                label="期间现金流"
                width="130"
                align="center"
              >
                <template #default="{ row }">
                  <span class="money-text" :class="getCashflowClass(row.period_cashflow)">
                    {{ formatMoney(row.period_cashflow) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column
                prop="period_dividend"
                label="分红金额"
                width="130"
                align="center"
              >
                <template #default="{ row }">
                  <span class="money-text dividend-text">
                    {{ formatMoney(row.period_dividend || 0) }}
                  </span>
                </template>
              </el-table-column>

              <el-table-column
                prop="period_return"
                label="季度收益"
                width="130"
                align="center"
              >
                <template #default="{ row }">
                  <span class="money-text" :class="getPnlClass(row.period_return)">
                    {{ formatMoney(row.period_return) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-else description="请选择年份查看年度收益复盘" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled, Refresh } from '@element-plus/icons-vue'
import { transactionAPI } from '@/api/transaction'
import * as echarts from 'echarts'

const props = defineProps({
  groupId: {
    type: String,
    required: true
  }
})

// 响应式数据
const loading = ref(false)
const selectedYear = ref(2025)  // 默认选择2025年
const annualData = ref(null)
const chartRef = ref(null)
const activeQuarters = ref(['Q1'])
const holdingsLoading = ref(false)
const holdingsAnalysis = ref(null)
const contributionData = ref(null)  // 年度收益贡献数据
const strategyChartRef = ref(null)  // 策略饼图ref
const waterfallChartRef = ref(null)  // 瀑布图ref
let chartInstance = null
let strategyChartInstance = null
let waterfallChartInstance = null

// 可选年份列表（从2020年到2026年）
const availableYears = ref([])
const initYears = () => {
  const currentYear = new Date().getFullYear()
  const years = []
  // 从2020年到当前年份，最多到2026年
  const endYear = Math.min(currentYear, 2026)
  for (let year = 2020; year <= endYear; year++) {
    years.push(year)
  }
  // 如果当前年份小于2026，也添加2026年
  if (currentYear < 2026 && !years.includes(2026)) {
    years.push(2026)
  }
  availableYears.value = years.reverse() // 倒序，最新年份在前
}

// 加载年度数据
const loadAnnualData = async () => {
  if (!selectedYear.value) {
    ElMessage.warning('请先选择年份')
    return
  }

  loading.value = true
  annualData.value = null // 清空旧数据

  try {
    const response = await transactionAPI.getClientAnnualReview(props.groupId, selectedYear.value)
    annualData.value = response

    console.log('年度数据加载成功:', response)
  } catch (error) {
    console.error('加载年度数据失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(`加载年度数据失败: ${errorMsg}`)
    annualData.value = null
    loading.value = false
    return
  }

  // 数据加载成功后，先结束loading状态
  loading.value = false

  // 等待DOM更新后渲染图表
  await nextTick()

  // 再等待一小段时间，确保DOM完全渲染
  setTimeout(() => {
    if (chartRef.value && annualData.value) {
      console.log('准备渲染图表')
      renderChart()
    } else {
      console.error('图表渲染失败，DOM未准备好', {
        hasChartRef: !!chartRef.value,
        hasAnnualData: !!annualData.value
      })
    }
  }, 150)
}

// 渲染图表
const renderChart = () => {
  console.log('renderChart 被调用', {
    hasChartRef: !!chartRef.value,
    hasAnnualData: !!annualData.value,
    chartRefElement: chartRef.value,
    annualDataKeys: annualData.value ? Object.keys(annualData.value) : []
  })

  if (!chartRef.value) {
    console.warn('图表渲染失败：chartRef为空')
    return
  }

  if (!annualData.value) {
    console.warn('图表渲染失败：annualData为空')
    return
  }

  if (!annualData.value.quarterly_performance || annualData.value.quarterly_performance.length === 0) {
    console.warn('图表渲染失败：没有季度数据')
    ElMessage.warning('暂无该年份的季度数据')
    return
  }

  // 检查容器尺寸
  const rect = chartRef.value.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    console.warn('图表容器尺寸为0', rect)
    ElMessage.warning('图表容器未正确显示')
    return
  }

  // 销毁旧图表实例
  if (chartInstance) {
    chartInstance.dispose()
  }

  // 创建新图表实例
  chartInstance = echarts.init(chartRef.value)

  // 准备数据
  const quarters = annualData.value.quarterly_performance.map(q => q.quarter)
  const quarterlyReturns = annualData.value.quarterly_performance.map(q => q.total_return)
  const cumulativeReturns = annualData.value.quarterly_performance.map(q => q.cumulative_return)

  console.log('图表数据:', { quarters, quarterlyReturns, cumulativeReturns })

  // 图表配置
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        crossStyle: {
          color: '#999'
        }
      },
      formatter: function (params) {
        let result = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          const value = formatMoney(param.value)
          // 红涨绿跌：正数红色，负数绿色
          const color = param.value >= 0 ? '#f56c6c' : '#67c23a'
          result += `
            <div style="display: flex; align-items: center; margin-top: 5px;">
              <span style="display: inline-block; width: 10px; height: 10px; background-color: ${param.color}; border-radius: 50%; margin-right: 5px;"></span>
              <span style="flex: 1;">${param.seriesName}:</span>
              <span style="font-weight: bold; color: ${color}; margin-left: 10px;">${value}</span>
            </div>
          `
        })
        return result
      }
    },
    legend: {
      data: ['季度收益', '累计收益'],
      top: '2%',
      left: 'center'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: quarters,
      axisPointer: {
        type: 'shadow'
      },
      axisLabel: {
        fontSize: 12,
        fontWeight: 'bold'
      }
    },
    yAxis: {
      type: 'value',
      name: '收益（元）',
      nameLocation: 'end',
      nameTextStyle: {
        align: 'right',
        padding: [0, 5, 0, 0]
      },
      axisLabel: {
        formatter: function (value) {
          if (Math.abs(value) >= 10000) {
            return (value / 10000).toFixed(1) + '万'
          }
          return value.toFixed(0)
        }
      }
    },
    series: [
      {
        name: '季度收益',
        type: 'bar',
        data: quarterlyReturns,
        itemStyle: {
          color: function (params) {
            // 红涨绿跌：正数红色，负数绿色
            return params.data >= 0 ? '#f56c6c' : '#67c23a'
          }
        },
        label: {
          show: true,
          position: 'inside',  // 标签显示在柱子内部（中间）
          formatter: function (params) {
            return formatMoney(params.value, false)
          },
          fontSize: 11,
          color: '#ffffff',  // 白色字体
          fontWeight: 'bold'
        }
      },
      {
        name: '累计收益',
        type: 'line',
        data: cumulativeReturns,
        itemStyle: {
          color: '#409eff'
        },
        lineStyle: {
          width: 3
        },
        symbol: 'circle',
        symbolSize: 8,
        label: {
          show: true,
          position: 'top',  // 折线标签始终在上方
          offset: [0, -10],  // 向上偏移10px，避免与柱状图重叠
          formatter: function (params) {
            return formatMoney(params.value, false)
          },
          fontSize: 10,
          color: '#606266',  // 深灰色
          fontWeight: 'normal'
        }
      }
    ]
  }

  chartInstance.setOption(option)

  // 监听窗口大小变化（只添加一次）
  if (!window.chartResizeListenerAdded) {
    window.addEventListener('resize', handleResize)
    window.chartResizeListenerAdded = true
  }
}

// 格式化函数
const formatMoney = (amount, showSymbol = true) => {
  if (amount == null || amount === '') return '--'
  const num = parseFloat(amount)
  const formatted = num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
  return showSymbol ? `¥ ${formatted}` : formatted
}

const getPnlClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  // 红涨绿跌：正数红色，负数绿色
  return num >= 0 ? 'profit-text' : 'loss-text'
}

const getCashflowClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  return num > 0 ? 'cashflow-out' : num < 0 ? 'cashflow-in' : ''
}

// 持仓变动分析
const analyzeHoldingsChange = async () => {
  if (!selectedYear.value) {
    ElMessage.warning('请先选择年份')
    return
  }

  holdingsLoading.value = true
  try {
    const response = await transactionAPI.getHoldingsChangeAnalysis(props.groupId, selectedYear.value)

    // 生成Markdown格式的分析报告
    const html = generateHoldingsAnalysisHTML(response)
    holdingsAnalysis.value = html

    // 保存收益贡献数据
    if (response.year_contribution_analysis) {
      contributionData.value = response.year_contribution_analysis

      // 等待DOM更新后初始化图表
      await nextTick()
      initContributionCharts()
    }
  } catch (error) {
    console.error('生成持仓变动分析失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(`生成持仓变动分析失败: ${errorMsg}`)
  } finally {
    holdingsLoading.value = false
  }
}

// 生成持仓变动分析HTML
const generateHoldingsAnalysisHTML = (data) => {
  const { client_info, year_start_holdings, year_end_holdings, year_contribution_analysis } = data

  // 后端已经按照策略排序，前端不再重新排序
  const sortedStartHoldings = year_start_holdings
  const sortedEndHoldings = year_end_holdings

  // 计算总计
  const startTotal = {
    count: sortedStartHoldings.length,
    cost: sortedStartHoldings.reduce((sum, h) => sum + h.cost, 0),
    marketValue: sortedStartHoldings.reduce((sum, h) => sum + h.market_value, 0),
    pnl: sortedStartHoldings.reduce((sum, h) => sum + h.pnl, 0)
  }

  const endTotal = {
    count: sortedEndHoldings.length,
    cost: sortedEndHoldings.reduce((sum, h) => sum + h.cost, 0),
    marketValue: sortedEndHoldings.reduce((sum, h) => sum + h.market_value, 0),
    pnl: sortedEndHoldings.reduce((sum, h) => sum + h.pnl, 0)
  }

  // 分析持仓变动
  const startMap = new Map(sortedStartHoldings.map(h => [h.product_code, h]))
  const endMap = new Map(sortedEndHoldings.map(h => [h.product_code, h]))

  const cleared = []  // 清仓
  const reduced = []  // 部分赎回
  const added = []    // 新增
  const intraYearTraded = []  // 年内新增又清仓

  // 从年度收益贡献数据中找出年内新增又清仓的产品
  if (year_contribution_analysis && year_contribution_analysis.product_contribution) {
    year_contribution_analysis.product_contribution.forEach(p => {
      // 年初市值=0 且 年末市值=0，说明是年内新增又清仓
      if (p.year_start_value === 0 && p.year_end_value === 0 && (p.year_purchase > 0 || p.year_redemption > 0)) {
        intraYearTraded.push({
          product_code: p.product_code,
          fund_name: p.fund_name,
          product_name: p.product_name,
          year_purchase: p.year_purchase,
          year_redemption: p.year_redemption,
          year_return: p.year_return,
          return_rate: p.return_rate
        })
      }
    })
  }

  // 找出清仓和部分赎回
  for (const [code, startHolding] of startMap) {
    const endHolding = endMap.get(code)
    if (!endHolding) {
      cleared.push(startHolding)
    } else if (endHolding.market_value < startHolding.market_value * 0.9) {
      reduced.push({
        ...endHolding,
        start_market_value: startHolding.market_value,
        reduction: startHolding.market_value - endHolding.market_value
      })
    }
  }

  // 找出新增
  for (const [code, endHolding] of endMap) {
    if (!startMap.has(code)) {
      added.push(endHolding)
    }
  }

  // 定义内联样式
  const styles = {
    container: 'padding: 16px;',
    tablesRow: 'display: flex; gap: 20px; margin-bottom: 24px;',
    tableCol: 'flex: 1; min-width: 0;',
    h3: 'font-size: 16px; font-weight: 600; color: #303133; margin: 0 0 12px 0;',
    table: 'width: 100%; border-collapse: collapse; margin-bottom: 16px; font-size: 13px; border: 1px solid #dcdfe6;',
    th: 'border: 1px solid #dcdfe6; padding: 12px 8px; text-align: center; background-color: #409eff; font-weight: 600; color: #ffffff; font-size: 13px;',
    thLeft: 'border: 1px solid #dcdfe6; padding: 12px 8px; text-align: left; background-color: #409eff; font-weight: 600; color: #ffffff; font-size: 13px;',
    td: 'border: 1px solid #dcdfe6; padding: 10px 8px; text-align: center; color: #606266;',
    tdLeft: 'border: 1px solid #dcdfe6; padding: 10px 8px; text-align: left; color: #606266; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;',
    tdProfit: 'border: 1px solid #dcdfe6; padding: 10px 8px; text-align: center; color: #f56c6c; font-weight: 600;',
    tdLoss: 'border: 1px solid #dcdfe6; padding: 10px 8px; text-align: center; color: #67c23a; font-weight: 600;',
    totalRow: 'background-color: #ecf5ff; border-top: 2px solid #409eff;',
    strategyRow: 'background-color: #f0f9ff; font-weight: 600; color: #409eff;',
    summary: 'font-size: 13px; color: #606266; margin: 12px 0; line-height: 1.6;',
    summarySection: 'margin-top: 24px;',
    p: 'font-size: 14px; color: #606266; margin: 12px 0; line-height: 1.8;'
  }

  // 生成表格行的函数（带策略分组和斑马纹）
  const generateTableRows = (holdings) => {
    // 预先计算总市值和各策略市值
    const totalMarketValue = holdings.reduce((sum, h) => sum + h.market_value, 0)
    const strategyMarketValues = {}

    holdings.forEach((h) => {
      const strategy = h.main_strategy || '其他'
      if (!strategyMarketValues[strategy]) {
        strategyMarketValues[strategy] = 0
      }
      strategyMarketValues[strategy] += h.market_value
    })

    let rows = ''
    let currentMainStrategy = null
    let rowIndex = 0

    holdings.forEach((h) => {
      // 标准化策略名称（null/undefined 转为 "其他"）
      const mainStrategy = h.main_strategy || '其他'

      // 检查是否需要插入策略分组行
      if (mainStrategy !== currentMainStrategy) {
        currentMainStrategy = mainStrategy
        // 计算该策略的市值占比
        const strategyValue = strategyMarketValues[mainStrategy] || 0
        const percentage = totalMarketValue > 0 ? (strategyValue / totalMarketValue * 100).toFixed(1) : '0.0'
        // 插入策略分组行（带百分比）
        rows += `<tr style="${styles.strategyRow}">`
        rows += `<td colspan="4" style="${styles.tdLeft.replace('color: #606266', 'color: #409eff')}">${mainStrategy}（${percentage}%）</td>`
        rows += '</tr>'
      }

      const isEven = rowIndex % 2 === 0
      const rowBg = isEven ? '' : 'background-color: #fafafa;'
      const pnlStyle = h.pnl >= 0 ? styles.tdProfit : styles.tdLoss
      const fundName = (h.fund_name || h.product_name || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

      rows += '<tr style="' + rowBg + '">'
      rows += `<td style="${styles.tdLeft}">${fundName}</td>`
      rows += `<td style="${styles.td}">${(h.market_value / 10000).toFixed(0)}</td>`
      rows += `<td style="${styles.td}">${h.shares.toFixed(0)}</td>`
      rows += `<td style="${pnlStyle}">${(h.pnl / 10000).toFixed(0)}</td>`
      rows += '</tr>'

      rowIndex++
    })
    return rows
  }

  // 生成HTML
  let html = `<div style="${styles.container}">`

  // 左右两列布局
  html += `<div style="${styles.tablesRow}">`

  // 左侧：年初持仓表
  html += `<div style="${styles.tableCol}">`
  html += `<h3 style="${styles.h3}">${client_info.year}年年初（${client_info.year_start}）持仓明细</h3>`
  html += `<table style="${styles.table}"><thead><tr>`
  html += `<th style="${styles.thLeft}">基金名称</th>`
  html += `<th style="${styles.th}">持仓市值（万）</th>`
  html += `<th style="${styles.th}">持仓份额</th>`
  html += `<th style="${styles.th}">持仓盈亏（万）</th>`
  html += '</tr></thead><tbody>'

  html += generateTableRows(sortedStartHoldings)

  const startPnlStyle = startTotal.pnl >= 0 ? styles.tdProfit : styles.tdLoss
  html += `<tr style="${styles.totalRow}">`
  html += `<td style="${styles.tdLeft}"><strong>合计</strong></td>`
  html += `<td style="${styles.td}"><strong>${(startTotal.marketValue / 10000).toFixed(0)}</strong></td>`
  html += `<td style="${styles.td}">-</td>`
  html += `<td style="${startPnlStyle}"><strong>${(startTotal.pnl / 10000).toFixed(0)}</strong></td>`
  html += '</tr>'
  html += '</tbody></table>'
  html += `<p style="${styles.summary}">${client_info.year}年年初持有 <strong>${startTotal.count}</strong> 只产品，合计成本 <strong>${(startTotal.cost / 10000).toFixed(0)}</strong> 万元，合计盈亏 <strong>${(startTotal.pnl / 10000).toFixed(0)}</strong> 万元</p>`
  html += '</div>'

  // 右侧：年末持仓表
  html += `<div style="${styles.tableCol}">`
  html += `<h3 style="${styles.h3}">${client_info.year}年年末（${client_info.year_end}）持仓明细</h3>`
  html += `<table style="${styles.table}"><thead><tr>`
  html += `<th style="${styles.thLeft}">基金名称</th>`
  html += `<th style="${styles.th}">持仓市值（万）</th>`
  html += `<th style="${styles.th}">持仓份额</th>`
  html += `<th style="${styles.th}">持仓盈亏（万）</th>`
  html += '</tr></thead><tbody>'

  html += generateTableRows(sortedEndHoldings)

  const endPnlStyle = endTotal.pnl >= 0 ? styles.tdProfit : styles.tdLoss
  html += `<tr style="${styles.totalRow}">`
  html += `<td style="${styles.tdLeft}"><strong>合计</strong></td>`
  html += `<td style="${styles.td}"><strong>${(endTotal.marketValue / 10000).toFixed(0)}</strong></td>`
  html += `<td style="${styles.td}">-</td>`
  html += `<td style="${endPnlStyle}"><strong>${(endTotal.pnl / 10000).toFixed(0)}</strong></td>`
  html += '</tr>'
  html += '</tbody></table>'
  html += `<p style="${styles.summary}">${client_info.year}年年末持有 <strong>${endTotal.count}</strong> 只产品，合计成本 <strong>${(endTotal.cost / 10000).toFixed(0)}</strong> 万元，合计盈亏 <strong>${(endTotal.pnl / 10000).toFixed(0)}</strong> 万元</p>`
  html += '</div>'

  html += '</div>' // 结束 holdings-tables-row

  // 持仓变动总结
  html += `<div style="${styles.summarySection}">`
  html += `<h3 style="${styles.h3}">持仓变动总结</h3>`

  if (cleared.length > 0) {
    const clearedNames = cleared.map(h => (h.fund_name || h.product_name || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')).join('、')
    const clearedPnl = cleared.reduce((sum, h) => sum + h.pnl, 0)
    const pnlColor = clearedPnl >= 0 ? '#f56c6c' : '#67c23a'
    html += `<p style="${styles.p}"><strong>清仓标的：</strong>清仓了${clearedNames}，清仓产品累计盈亏 <span style="color: ${pnlColor}; font-weight: 600;">${(clearedPnl / 10000).toFixed(0)}</span> 万元</p>`
  }

  if (reduced.length > 0) {
    const reducedNames = reduced.map(h => (h.fund_name || h.product_name || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')).join('、')
    const reducedAmount = reduced.reduce((sum, h) => sum + h.reduction, 0)
    html += `<p style="${styles.p}"><strong>部分赎回标的：</strong>部分赎回了${reducedNames}，合计赎回金额约 <strong>${(reducedAmount / 10000).toFixed(0)}</strong> 万元</p>`
  }

  if (added.length > 0) {
    const addedNames = added.map(h => (h.fund_name || h.product_name || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')).join('、')
    const addedAmount = added.reduce((sum, h) => sum + h.cost, 0)
    html += `<p style="${styles.p}"><strong>新增标的：</strong>新增了${addedNames}，合计申购金额约 <strong>${(addedAmount / 10000).toFixed(0)}</strong> 万元</p>`
  }

  if (intraYearTraded.length > 0) {
    const tradedInfo = intraYearTraded.map(p => {
      const name = (p.fund_name || p.product_name || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      const returnColor = p.year_return >= 0 ? '#f56c6c' : '#67c23a'
      return `${name}（申购 <strong>${(p.year_purchase / 10000).toFixed(0)}</strong> 万，赎回 <strong>${(p.year_redemption / 10000).toFixed(0)}</strong> 万，收益 <span style="color: ${returnColor}; font-weight: 600;">${(p.year_return / 10000).toFixed(0)}</span> 万，收益率 <span style="color: ${returnColor}; font-weight: 600;">${p.return_rate.toFixed(1)}%</span>）`
    }).join('、')
    html += `<p style="${styles.p}"><strong>年内交易产品：</strong>${tradedInfo}</p>`
  }

  html += '</div>' // 结束总结区域
  html += '</div>' // 结束容器

  return html
}

// 生命周期
onMounted(() => {
  initYears()
  // 组件挂载后等待一小段时间再加载数据，确保DOM完全准备好
  setTimeout(() => {
    if (selectedYear.value) {
      loadAnnualData()
    }
  }, 200)
})

// 监听groupId变化
watch(() => props.groupId, (newVal, oldVal) => {
  if (newVal && newVal !== oldVal && selectedYear.value) {
    loadAnnualData()
  }
})

// 组件卸载时销毁图表
import { onBeforeUnmount } from 'vue'
onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  if (strategyChartInstance) {
    strategyChartInstance.dispose()
    strategyChartInstance = null
  }
  if (waterfallChartInstance) {
    waterfallChartInstance.dispose()
    waterfallChartInstance = null
  }
  window.removeEventListener('resize', handleResize)
  window.chartResizeListenerAdded = false
})

// 窗口大小调整处理函数
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
  if (strategyChartInstance) {
    strategyChartInstance.resize()
  }
  if (waterfallChartInstance) {
    waterfallChartInstance.resize()
  }
}

// 初始化收益贡献图表
const initContributionCharts = () => {
  if (!contributionData.value) return

  // 初始化策略饼图
  initStrategyPieChart()

  // 初始化产品瀑布图
  initWaterfallChart()
}

// 初始化策略收益贡献饼图
const initStrategyPieChart = () => {
  if (!strategyChartRef.value || !contributionData.value) return

  // 销毁旧实例
  if (strategyChartInstance) {
    strategyChartInstance.dispose()
  }

  // 创建新实例
  strategyChartInstance = echarts.init(strategyChartRef.value)

  const { strategy_contribution } = contributionData.value

  // 准备饼图数据
  const pieData = strategy_contribution.map(item => ({
    name: item.strategy,
    value: item.total_return / 10000,  // 转换为万元
    percentage: item.percentage
  }))

  // 配置项
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `${params.name}<br/>收益：¥${params.value.toFixed(1)}万<br/>占比：${params.data.percentage.toFixed(1)}%`
      }
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center',
      formatter: (name) => {
        const item = pieData.find(d => d.name === name)
        return `${name}  ${item.percentage.toFixed(1)}%`
      }
    },
    color: ['#409EFF', '#67C23A', '#E6A23C', '#909399'],
    series: [
      {
        name: '策略收益',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: (params) => {
            return `${params.name}\n¥${params.value.toFixed(1)}万`
          }
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        data: pieData
      }
    ]
  }

  strategyChartInstance.setOption(option)
}

// 初始化产品收益瀑布图
const initWaterfallChart = () => {
  if (!waterfallChartRef.value || !contributionData.value) return

  // 销毁旧实例
  if (waterfallChartInstance) {
    waterfallChartInstance.dispose()
  }

  // 创建新实例
  waterfallChartInstance = echarts.init(waterfallChartRef.value)

  const { product_contribution } = contributionData.value

  // 计算总收益
  const totalReturn = product_contribution.reduce((sum, p) => sum + p.year_return, 0) / 10000

  // 准备产品数据：按收益金额排序（正收益从大到小，负收益从小到大）
  const sortedProducts = [...product_contribution]
    .sort((a, b) => {
      const aReturn = a.year_return
      const bReturn = b.year_return
      // 正收益在前，负收益在后
      if (aReturn > 0 && bReturn > 0) return bReturn - aReturn  // 正收益从大到小
      if (aReturn < 0 && bReturn < 0) return aReturn - bReturn  // 负收益从小到大（绝对值大的在前）
      return bReturn - aReturn  // 正收益排在负收益前面
    })
    .slice(0, 15)  // 显示前15个产品

  // 构建瀑布图数据
  const categories = []
  const displayData = []  // 显示的柱子高度
  const baseData = []     // 基准位置（柱子起点）
  const colors = []       // 颜色数组
  const tooltipData = []  // tooltip数据

  let cumulative = 0  // 累计值

  // 起点柱：总收益
  categories.push('总收益')
  displayData.push(totalReturn)
  baseData.push(0)
  colors.push('#2C3E50')  // 深灰色
  tooltipData.push({
    name: '总收益',
    value: totalReturn,
    percentage: 100,
    fullName: '年度总收益'
  })
  cumulative = totalReturn

  // 中间产品柱
  sortedProducts.forEach(product => {
    const productReturn = product.year_return / 10000
    const productName = product.fund_name || product.product_name || '未知产品'
    const shortName = productName.length > 10 ? productName.substring(0, 10) + '...' : productName
    const percentage = totalReturn !== 0 ? (productReturn / totalReturn * 100) : 0

    categories.push(shortName)

    // 正收益：柱子从累计值向上
    // 负收益：柱子从累计值向下
    if (productReturn >= 0) {
      displayData.push(productReturn)
      baseData.push(cumulative - productReturn)
      colors.push('#2BB673')  // 绿色
    } else {
      displayData.push(-productReturn)  // 显示正值，但从上往下
      baseData.push(cumulative)
      colors.push('#E74C3C')  // 红色
    }

    tooltipData.push({
      name: shortName,
      value: productReturn,
      percentage: percentage,
      fullName: productName,
      strategy: product.main_strategy || '未知',
      returnRate: product.return_rate
    })

    cumulative -= productReturn
  })

  // 终点柱：累计收益（应该接近0或就是总收益）
  categories.push('累计')
  displayData.push(Math.abs(cumulative))
  baseData.push(Math.min(cumulative, 0))
  colors.push('#34495E')  // 深蓝色
  tooltipData.push({
    name: '累计',
    value: cumulative,
    percentage: (cumulative / totalReturn * 100),
    fullName: '最终累计收益'
  })

  // 构建连接线数据
  const lineData = []
  let previousTop = totalReturn
  for (let i = 1; i < categories.length - 1; i++) {
    const currentBase = baseData[i]
    const currentDisplay = displayData[i]
    const currentTop = currentBase + (colors[i] === '#E74C3C' ? -currentDisplay : currentDisplay)

    lineData.push({
      xAxis: i - 1,
      yAxis: previousTop
    })
    lineData.push({
      xAxis: i,
      yAxis: previousTop
    })

    previousTop = currentTop
  }

  // 计算Y轴的合适范围
  const allValues = [...displayData, ...baseData.map((base, idx) => base + displayData[idx])]
  const minValue = Math.min(...allValues, 0)
  const maxValue = Math.max(...allValues, 0)
  const range = maxValue - minValue
  const yAxisMin = Math.floor(minValue - range * 0.1)
  const yAxisMax = Math.ceil(maxValue + range * 0.1)

  // 配置项
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const stackData = params.find(p => p.seriesName === '收益基准')
        const barData = params.find(p => p.seriesName === '产品收益')

        if (!barData) return ''

        const dataIndex = barData.dataIndex
        const data = tooltipData[dataIndex]

        let result = `<strong>${data.fullName}</strong><br/>`
        result += `收益金额：${data.value >= 0 ? '+' : ''}${data.value.toFixed(1)} 万元<br/>`
        result += `占比：${data.percentage.toFixed(1)}%<br/>`
        if (data.strategy) {
          result += `策略：${data.strategy}<br/>`
        }
        if (data.returnRate !== undefined) {
          result += `收益率：${data.returnRate.toFixed(1)}%`
        }

        return result
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '12%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        interval: 0,
        rotate: 45,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      name: '收益贡献金额（万元）',
      min: yAxisMin,
      max: yAxisMax,
      axisLabel: {
        formatter: '{value}'
      },
      splitLine: {
        show: true,
        lineStyle: {
          type: 'dashed',
          color: '#E5E5E5'
        }
      }
    },
    series: [
      // 隐藏的基准系列（用于堆叠）
      {
        name: '收益基准',
        type: 'bar',
        stack: 'total',
        itemStyle: {
          borderColor: 'transparent',
          color: 'transparent'
        },
        emphasis: {
          itemStyle: {
            borderColor: 'transparent',
            color: 'transparent'
          }
        },
        data: baseData,
        silent: true
      },
      // 显示的柱子系列
      {
        name: '产品收益',
        type: 'bar',
        stack: 'total',
        barWidth: '50%',
        data: displayData.map((val, idx) => ({
          value: val,
          itemStyle: {
            color: colors[idx],
            borderRadius: idx === 0 || idx === displayData.length - 1 ? [4, 4, 4, 4] : [4, 4, 0, 0]
          }
        })),
        label: {
          show: true,
          position: (params) => {
            const dataIndex = params.dataIndex
            const data = tooltipData[dataIndex]
            // 正收益标签在上方，负收益标签在下方
            return data.value >= 0 ? 'top' : 'bottom'
          },
          formatter: (params) => {
            const dataIndex = params.dataIndex
            const data = tooltipData[dataIndex]
            const value = data.value
            const percentage = data.percentage

            // 格式化显示
            const valueStr = `${value >= 0 ? '+' : ''}${value.toFixed(1)}`
            const percentStr = `${percentage.toFixed(0)}%`

            return `${valueStr}\n${percentStr}`
          },
          fontSize: 11,
          fontWeight: 'bold',
          color: (params) => {
            const dataIndex = params.dataIndex
            const data = tooltipData[dataIndex]
            // 正收益红色，负收益绿色
            return data.value >= 0 ? '#E74C3C' : '#2BB673'
          },
          lineHeight: 16
        }
      },
      // 连接线系列
      {
        name: '连接线',
        type: 'line',
        markLine: {
          symbol: 'none',
          lineStyle: {
            type: 'dashed',
            color: '#BFBFBF',
            width: 1
          },
          data: lineData,
          silent: true
        }
      }
    ]
  }

  waterfallChartInstance.setOption(option)
}
</script>

<style scoped>
.annual-review {
  padding: 0;
}

.year-selector-card {
  margin-bottom: 20px;
}

.selector-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
}

.selector-label {
  font-weight: 500;
  font-size: 14px;
  color: #606266;
}

.loading-container {
  padding: 20px;
}

.summary-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
  font-size: 16px;
}

.summary-item {
  text-align: center;
  padding: 16px;
}

.summary-item .label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.summary-item .value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.summary-item .sub-value {
  font-size: 14px;
  font-weight: normal;
  margin-left: 8px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 500px;
}

.holdings-change-card {
  margin-bottom: 20px;
}

.holdings-analysis-content {
  padding: 16px;
}

.holdings-tables-row {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.holdings-table-col {
  flex: 1;
  min-width: 0;
}

.holdings-analysis h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.holdings-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
  font-size: 13px;
}

.holdings-table th,
.holdings-table td {
  border: 1px solid #ebeef5;
  padding: 10px 6px;
  text-align: center;
}

.holdings-table th {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #606266;
  font-size: 12px;
}

.holdings-table td {
  color: #606266;
}

.holdings-table td:first-child {
  text-align: left;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.holdings-table .total-row {
  background-color: #fafafa;
  font-weight: 600;
}

.holdings-table .profit {
  color: #f56c6c;
  font-weight: 600;
}

.holdings-table .loss {
  color: #67c23a;
  font-weight: 600;
}

.holdings-analysis .summary {
  font-size: 13px;
  color: #606266;
  margin: 12px 0;
  line-height: 1.6;
}

.holdings-analysis p {
  font-size: 14px;
  color: #606266;
  margin: 12px 0;
  line-height: 1.8;
}

.holdings-analysis p strong {
  color: #303133;
  font-weight: 600;
}

.holdings-analysis p .profit {
  color: #f56c6c;
  font-weight: 600;
}

.holdings-analysis p .loss {
  color: #67c23a;
  font-weight: 600;
}

.details-card {
  margin-bottom: 20px;
}

.quarter-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 40px;
}

.quarter-name {
  font-weight: 500;
  font-size: 15px;
}

.quarter-stats {
  font-size: 14px;
  color: #606266;
}

/* 金额样式 - 红涨绿跌 */
.money-text {
  font-weight: 500;
}

.profit-text {
  color: #f56c6c;  /* 红色表示正收益（赚钱） */
  font-weight: 600;
}

.loss-text {
  color: #67c23a;  /* 绿色表示负收益（亏钱） */
  font-weight: 600;
}

.dividend-text {
  color: #e6a23c;  /* 橙色表示分红 */
  font-weight: 500;
}

.cashflow-out {
  color: #e6a23c;
}

.cashflow-in {
  color: #409eff;
}

/* 年度收益分析图表卡片 */
.contribution-charts-card {
  margin-bottom: 20px;
}

.chart-container {
  padding: 16px;
}

.chart-title {
  text-align: center;
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 16px;
}

.chart {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .selector-wrapper {
    flex-direction: column;
    align-items: stretch;
  }

  .chart-container {
    height: 400px;
  }

  .quarter-title {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
