<template>
  <div class="public-fund">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>公募基金管理</h2>
      <p class="page-description">公募基金数据查询、分析与管理</p>
    </div>
    
    <!-- 功能卡片 -->
    <el-row :gutter="24" class="feature-cards">
      <el-col :span="8">
        <el-card class="feature-card" shadow="hover">
          <div class="card-content">
            <el-icon class="card-icon" color="#409eff"><TrendCharts /></el-icon>
            <h3>基金行情</h3>
            <p>实时查询公募基金净值、涨跌幅等行情数据</p>
            <el-button type="primary" @click="goToQuotes">查看行情</el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="feature-card" shadow="hover">
          <div class="card-content">
            <el-icon class="card-icon" color="#67c23a"><Search /></el-icon>
            <h3>基金筛选</h3>
            <p>根据业绩、规模、类型等条件筛选优质基金</p>
            <el-button type="success" @click="goToScreen">基金筛选</el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="feature-card" shadow="hover">
          <div class="card-content">
            <el-icon class="card-icon" color="#e6a23c"><DataAnalysis /></el-icon>
            <h3>业绩分析</h3>
            <p>基金历史业绩、风险指标深度分析对比</p>
            <el-button type="warning" @click="goToAnalysis">业绩分析</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>


    <!-- 快速查询 -->
    <el-card class="quick-search-section">
      <template #header>
        <span>快速查询</span>
      </template>
      
      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="基金代码/名称">
          <el-input
            v-model="searchForm.keyword"
            placeholder="输入基金代码或名称"
            style="width: 300px"
            @keyup.enter="searchFund"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchFund">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="search-results">
        <h4>搜索结果</h4>
        <el-table :data="searchResults" stripe>
          <el-table-column prop="fund_code" label="基金代码" width="120" />
          <el-table-column prop="fund_name" label="基金名称" show-overflow-tooltip />
          <el-table-column prop="nav" label="最新净值" width="120" />
          <el-table-column prop="nav_date" label="净值日期" width="120" />
          <el-table-column prop="change_rate" label="涨跌幅" width="100">
            <template #default="{ row }">
              <span :class="getChangeRateClass(row.change_rate)">
                {{ formatChangeRate(row.change_rate) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 页面数据
const searchForm = reactive({
  keyword: ''
})

const searchResults = ref([])


// 功能导航
const goToQuotes = () => {
  ElMessage.info('基金行情功能开发中...')
}

const goToScreen = () => {
  ElMessage.info('基金筛选功能开发中...')
}

const goToAnalysis = () => {
  ElMessage.info('业绩分析功能开发中...')
}


// 基金搜索
const searchFund = () => {
  if (!searchForm.keyword.trim()) {
    ElMessage.warning('请输入基金代码或名称')
    return
  }
  
  ElMessage.info('搜索功能开发中...')
  // TODO: 实现基金搜索功能
  
  // 模拟搜索结果
  searchResults.value = [
    {
      fund_code: '000001',
      fund_name: '华夏成长混合',
      nav: '2.1234',
      nav_date: '2024-11-08',
      change_rate: 1.23
    }
  ]
}

const viewDetail = (fund) => {
  ElMessage.info(`查看 ${fund.fund_name} 详情功能开发中...`)
}

// 格式化函数
const getChangeRateClass = (rate) => {
  if (rate > 0) return 'positive'
  if (rate < 0) return 'negative'
  return 'neutral'
}

const formatChangeRate = (rate) => {
  if (rate == null) return '--'
  const sign = rate > 0 ? '+' : ''
  return `${sign}${rate.toFixed(2)}%`
}

// 生命周期
onMounted(() => {
  // 页面初始化逻辑
})
</script>

<style scoped>
.public-fund {
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

.feature-cards {
  margin-bottom: 24px;
}

.feature-card {
  height: 200px;
  cursor: pointer;
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-content {
  text-align: center;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.card-icon {
  font-size: 40px;
  margin-bottom: 16px;
}

.card-content h3 {
  color: #303133;
  margin: 0 0 12px 0;
  font-size: 18px;
  font-weight: 600;
}

.card-content p {
  color: #606266;
  margin: 0 0 16px 0;
  font-size: 14px;
  line-height: 1.5;
}


.quick-search-section {
  margin-bottom: 24px;
}

.search-form {
  margin-bottom: 16px;
}

.search-results {
  margin-top: 24px;
}

.search-results h4 {
  color: #303133;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

/* 涨跌幅颜色 */
.positive {
  color: #f56c6c;
  font-weight: 600;
}

.negative {
  color: #67c23a;
  font-weight: 600;
}

.neutral {
  color: #909399;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .public-fund {
    padding: 16px;
  }
  
  .page-header h2 {
    font-size: 20px;
  }
  
  .feature-cards .el-col {
    margin-bottom: 16px;
  }
  
}
</style>