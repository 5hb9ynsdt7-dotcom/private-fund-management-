<template>
  <el-card class="fund-info-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <div class="fund-title">
          <span class="fund-code">{{ fundInfo.fund_code }}</span>
          <span class="fund-name">{{ fundInfo.fund_name }}</span>
        </div>
        <div class="card-actions">
          <slot name="actions"></slot>
        </div>
      </div>
    </template>

    <div class="fund-info-content">
      <div class="info-row">
        <div class="info-item">
          <span class="info-label">基金类型</span>
          <span class="info-value">{{ fundInfo.fund_type || '--' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">基金公司</span>
          <span class="info-value">{{ fundInfo.fund_company || '--' }}</span>
        </div>
      </div>

      <div class="info-row">
        <div class="info-item">
          <span class="info-label">基金经理</span>
          <span class="info-value">{{ fundInfo.fund_manager || '--' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">成立日期</span>
          <span class="info-value">{{ formatDate(fundInfo.establish_date) }}</span>
        </div>
      </div>

      <div class="info-row" v-if="fundInfo.asset_scale">
        <div class="info-item">
          <span class="info-label">资产规模</span>
          <span class="info-value">{{ fundInfo.asset_scale }} 亿</span>
        </div>
        <div class="info-item">
          <span class="info-label">数据来源</span>
          <span class="info-value">{{ getDataSourceText(fundInfo.data_source) }}</span>
        </div>
      </div>

      <div class="info-row" v-if="fundInfo.remark">
        <div class="info-item full-width">
          <span class="info-label">备注</span>
          <span class="info-value">{{ fundInfo.remark }}</span>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  fundInfo: {
    type: Object,
    required: true,
    default: () => ({})
  }
})

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '--'
  return dateStr
}

// 数据来源文本
const getDataSourceText = (source) => {
  const sourceMap = {
    'manual': '手动录入',
    'eastmoney': '天天基金',
    'wind': 'Wind',
    'auto': '自动抓取'
  }
  return sourceMap[source] || source || '--'
}
</script>

<style scoped>
.fund-info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.fund-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fund-code {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
  font-family: 'Courier New', Courier, monospace;
}

.fund-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.fund-info-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-row {
  display: flex;
  gap: 20px;
}

.info-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-item.full-width {
  flex: 1 1 100%;
}

.info-label {
  font-size: 12px;
  color: #999;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 400;
}

.card-actions {
  display: flex;
  gap: 10px;
}
</style>
