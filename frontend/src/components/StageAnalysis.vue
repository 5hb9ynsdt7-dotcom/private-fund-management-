<template>
  <div class="stage-analysis">
    <!-- 收益趋势图表 -->
    <div class="charts-section" v-loading="trendLoading">
      <!-- 刷新按钮 -->
      <div class="charts-header">
        <el-button @click="refreshTrendData" size="small" :loading="trendLoading">
          <el-icon><Refresh /></el-icon>
          刷新图表数据
        </el-button>
      </div>
      
      <el-row :gutter="24">
        <!-- 月度绝对收益图表 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <div class="chart-container" ref="profitChartContainer" style="height: 450px;"></div>
          </el-card>
        </el-col>
        
        <!-- 累计绝对收益图表 -->
        <el-col :span="12">
          <el-card class="chart-card">
            <div class="chart-container" ref="cumulativeReturnChartContainer" style="height: 450px;"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 月度胜率显示 -->
      <div class="monthly-win-rate" v-if="monthlyWinRate !== null">
        <div class="win-rate-text">
          月度胜率为：<span class="win-rate-value">{{ monthlyWinRate.toFixed(2) }}%</span>
          <span class="win-rate-detail">（{{ positiveMonths }}/{{ totalMonths }}）</span>
        </div>
      </div>
    </div>

    <!-- 时间段收益分析器 -->
    <el-card class="analyzer-card">
      <template #header>
        <div class="card-header">
          <span>时间段收益分析器</span>
        </div>
      </template>
      
      <!-- 时间选择器 -->
      <div class="time-selector">
        <el-row :gutter="24">
          <el-col :span="12">
            <div class="selector-group">
              <el-date-picker
                v-model="periodDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
                @change="onDateRangeChange"
              />
            </div>
          </el-col>
          <el-col :span="12">
            <div class="preset-buttons">
              <el-button-group>
                <el-button @click="setPresetPeriod('3months')" size="small">近3个月</el-button>
                <el-button @click="setPresetPeriod('ytd')" size="small">今年以来</el-button>
                <el-button @click="setPresetPeriod('1year')" size="small">近1年</el-button>
                <el-button @click="setPresetPeriod('all')" size="small">全部时间</el-button>
              </el-button-group>
              <el-button 
                type="primary" 
                @click="calculatePeriodAnalysis" 
                :loading="periodLoading"
                :disabled="!periodDateRange || periodDateRange.length !== 2"
                style="margin-left: 12px;"
              >
                计算分析
              </el-button>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 分析结果 -->
      <div v-if="periodAnalysis" class="analysis-results">
        <!-- 概要卡片 -->
        <div class="summary-cards" style="margin-top: 24px;">
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="summary-card">
                <div class="label">时间段总收益</div>
                <div class="value profit-text" :style="{ color: periodAnalysis.total_return >= 0 ? '#f56c6c' : '#67c23a' }">
                  {{ formatMoney(periodAnalysis.total_return) }}
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card">
                <div class="label">期初总市值</div>
                <div class="value">{{ formatMoney(periodAnalysis.total_start_value) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card">
                <div class="label">期末总市值</div>
                <div class="value">{{ formatMoney(periodAnalysis.total_end_value) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-card">
                <div class="label">总收益率</div>
                <div class="value profit-text" :style="{ color: periodAnalysis.total_return >= 0 ? '#f56c6c' : '#67c23a' }">
                  {{ formatPercent(periodAnalysis.total_return_rate) }}
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 产品明细表格 -->
        <div class="product-details" style="margin-top: 24px;">
          <el-table 
            :data="productDetails" 
            stripe 
            style="width: 100%"
            :default-sort="{prop: 'period_return', order: 'descending'}"
          >
            <el-table-column prop="fund_name" label="产品名称" min-width="200">
              <template #default="{ row }">
                <div class="product-info">
                  <div class="product-name">{{ row.fund_name || row.product_name || row.product_code }}</div>
                  <div class="product-code" v-if="row.product_code">{{ row.product_code }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="sub_strategy" label="细分策略" width="120">
              <template #default="{ row }">
                {{ row.sub_strategy || row.main_strategy || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="start_market_value" label="期初市值" width="120" align="right">
              <template #default="{ row }">
                <span class="money-text">{{ formatMoney(row.start_market_value) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="end_market_value" label="期末市值" width="120" align="right">
              <template #default="{ row }">
                <span class="money-text">{{ formatMoney(row.end_market_value) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="period_return" label="期间收益" width="120" align="right" sortable>
              <template #default="{ row }">
                <span class="profit-text" :style="{ color: row.period_return >= 0 ? '#f56c6c' : '#67c23a' }">
                  {{ formatMoney(row.period_return) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="return_contribution" label="收益占比" width="100" align="right">
              <template #default="{ row }">
                <span class="percent-text">{{ formatPercent(row.return_contribution) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-empty description="请选择分析时间段并点击计算分析" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import request from '@/api/index'

// Props
const props = defineProps({
  groupId: {
    type: String,
    required: true
  }
})

// Reactive data
const trendLoading = ref(false)
const periodLoading = ref(false)
const profitChart = ref(null)
const cumulativeReturnChart = ref(null)
const profitChartContainer = ref(null)
const cumulativeReturnChartContainer = ref(null)
const periodDateRange = ref([])
const periodAnalysis = ref(null)
const productDetails = ref([])
const monthlyTrendData = ref([])

// 月度胜率相关数据
const monthlyWinRate = ref(null)
const positiveMonths = ref(0)
const totalMonths = ref(0)

// 获取月度收益趋势数据
const fetchMonthlyTrend = async () => {
  trendLoading.value = true
  try {
    const data = await request.get(`/api/transaction/clients/${props.groupId}/monthly-profit-trend`)
    monthlyTrendData.value = data.monthly_trend || []
    
    // 计算月度胜率
    calculateMonthlyWinRate()
    
    // 重新渲染图表
    await nextTick()
    renderTrendCharts()
    
  } catch (error) {
    console.error('获取月度收益趋势失败:', error)
    ElMessage.error('获取月度收益趋势失败')
  } finally {
    trendLoading.value = false
  }
}

// 计算月度胜率
const calculateMonthlyWinRate = () => {
  if (!monthlyTrendData.value || monthlyTrendData.value.length === 0) {
    monthlyWinRate.value = null
    positiveMonths.value = 0
    totalMonths.value = 0
    return
  }
  
  let positiveCount = 0
  const totalCount = monthlyTrendData.value.length
  
  monthlyTrendData.value.forEach(item => {
    // 使用正确的字段名 monthly_return
    const monthlyReturn = parseFloat(item.monthly_return || 0)
    
    if (monthlyReturn > 0) {
      positiveCount++
    }
  })
  
  positiveMonths.value = positiveCount
  totalMonths.value = totalCount
  monthlyWinRate.value = totalCount > 0 ? (positiveCount / totalCount) * 100 : 0
}

// 渲染收益趋势图表
const renderTrendCharts = () => {
  if (!profitChartContainer.value || !cumulativeReturnChartContainer.value || !monthlyTrendData.value.length) return
  
  // 销毁现有图表
  if (profitChart.value) {
    profitChart.value.dispose()
  }
  if (cumulativeReturnChart.value) {
    cumulativeReturnChart.value.dispose()
  }
  
  // 初始化图表
  profitChart.value = echarts.init(profitChartContainer.value)
  cumulativeReturnChart.value = echarts.init(cumulativeReturnChartContainer.value)
  
  const months = monthlyTrendData.value.map(item => item.year_month)
  const monthlyReturns = monthlyTrendData.value.map(item => item.monthly_return)
  const cumulativeReturns = monthlyTrendData.value.map(item => item.cumulative_return || 0)
  const investmentScale = monthlyTrendData.value.map(item => item.month_end_value || 0)
  
  // 计算左轴和右轴的数据范围以对齐0点
  const leftMin = Math.min(...cumulativeReturns, 0)
  const leftMax = Math.max(...cumulativeReturns, 0)
  const rightMax = Math.max(...investmentScale, 0)
  
  // 计算对齐0点所需的比例
  const leftRange = leftMax - leftMin
  const rightRange = rightMax
  
  // 计算右轴的最小值，使两轴0点对齐
  const rightMin = rightMax > 0 ? -(rightMax * Math.abs(leftMin) / (leftMax || 1)) : 0
  
  // 月度收益图表配置
  const profitOption = {
    title: {
      text: '月度绝对收益',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = `<div style="margin-bottom: 5px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          const value = formatMoney(param.value)
          const color = param.value >= 0 ? '#f56c6c' : '#67c23a'
          result += `<div><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>月度收益: ${value}</div>`
        })
        return result
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '收益金额(元)',
      axisLabel: {
        formatter: value => formatMoneyShort(value)
      }
    },
    series: [
      {
        name: '月度收益',
        type: 'bar',
        data: monthlyReturns,
        itemStyle: {
          color: function(params) {
            return params.value >= 0 ? '#f56c6c' : '#67c23a'
          }
        }
      }
    ]
  }
  
  // 累计绝对收益图表配置
  const cumulativeReturnOption = {
    title: {
      text: '累计绝对收益',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = `<div style="margin-bottom: 5px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          if (param.seriesName === '累计绝对收益') {
            const value = formatMoney(param.value)
            const color = param.value >= 0 ? '#f56c6c' : '#67c23a'  // 正收益红色，负收益绿色
            result += `<div><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${color};"></span>累计收益: ${value}</div>`
          } else if (param.seriesName === '投资规模') {
            const value = formatMoney(param.value)
            result += `<div><span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:#c0c4cc;"></span>投资规模: ${value}</div>`
          }
        })
        return result
      }
    },
    legend: {
      data: ['累计绝对收益', '投资规模'],
      top: '8%'
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '15%',
      top: '25%',
      containLabel: true,
      show: true,
      borderWidth: 0
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '累计收益(元)',
        position: 'left',
        min: leftMin,
        max: leftMax,
        splitNumber: 5,
        axisLabel: {
          formatter: value => formatMoneyShort(value)
        },
        axisLine: {
          lineStyle: {
            color: '#409eff'
          }
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: '#e6e6e6',
            width: 1,
            type: 'solid'
          }
        }
      },
      {
        type: 'value',
        name: '',
        position: 'right',
        min: rightMin,
        max: rightMax,
        splitNumber: 5,
        axisLabel: {
          formatter: value => formatMoneyShort(value)
        },
        axisLine: {
          lineStyle: {
            color: '#909399'
          }
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '零基准线',
        type: 'line',
        yAxisIndex: 0,
        data: months.map(() => 0),
        lineStyle: {
          type: 'dashed',
          color: '#909399',
          width: 2
        },
        itemStyle: {
          opacity: 0
        },
        showSymbol: false,
        silent: true
      },
      {
        name: '累计绝对收益',
        type: 'line',
        yAxisIndex: 0,
        data: cumulativeReturns,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,  // 使用小一点的点
        itemStyle: {
          color: function(params) {
            return params.value >= 0 ? '#f56c6c' : '#67c23a'  // 正收益红色，负收益绿色
          }
        },
        lineStyle: {
          width: 2,
          color: '#409eff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.2)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ]
          }
        }
      },
      {
        name: '投资规模',
        type: 'bar',
        yAxisIndex: 1,
        data: investmentScale,
        itemStyle: {
          color: 'rgba(192, 196, 204, 0.6)'
        },
        barWidth: '60%'
      }
    ]
  }
  
  profitChart.value.setOption(profitOption)
  cumulativeReturnChart.value.setOption(cumulativeReturnOption)
}

// 设置预设时间段
const setPresetPeriod = (preset) => {
  const now = new Date()
  const today = now.toISOString().split('T')[0]
  
  switch (preset) {
    case '3months':
      const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate())
      periodDateRange.value = [threeMonthsAgo.toISOString().split('T')[0], today]
      break
    case 'ytd':
      const yearStart = new Date(now.getFullYear(), 0, 1)
      periodDateRange.value = [yearStart.toISOString().split('T')[0], today]
      break
    case '1year':
      const oneYearAgo = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
      periodDateRange.value = [oneYearAgo.toISOString().split('T')[0], today]
      break
    case 'all':
      // 设置为很早的日期到今天
      periodDateRange.value = ['2020-01-01', today]
      break
  }
}

// 计算时间段收益分析
const calculatePeriodAnalysis = async () => {
  if (!periodDateRange.value || periodDateRange.value.length !== 2) {
    ElMessage.warning('请选择分析时间段')
    return
  }
  
  periodLoading.value = true
  try {
    const [startDate, endDate] = periodDateRange.value
    const data = await request.get(
      `/api/transaction/clients/${props.groupId}/period-profit-analysis?start_date=${startDate}&end_date=${endDate}`
    )
    
    periodAnalysis.value = data.period_analysis
    productDetails.value = data.product_details || []
    
    ElMessage.success('分析计算完成')
    
  } catch (error) {
    console.error('时间段收益分析失败:', error)
    ElMessage.error('时间段收益分析失败')
  } finally {
    periodLoading.value = false
  }
}

// 日期范围变化处理
const onDateRangeChange = (value) => {
  if (value && value.length === 2) {
    // 可以添加自动计算或其他逻辑
  }
}

// 刷新趋势数据
const refreshTrendData = () => {
  fetchMonthlyTrend()
}

// 工具函数
const formatMoney = (value) => {
  if (value === null || value === undefined) return '0.00'
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatMoneyShort = (value) => {
  if (Math.abs(value) >= 100000000) {
    return (value / 100000000).toFixed(1) + '亿'
  } else if (Math.abs(value) >= 10000) {
    return (value / 10000).toFixed(1) + '万'
  }
  return value.toFixed(0)
}

const formatPercent = (value) => {
  if (value === null || value === undefined) return '0.00%'
  return Number(value).toFixed(2) + '%'
}

const getProfitClass = (value) => {
  if (value > 0) return 'profit'
  if (value < 0) return 'loss'
  return ''
}

// 生命周期
onMounted(() => {
  fetchMonthlyTrend()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    if (profitChart.value) {
      profitChart.value.resize()
    }
    if (cumulativeReturnChart.value) {
      cumulativeReturnChart.value.resize()
    }
  })
})

onUnmounted(() => {
  if (profitChart.value) {
    profitChart.value.dispose()
  }
  if (cumulativeReturnChart.value) {
    cumulativeReturnChart.value.dispose()
  }
  window.removeEventListener('resize', () => {})
})
</script>

<style scoped>
.stage-analysis {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.charts-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-card, .analyzer-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.time-selector {
  margin-bottom: 24px;
}

.selector-group {
  display: flex;
  align-items: center;
}

.preset-buttons {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.summary-cards {
  display: flex;
  gap: 16px;
}

.summary-card {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  flex: 1;
}

.summary-card .label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.summary-card .value {
  font-size: 20px;
  font-weight: 600;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.product-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.product-name {
  font-weight: 500;
  color: #303133;
}

.product-code {
  font-size: 12px;
  color: #909399;
}

.money-text, .percent-text, .profit-text {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif !important;
  font-weight: 500;
}

.profit-text.profit {
  color: #67c23a;
}

.profit-text.loss {
  color: #f56c6c;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.monthly-win-rate {
  text-align: center;
  margin-top: 16px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.win-rate-text {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.win-rate-value {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
  margin: 0 8px;
}

.win-rate-detail {
  font-size: 14px;
  color: #909399;
  margin-left: 8px;
}
</style>