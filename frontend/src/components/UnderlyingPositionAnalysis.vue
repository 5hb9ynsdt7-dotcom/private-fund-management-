<template>
  <div class="underlying-analysis">
    <el-card class="analysis-card">
      <template #header>
        <div class="analysis-header">
          <h3>底层持仓分析（主观）</h3>
          <span class="analysis-subtitle">穿透分析客户持有的主观多头及股债混合产品的底层资产配置</span>
        </div>
      </template>
      
      <div v-loading="loading">
        <div v-if="error" class="error-state">
          <el-alert
            :title="error"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
        
        <div v-else-if="analysisData" class="analysis-content">
          <!-- 分析说明 -->
          <div class="analysis-info">
            <el-tag type="info" size="small">
              分析了{{ analysisData.analyzed_positions }}个主观产品，共{{ analysisData.total_positions }}个持仓
            </el-tag>
            <span class="total-value">
              底层资产总市值：<strong>{{ formatCurrency(analysisData.asset_distribution.total_value) }}</strong>
            </span>
          </div>
          
          <!-- 图表区域 -->
          <el-row :gutter="24" class="charts-row">
            <!-- 资产类别分布饼图 -->
            <el-col :span="12">
              <div class="chart-container">
                <h4 class="chart-title">底层资产类别分布</h4>
                <div ref="assetChartRef" class="chart" style="height: 350px;"></div>
              </div>
            </el-col>
            
            <!-- 行业分布柱状图 -->
            <el-col :span="12">
              <div class="chart-container">
                <h4 class="chart-title">底层行业分布</h4>
                <div ref="industryChartRef" class="chart" style="height: 350px;"></div>
              </div>
            </el-col>
          </el-row>
          
          <!-- 详细数据表格 -->
          <div class="data-tables">
            <el-row :gutter="24">
              <!-- 资产分布表 -->
              <el-col :span="12">
                <h4 class="table-title">资产类别详情</h4>
                <el-table 
                  :data="Array.from(analysisData.asset_distribution.data)" 
                  size="small"
                  :max-height="200"
                >
                  <el-table-column prop="name" label="资产类别" width="120" />
                  <el-table-column prop="value" label="市值" align="right">
                    <template #default="scope">
                      {{ formatCurrency(scope.row.value) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="percentage" label="占比" align="right" width="80">
                    <template #default="scope">
                      {{ scope.row.percentage ? scope.row.percentage.toFixed(1) : '0.0' }}%
                    </template>
                  </el-table-column>
                </el-table>
              </el-col>
              
              <!-- 行业分布表 -->
              <el-col :span="12">
                <h4 class="table-title">行业分布详情</h4>
                <el-table 
                  :data="Array.from(analysisData.industry_distribution.data)" 
                  size="small"
                  :max-height="200"
                >
                  <el-table-column prop="name" label="行业" width="120" />
                  <el-table-column prop="value" label="市值" align="right">
                    <template #default="scope">
                      {{ formatCurrency(scope.row.value) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="percentage" label="占比" align="right" width="80">
                    <template #default="scope">
                      {{ scope.row.percentage ? scope.row.percentage.toFixed(1) : '0.0' }}%
                    </template>
                  </el-table-column>
                </el-table>
              </el-col>
            </el-row>
          </div>
          
          <!-- 产品清单 -->
          <div class="product-list-section" v-if="analysisData.product_list && analysisData.product_list.length > 0">
            <h4 class="table-title">分析产品清单</h4>
            <el-table 
              :data="analysisData.product_list" 
              size="small"
              stripe
              style="margin-top: 10px;"
            >
              <el-table-column prop="fund_code" label="产品代码" width="120" />
              <el-table-column prop="fund_name" label="产品名称" min-width="200" show-overflow-tooltip />
              <el-table-column prop="sub_strategy" label="策略类型" width="120" align="center" />
              <el-table-column prop="market_value" label="持仓市值" width="120" align="right">
                <template #default="scope">
                  {{ formatCurrency(scope.row.market_value) }}
                </template>
              </el-table-column>
              <el-table-column prop="weight" label="权重占比" width="100" align="right">
                <template #default="scope">
                  {{ scope.row.weight ? scope.row.weight.toFixed(1) + '%' : '--' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        
        <div v-else-if="!loading" class="empty-state">
          <el-empty description="暂无底层持仓分析数据" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { positionAPI } from '@/api/position'

// Props
const props = defineProps({
  groupId: {
    type: String,
    required: true
  }
})

// 响应式数据
const loading = ref(false)
const error = ref('')
const analysisData = ref(null)
const assetChartRef = ref()
const industryChartRef = ref()
let assetChart = null
let industryChart = null

// 格式化货币
const formatCurrency = (value) => {
  if (!value) return '¥0'
  return '¥' + Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}

// 获取分析数据
const fetchAnalysisData = async () => {
  try {
    loading.value = true
    error.value = ''
    
    console.log('开始获取底层持仓分析数据, groupId:', props.groupId)
    const response = await positionAPI.getUnderlyingAnalysis(props.groupId)
    console.log('API响应:', response)
    
    if (response.success) {
      analysisData.value = response.data
      console.log('设置analysisData:', analysisData.value)
      
      // 等待DOM更新后初始化图表
      await nextTick()
      console.log('开始初始化图表')
      initCharts()
    } else {
      console.error('API返回错误:', response.message)
      error.value = response.message || '获取分析数据失败'
    }
  } catch (err) {
    console.error('底层持仓分析失败:', err)
    error.value = err.response?.data?.detail || '网络请求失败'
  } finally {
    loading.value = false
  }
}

// 初始化图表
const initCharts = () => {
  console.log('initCharts调用, analysisData.value:', analysisData.value)
  if (!analysisData.value) {
    console.log('analysisData为空，跳过图表初始化')
    return
  }
  
  console.log('资产分布数据:', analysisData.value.asset_distribution?.data)
  console.log('行业分布数据:', analysisData.value.industry_distribution?.data)
  
  // 初始化资产分布饼图
  if (assetChartRef.value) {
    console.log('初始化资产分布饼图')
    assetChart = echarts.init(assetChartRef.value)
    const assetOption = {
      tooltip: {
        trigger: 'item',
        formatter: (params) => {
          return `${params.name}<br/>市值: ${formatCurrency(params.value)}<br/>占比: ${params.percent}%`
        }
      },
      legend: {
        orient: 'vertical',
        right: 10,
        top: 'middle',
        type: 'scroll'
      },
      series: [
        {
          name: '资产分布',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: true,
          label: {
            show: true,
            position: 'outside',
            formatter: '{d}%',
            fontSize: 12,
            fontWeight: 'normal'
          },
          labelLine: {
            show: true,
            length: 10,
            length2: 20,
            smooth: false
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '14',
              fontWeight: 'bold',
              formatter: '{b}\n{d}%'
            }
          },
          data: Array.from(analysisData.value.asset_distribution.data).map(item => ({
            name: item.name,
            value: item.value
          }))
        }
      ]
    }
    assetChart.setOption(assetOption)
    console.log('资产分布饼图设置完成')
  }
  
  // 初始化行业分布柱状图
  if (industryChartRef.value) {
    console.log('初始化行业分布柱状图')
    industryChart = echarts.init(industryChartRef.value)
    const industryData = Array.from(analysisData.value.industry_distribution.data)
    console.log('行业数据:', industryData)
    
    const industryOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params) => {
          const param = params[0]
          const percentage = param.data.percentage ? param.data.percentage.toFixed(1) : '0.0'
          return `${param.name}<br/>市值: ${formatCurrency(param.value)}<br/>占比: ${percentage}%`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: industryData.map(item => item.name),
        axisLabel: {
          rotate: 45,
          interval: 0
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value) => {
            if (value >= 10000) {
              return (value / 10000).toFixed(0) + '万'
            }
            return value.toString()
          }
        }
      },
      series: [
        {
          type: 'bar',
          data: industryData.map(item => ({
            value: item.value,
            percentage: item.percentage
          })),
          itemStyle: {
            color: '#409EFF'
          },
          label: {
            show: true,
            position: 'top',
            formatter: (params) => {
              const percentage = params.data.percentage ? params.data.percentage.toFixed(1) : '0.0'
              return `${percentage}%`
            },
            fontSize: 11,
            fontWeight: 'normal',
            color: '#666'
          }
        }
      ]
    }
    industryChart.setOption(industryOption)
    console.log('行业分布柱状图设置完成')
  }
  
  // 响应式调整
  window.addEventListener('resize', () => {
    assetChart?.resize()
    industryChart?.resize()
  })
}

// 生命周期
onMounted(() => {
  console.log('UnderlyingPositionAnalysis组件已挂载, groupId:', props.groupId)
  fetchAnalysisData()
})

// 清理图表
const cleanup = () => {
  assetChart?.dispose()
  industryChart?.dispose()
  window.removeEventListener('resize', () => {
    assetChart?.resize()
    industryChart?.resize()
  })
}

// 组件卸载时清理
import { onUnmounted } from 'vue'
onUnmounted(cleanup)
</script>

<style scoped>
.underlying-analysis {
  margin-top: 24px;
}

.analysis-card {
  border: 1px solid #e4e7ed;
}

.analysis-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.analysis-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.analysis-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.analysis-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 16px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.total-value {
  font-size: 14px;
  color: #606266;
}

.total-value strong {
  color: #409EFF;
  font-weight: 600;
}

.charts-row {
  margin-bottom: 24px;
}

.chart-container {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 16px;
  background: white;
}

.chart-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  text-align: center;
}

.chart {
  width: 100%;
}

.data-tables {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.table-title {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.error-state {
  padding: 20px;
}

.empty-state {
  padding: 40px 20px;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
}

:deep(.el-table th) {
  background-color: #fafafa;
}
</style>