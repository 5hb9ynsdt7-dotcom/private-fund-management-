<template>
  <div class="nav-chart-container">
    <div class="chart-header">
      <div class="chart-title">
        <span>净值走势</span>
      </div>
      <div class="chart-controls">
        <el-radio-group v-model="chartType" size="small" @change="updateChart">
          <el-radio-button label="unit">单位净值</el-radio-button>
          <el-radio-button label="accum">累计净值</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    <div
      ref="chartRef"
      class="chart-canvas"
      :style="{ height: height }"
    ></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  navData: {
    type: Array,
    required: true,
    default: () => []
  },
  height: {
    type: String,
    default: '400px'
  }
})

const chartRef = ref(null)
const chartInstance = ref(null)
const chartType = ref('unit')

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  chartInstance.value = echarts.init(chartRef.value)

  // 设置图表配置
  updateChart()

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

// 更新图表
const updateChart = () => {
  if (!chartInstance.value || !props.navData || props.navData.length === 0) {
    return
  }

  // 准备数据
  const dates = props.navData.map(item => item.nav_date)
  const values = props.navData.map(item =>
    chartType.value === 'unit' ? item.unit_nav : item.accum_nav
  )

  const option = {
    title: {
      show: false
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function (params) {
        const date = params[0].axisValue
        const value = params[0].value
        const navType = chartType.value === 'unit' ? '单位净值' : '累计净值'
        return `${date}<br/>${navType}: ${value}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLabel: {
        rotate: 45,
        interval: 'auto'
      }
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        formatter: '{value}'
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: chartType.value === 'unit' ? '单位净值' : '累计净值',
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
          color: '#1890ff'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(24, 144, 255, 0.3)'
              },
              {
                offset: 1,
                color: 'rgba(24, 144, 255, 0.05)'
              }
            ]
          }
        }
      }
    ]
  }

  chartInstance.value.setOption(option)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 监听数据变化
watch(
  () => props.navData,
  () => {
    nextTick(() => {
      updateChart()
    })
  },
  { deep: true }
)

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.nav-chart-container {
  width: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.chart-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.chart-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.chart-canvas {
  width: 100%;
}
</style>
