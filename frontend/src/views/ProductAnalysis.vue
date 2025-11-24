<template>
  <div class="product-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>产品分析</h2>
      <p class="page-description">产品全维度指标分析与风险评估</p>
    </div>

    <!-- 产品选择 -->
    <el-card class="filter-section">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select
            v-model="selectedFundCode"
            placeholder="选择产品"
            filterable
            clearable
            style="width: 100%"
            @change="loadProductAnalysis"
          >
            <el-option
              v-for="fund in fundList"
              :key="fund.fund_code"
              :label="`${fund.fund_code} - ${fund.fund_name}`"
              :value="fund.fund_code"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadProductAnalysis" :loading="loading">
            <el-icon><Search /></el-icon>
            分析
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 基础指标卡片 -->
    <el-row :gutter="24" class="stats-section" v-if="analysisData">
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="累计收益率"
            :value="analysisData.basic_metrics.cumulative_return"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon :style="`color: ${analysisData.basic_metrics.cumulative_return >= 0 ? '#f56c6c' : '#67c23a'}`">
                <TrendCharts />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="年化收益率"
            :value="analysisData.basic_metrics.annualized_return"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><DataLine /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="最大回撤"
            :value="analysisData.basic_metrics.max_drawdown"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon style="color: #e6a23c"><Bottom /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="波动率"
            :value="analysisData.basic_metrics.volatility"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon style="color: #909399"><Grid /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="夏普比率"
            :value="analysisData.basic_metrics.sharpe_ratio"
            :precision="2"
          >
            <template #prefix>
              <el-icon style="color: #67c23a"><Histogram /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="卡玛比率"
            :value="analysisData.basic_metrics.calmar_ratio"
            :precision="2"
          >
            <template #prefix>
              <el-icon style="color: #f56c6c"><Trophy /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="24" v-if="analysisData">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>净值走势与回撤</span>
            </div>
          </template>
          <div ref="navChartRef" style="width: 100%; height: 600px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 持有期分析 -->
    <el-row :gutter="24" v-if="analysisData">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>持有期收益分析</span>
              <el-tag>任意时间买入持有</el-tag>
            </div>
          </template>
          <el-table :data="analysisData.holding_period_analysis" border stripe>
            <el-table-column prop="period" label="持有期" align="center" />
            <el-table-column prop="sample_count" label="样本数" align="center" />
            <el-table-column label="盈利概率" align="center">
              <template #default="scope">
                <span class="percent-text" :style="`color: ${scope.row.profit_probability >= 50 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.profit_probability.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="平均收益" align="center">
              <template #default="scope">
                <span class="percent-text" :style="`color: ${scope.row.avg_return >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.avg_return >= 0 ? '+' : '' }}{{ scope.row.avg_return.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="最佳收益" align="center">
              <template #default="scope">
                <span class="percent-text" style="color: #f56c6c">
                  +{{ scope.row.max_return.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="最差收益" align="center">
              <template #default="scope">
                <span class="percent-text" style="color: #67c23a">
                  {{ scope.row.min_return.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 月度收益分析 -->
    <el-row :gutter="24" v-if="analysisData" align="stretch">
      <el-col :span="16">
        <el-card class="monthly-card">
          <template #header>
            <div class="card-header">
              <span>月度收益分布</span>
            </div>
          </template>
          <div ref="monthlyReturnChartRef" style="width: 100%; height: 450px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="monthly-card">
          <template #header>
            <div class="card-header">
              <span>月度胜率统计</span>
            </div>
          </template>
          <div class="monthly-stats">
            <el-statistic
              title="月度胜率"
              :value="analysisData.monthly_stats.win_rate"
              :precision="2"
              suffix="%"
            >
              <template #prefix>
                <el-icon style="color: #409eff"><TrendCharts /></el-icon>
              </template>
            </el-statistic>
            <el-divider />
            <el-row :gutter="16">
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">上涨月份</div>
                  <div class="value positive">{{ analysisData.monthly_stats.positive_months }}个</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">下跌月份</div>
                  <div class="value negative">{{ analysisData.monthly_stats.negative_months }}个</div>
                </div>
              </el-col>
            </el-row>
            <el-divider />
            <el-row :gutter="16">
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">最佳月度</div>
                  <div class="value positive">+{{ analysisData.monthly_stats.best_month.toFixed(2) }}%</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">最差月度</div>
                  <div class="value negative">{{ analysisData.monthly_stats.worst_month.toFixed(2) }}%</div>
                </div>
              </el-col>
            </el-row>
            <el-divider />
            <el-row :gutter="16">
              <el-col :span="24">
                <div class="mini-stat">
                  <div class="label">平均月度收益</div>
                  <div class="value" :class="analysisData.monthly_stats.avg_monthly_return >= 0 ? 'positive' : 'negative'">
                    {{ analysisData.monthly_stats.avg_monthly_return >= 0 ? '+' : '' }}{{ analysisData.monthly_stats.avg_monthly_return.toFixed(2) }}%
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 风险指标 -->
    <el-row :gutter="24" v-if="analysisData">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>风险指标详情</span>
            </div>
          </template>
          <el-row :gutter="24">
            <el-col :span="6">
              <div class="risk-item">
                <div class="risk-label">下行风险</div>
                <div class="risk-value">{{ analysisData.risk_metrics.downside_deviation.toFixed(2) }}%</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="risk-item">
                <div class="risk-label">索提诺比率</div>
                <div class="risk-value">{{ analysisData.risk_metrics.sortino_ratio.toFixed(2) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="risk-item">
                <div class="risk-label">最大连续下跌天数</div>
                <div class="risk-value">{{ analysisData.risk_metrics.max_consecutive_loss_days }}天</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="risk-item">
                <div class="risk-label">VAR(95%)</div>
                <div class="risk-value">{{ analysisData.risk_metrics.var_95.toFixed(2) }}%</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-if="!analysisData && !loading" description="请选择产品进行分析" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const loading = ref(false)
const selectedFundCode = ref('')
const fundList = ref([])
const analysisData = ref(null)
const navChartRef = ref(null)
const monthlyReturnChartRef = ref(null)
let navChart = null
let monthlyReturnChart = null

onMounted(() => {
  loadFundList()
})

const loadFundList = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/nav/funds`)
    fundList.value = response.data.data.funds
  } catch (error) {
    ElMessage.error('加载产品列表失败')
  }
}

const loadProductAnalysis = async () => {
  if (!selectedFundCode.value) {
    ElMessage.warning('请选择产品')
    return
  }

  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/product-analysis/${selectedFundCode.value}`)
    analysisData.value = response.data.data

    await nextTick()
    renderNavChart()
    renderMonthlyReturnChart()

    ElMessage.success('分析完成')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '分析失败')
  } finally {
    loading.value = false
  }
}

const renderNavChart = () => {
  if (!navChartRef.value || !analysisData.value) return

  if (navChart) {
    navChart.dispose()
  }

  navChart = echarts.init(navChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['净值', '回撤']
    },
    grid: [
      {
        left: '3%',
        right: '4%',
        top: '5%',
        height: '35%'
      },
      {
        left: '3%',
        right: '4%',
        top: '60%',
        height: '35%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: analysisData.value.nav_curve.dates,
        gridIndex: 0
      },
      {
        type: 'category',
        data: analysisData.value.nav_curve.dates,
        gridIndex: 1,
        position: 'top',
        axisLine: { onZero: false }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '净值',
        gridIndex: 0,
        min: (value) => {
          // 动态计算最小值，确保从合理位置开始
          const minVal = Math.floor(value.min * 10) / 10
          return Math.max(0.4, minVal - 0.1)
        },
        scale: true,
        axisLabel: {
          formatter: (value) => value.toFixed(1)
        }
      },
      {
        type: 'value',
        name: '回撤(%)',
        gridIndex: 1,
        max: 0,
        axisLabel: {
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '净值',
        type: 'line',
        data: analysisData.value.nav_curve.values,
        smooth: true,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '回撤',
        type: 'line',
        data: analysisData.value.nav_curve.drawdowns,
        smooth: true,
        xAxisIndex: 1,
        yAxisIndex: 1,
        areaStyle: {
          color: '#67C23A',
          opacity: 0.3
        },
        itemStyle: {
          color: '#67C23A'
        },
        lineStyle: {
          color: '#67C23A'
        }
      }
    ]
  }

  navChart.setOption(option)
}

const renderMonthlyReturnChart = () => {
  if (!monthlyReturnChartRef.value || !analysisData.value) return

  if (monthlyReturnChart) {
    monthlyReturnChart.dispose()
  }

  monthlyReturnChart = echarts.init(monthlyReturnChartRef.value)

  const monthlyData = analysisData.value.monthly_returns
  const colors = monthlyData.returns.map(val => val >= 0 ? '#F56C6C' : '#67C23A')

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const value = params[0].value
        return `${params[0].axisValue}<br/>收益率: ${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: monthlyData.months,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '收益率(%)',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '月度收益',
        type: 'bar',
        data: monthlyData.returns,
        itemStyle: {
          color: (params) => {
            return params.value >= 0 ? '#F56C6C' : '#67C23A'
          }
        }
      }
    ]
  }

  monthlyReturnChart.setOption(option)
}
</script>

<style scoped>
.product-analysis {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.page-description {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.filter-section {
  margin-bottom: 24px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.chart-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.monthly-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.monthly-stats {
  padding: 20px;
}

.mini-stat {
  text-align: center;
  padding: 10px 0;
}

.mini-stat .label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.mini-stat .value {
  font-size: 20px;
  font-weight: 600;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.mini-stat .value.positive {
  color: #f56c6c;
}

.mini-stat .value.negative {
  color: #67c23a;
}

.risk-item {
  text-align: center;
  padding: 20px;
  background-color: #f9fafb;
  border-radius: 8px;
}

.risk-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.risk-value {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.percent-text {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}
</style>
