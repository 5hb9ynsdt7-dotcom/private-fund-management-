<template>
  <div class="indicator-card">
    <div class="indicator-label">{{ label }}</div>
    <div
      class="indicator-value"
      :class="getValueClass"
    >
      {{ formattedValue }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true,
    default: '指标名称'
  },
  value: {
    type: [Number, String],
    default: 0
  },
  unit: {
    type: String,
    default: '%'
  },
  colorize: {
    type: Boolean,
    default: true
  },
  precision: {
    type: Number,
    default: 2
  }
})

// 格式化值
const formattedValue = computed(() => {
  if (props.value === null || props.value === undefined) {
    return '--'
  }

  const numValue = typeof props.value === 'number' ? props.value : parseFloat(props.value)

  if (isNaN(numValue)) {
    return '--'
  }

  const formatted = numValue.toFixed(props.precision)
  return `${formatted}${props.unit}`
})

// 根据正负值返回颜色类
const getValueClass = computed(() => {
  if (!props.colorize) {
    return ''
  }

  const numValue = typeof props.value === 'number' ? props.value : parseFloat(props.value)

  if (isNaN(numValue)) {
    return ''
  }

  if (numValue > 0) {
    return 'value-positive'
  } else if (numValue < 0) {
    return 'value-negative'
  }

  return ''
})
</script>

<style scoped>
.indicator-card {
  text-align: center;
  padding: 20px 15px;
  background: #fafafa;
  border-radius: 8px;
  transition: all 0.3s;
}

.indicator-card:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

.indicator-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
  font-weight: 500;
}

.indicator-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.value-positive {
  color: #f5222d;
}

.value-negative {
  color: #52c41a;
}
</style>
