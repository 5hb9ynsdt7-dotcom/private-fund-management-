<template>
  <div class="trade-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>交易详情</h2>
      <p class="page-description">{{ clientId }} 客户交易详细信息</p>
    </div>
    
    <!-- 功能开发中提示 -->
    <el-card class="development-notice">
      <el-result
        icon="info"
        title="功能开发中"
        sub-title="交易详情页面正在开发中，敬请期待"
      >
        <template #extra>
          <el-button type="primary" @click="$router.push('/trade')">
            返回交易分析
          </el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const clientId = computed(() => route.params.id || '未知客户')
</script>

<style scoped>
.trade-detail {
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

.development-notice {
  text-align: center;
}

@media (max-width: 768px) {
  .trade-detail {
    padding: 16px;
  }
  
  .page-header h2 {
    font-size: 20px;
  }
}
</style>