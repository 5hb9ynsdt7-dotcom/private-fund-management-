<template>
  <div class="trade-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>交易分析</h2>
      <p class="page-description">客户交易行为分析和统计</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-section">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="总交易笔数"
            :value="statistics.totalTrades"
            suffix="笔"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><Switch /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="总交易金额"
            :value="statistics.totalAmount"
            :precision="2"
            suffix="万元"
          >
            <template #prefix>
              <el-icon style="color: #67c23a"><Money /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="申购金额"
            :value="statistics.subscriptionAmount"
            :precision="2"
            suffix="万元"
          >
            <template #prefix>
              <el-icon style="color: #e6a23c"><Plus /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="赎回金额"
            :value="statistics.redemptionAmount"
            :precision="2"
            suffix="万元"
          >
            <template #prefix>
              <el-icon style="color: #f56c6c"><Minus /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 功能开发中提示 -->
    <el-card class="development-notice">
      <el-result
        icon="info"
        title="功能开发中"
        sub-title="交易分析页面正在开发中，敬请期待"
      >
        <template #extra>
          <el-button type="primary" @click="$router.push('/nav')">
            返回净值管理
          </el-button>
          <el-button @click="$router.push('/strategy')">
            查看策略管理
          </el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

// 模拟统计数据
const statistics = reactive({
  totalTrades: 2856,
  totalAmount: 15680.5,
  subscriptionAmount: 8920.3,
  redemptionAmount: 6760.2
})
</script>

<style scoped>
.trade-analysis {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  color: #303133;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.development-notice {
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-section .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .trade-analysis {
    padding: 16px;
  }
  
  .page-header h2 {
    font-size: 20px;
  }
  
  .stats-section .el-col {
    margin-bottom: 12px;
  }
}
</style>