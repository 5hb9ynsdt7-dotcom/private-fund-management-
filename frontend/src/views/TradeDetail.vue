<template>
  <div class="trade-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>{{ reportTitle }}</h2>
      <el-button @click="$router.push('/trade')" size="small">
        <el-icon><Back /></el-icon>
        返回交易分析
      </el-button>
    </div>
    
    <!-- 客户概览卡片 -->
    <el-card class="client-overview" v-loading="analysisLoading">
      <template #header>
        <div class="card-header">
          <span>客户概览</span>
          <el-button @click="refreshData" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <!-- 第一行：投资总额、赎回总额、当前持仓市值、总现金分红 -->
      <el-row :gutter="24">
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">投资总额</div>
            <div class="value amount">{{ formatMoney(analysisData?.total_investment_amount || 0) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">赎回总额</div>
            <div class="value amount">{{ formatMoney(analysisData?.total_redemption_amount || 0) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">当前持仓市值</div>
            <div class="value amount market-value">{{ formatMoney(analysisData?.current_total_market_value || 0) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">总现金分红</div>
            <div class="value amount dividend-income">{{ formatMoney(analysisData?.total_dividend_income || 0) }}</div>
          </div>
        </el-col>
      </el-row>
      
      <el-divider />
      
      <!-- 第二行：总产品数、当前持仓产品数、累计盈亏、累计收益率 -->
      <el-row :gutter="24">
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">总产品数</div>
            <div class="value">{{ analysisData?.total_products || 0 }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">当前持仓产品数</div>
            <div class="value">{{ analysisData?.current_holding_products || 0 }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">累计盈亏</div>
            <div class="value amount" :class="getPnlClass(analysisData?.cumulative_pnl)">
              {{ formatMoney(analysisData?.cumulative_pnl || 0) }}
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="overview-item">
            <div class="label">累计收益率</div>
            <div class="value percent" :class="getPnlClass(analysisData?.cumulative_return_rate)">
              {{ formatPercent(analysisData?.cumulative_return_rate || 0) }}
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 视图切换 -->
    <el-card class="view-toggle-section">
      <el-radio-group v-model="currentView" size="large">
        <el-radio-button value="holdings">当前持仓</el-radio-button>
        <el-radio-button value="cleared">已清仓产品</el-radio-button>
        <el-radio-button value="stage-analysis">阶段收益分析</el-radio-button>
      </el-radio-group>
    </el-card>
    
    <!-- 当前持仓产品 -->
    <div v-if="currentView === 'holdings'">
      <div v-for="(strategyGroup, strategyName) in groupedCurrentHoldings" :key="strategyName" class="strategy-group">
        <el-card class="strategy-card">
          <template #header>
            <div class="strategy-header">
              <span class="strategy-name">{{ strategyName }}</span>
              <span class="product-count">{{ strategyGroup.length }} 个产品</span>
            </div>
          </template>
          
          <el-table
            :data="strategyGroup"
            style="width: 100%"
            stripe
            border
            table-layout="fixed"
            :show-summary="true"
            :summary-method="(param) => getHoldingsSummaryMethod(param, strategyGroup)"
            sum-text="汇总"
          >
            <el-table-column
              prop="fund_name"
              label="产品名称"
              width="360"
              align="left"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div class="product-cell">
                  <div class="product-name">{{ row.fund_name || row.product_name || '--' }}</div>
                  <div class="product-labels">
                    <span class="label label-strategy">{{ row.sub_strategy || '--' }}</span>
                    <span class="label label-status">{{ row.holding_status }}</span>
                    <span v-if="row.is_qd_product" class="label label-qd">QD</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="first_buy_date"
              label="首次买入日期"
              align="center"
            >
              <template #default="{ row }">
                <span class="date-cell">{{ formatDate(row.first_buy_date) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="total_buy_amount"
              label="买入金额"
              align="center"
            >
              <template #default="{ row }">
                <span class="money-text">{{ formatMoney(row.total_buy_amount) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="total_sell_amount"
              label="赎回金额"
              align="center"
            >
              <template #default="{ row }">
                <span class="money-text">{{ formatMoney(row.total_sell_amount) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="total_dividend_amount"
              label="分红金额"
              align="center"
            >
              <template #default="{ row }">
                <span class="money-text dividend-text">{{ formatMoney(row.total_dividend_amount || 0) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="current_shares"
              label="当前持仓份额"
              align="center"
            >
              <template #default="{ row }">
                <span class="shares-text">{{ formatShares(row.current_shares) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="latest_nav"
              label="最新单位净值"
              align="center"
            >
              <template #default="{ row }">
                <div class="nav-cell">
                  <div class="nav-value">{{ formatNav(row.latest_nav) }}</div>
                  <div class="nav-date date-cell" v-if="row.nav_date">{{ formatDate(row.nav_date) }}</div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="total_pnl"
              label="持有盈亏"
              align="center"
            >
              <template #default="{ row }">
                <span class="money-text" :class="getPnlClass(row.total_pnl)">{{ formatMoney(row.total_pnl) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column
              prop="return_rate"
              label="持有收益率"
              align="center"
            >
              <template #default="{ row }">
                <span class="percent-text" :class="getPnlClass(row.return_rate)">{{ formatPercent(row.return_rate) }}</span>
              </template>
            </el-table-column>
            
            <el-table-column
              label="操作"
              width="100"
              align="center"
            >
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  type="text" 
                  @click="showTransactionDetails(row)"
                >
                  交易明细
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
      
      <el-empty v-if="!analysisData?.current_holdings?.length" description="暂无当前持仓产品" />
    </div>
    
    <!-- 已清仓产品 -->
    <div v-if="currentView === 'cleared'">
      <el-card class="cleared-products-card">
        <template #header>
          <div class="card-header">
            <span>已清仓产品</span>
            <span class="product-count">{{ analysisData?.cleared_products?.length || 0 }} 个产品</span>
          </div>
        </template>
        
        <el-table
          :data="sortedClearedProducts"
          style="width: 100%"
          stripe
          border
          table-layout="fixed"
          :show-summary="true"
          :summary-method="getClearedSummaryMethod"
          sum-text="汇总"
        >
          <el-table-column
            prop="fund_name"
            label="产品名称"
            width="360"
            align="left"
            show-overflow-tooltip
          >
            <template #default="{ row }">
              <div class="product-cell">
                <div class="product-name">{{ row.fund_name || row.product_name || '--' }}</div>
                <div class="product-labels">
                  <span class="label label-strategy">{{ row.sub_strategy || '--' }}</span>
                  <span class="label label-status label-cleared">已清仓</span>
                  <span v-if="row.is_qd_product" class="label label-qd">QD</span>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="first_buy_date"
            label="首次买入日期"
            align="center"
          >
            <template #default="{ row }">
              <span class="date-cell">{{ formatDate(row.first_buy_date) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="total_buy_amount"
            label="买入金额"
            align="center"
          >
            <template #default="{ row }">
              <span class="money-text">{{ formatMoney(row.total_buy_amount) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="total_sell_amount"
            label="赎回金额"
            align="center"
          >
            <template #default="{ row }">
              <span class="money-text">{{ formatMoney(row.total_sell_amount) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="total_dividend_amount"
            label="分红金额"
            align="center"
          >
            <template #default="{ row }">
              <span class="money-text dividend-text">{{ formatMoney(row.total_dividend_amount || 0) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="total_pnl"
            label="持有盈亏"
            align="center"
          >
            <template #default="{ row }">
              <span class="money-text" :class="getPnlClass(row.total_pnl)">{{ formatMoney(row.total_pnl) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="return_rate"
            label="持有收益率"
            align="center"
          >
            <template #default="{ row }">
              <span class="percent-text" :class="getPnlClass(row.return_rate)">{{ formatPercent(row.return_rate) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            prop="last_transaction_date"
            label="最后交易日期"
            align="center"
          >
            <template #default="{ row }">
              <span class="date-cell">{{ formatDate(row.last_transaction_date) }}</span>
            </template>
          </el-table-column>
          
          <el-table-column
            label="操作"
            width="100"
            align="center"
          >
            <template #default="{ row }">
              <el-button 
                size="small" 
                type="text" 
                @click="showTransactionDetails(row)"
              >
                交易明细
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      
      <el-empty v-if="!analysisData?.cleared_products?.length" description="暂无已清仓产品" />
    </div>
    
    <!-- 阶段收益分析 -->
    <div v-if="currentView === 'stage-analysis'">
      <StageAnalysis :group-id="groupId" />
    </div>
    
    <!-- 交易明细对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      :title="`${selectedProduct?.product_name || selectedProduct?.fund_name} - 交易明细`"
      width="80%"
      destroy-on-close
    >
      <el-table
        :data="selectedProduct?.transactions || []"
        style="width: 100%"
        stripe
        border
        max-height="400"
      >
        <el-table-column
          prop="confirmed_date"
          label="交易日期"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ formatDate(row.confirmed_date) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="transaction_type"
          label="交易类型"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :type="getTransactionTypeClass(row.transaction_type)" size="small">
              {{ row.transaction_type }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="confirmed_shares"
          label="确认份额"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ formatShares(row.confirmed_shares) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="confirmed_amount"
          label="确认金额"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <span class="money-text" :class="getAmountClass(row.confirmed_amount)">
              {{ formatMoney(row.confirmed_amount) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="transaction_fee"
          label="手续费"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span class="fee-text">{{ formatMoney(row.transaction_fee) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { transactionAPI } from '@/api/transaction'
import StageAnalysis from '@/components/StageAnalysis.vue'

const route = useRoute()
const router = useRouter()

// 获取路由参数
const groupId = computed(() => route.params.groupId || '未知客户')

// 响应式数据
const analysisLoading = ref(false)
const analysisData = ref(null)
const currentView = ref('holdings')
const detailDialogVisible = ref(false)
const selectedProduct = ref(null)

// 报告标题 - 个性化显示客户姓氏
const reportTitle = computed(() => {
  let title = '总的二级交易分析'
  
  // 提取客户姓氏
  if (analysisData.value?.client_info?.client_name) {
    const clientName = analysisData.value.client_info.client_name
    // 取第一个字符作为姓氏，添加"总"
    const surname = clientName.charAt(0)
    if (surname) {
      title = `${surname}总的二级交易分析`
    }
  }
  
  // 添加日期
  if (analysisData.value?.report_date) {
    title += `（${analysisData.value.report_date}）`
  }
  
  return title
})

// 按大类策略分组的当前持仓
const groupedCurrentHoldings = computed(() => {
  if (!analysisData.value?.current_holdings) return {}
  
  const grouped = {}
  analysisData.value.current_holdings.forEach(holding => {
    // 直接使用大类策略作为分组名
    const mainStrategy = holding.main_strategy || '其他策略'
    
    if (!grouped[mainStrategy]) {
      grouped[mainStrategy] = []
    }
    grouped[mainStrategy].push(holding)
  })
  
  return grouped
})

// 按最后交易日期排序的已清仓产品（最新的在前面）
const sortedClearedProducts = computed(() => {
  if (!analysisData.value?.cleared_products) return []
  
  return [...analysisData.value.cleared_products].sort((a, b) => {
    // 将日期字符串转换为Date对象进行比较，最新日期排在前面
    const dateA = new Date(a.last_transaction_date || '1900-01-01')
    const dateB = new Date(b.last_transaction_date || '1900-01-01')
    return dateB - dateA // 降序排序（最新的在前面）
  })
})

// 当前持仓汇总计算方法
const getHoldingsSummaryMethod = (param, strategyGroup) => {
  const { columns } = param
  const sums = []
  
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '汇总'
      return
    }
    
    const values = strategyGroup.map(item => Number(item[column.property]) || 0)
    
    switch (column.property) {
      case 'total_buy_amount':
      case 'total_sell_amount':
      case 'total_dividend_amount':
      case 'total_pnl':
        const sum = values.reduce((prev, curr) => prev + curr, 0)
        sums[index] = formatMoney(sum)
        break
      case 'return_rate':
        // 计算总体收益率：总盈亏 / 总买入金额 * 100
        const totalBuyAmount = strategyGroup.reduce((sum, item) => sum + (Number(item.total_buy_amount) || 0), 0)
        const totalPnl = strategyGroup.reduce((sum, item) => sum + (Number(item.total_pnl) || 0), 0)
        const avgReturnRate = totalBuyAmount > 0 ? (totalPnl / totalBuyAmount) * 100 : 0
        sums[index] = formatPercent(avgReturnRate)
        break
      default:
        sums[index] = '--'
        break
    }
  })
  
  return sums
}

// 已清仓产品汇总计算方法
const getClearedSummaryMethod = (param) => {
  const { columns, data } = param
  const sums = []
  
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '汇总'
      return
    }
    
    const values = data.map(item => Number(item[column.property]) || 0)
    
    switch (column.property) {
      case 'total_buy_amount':
      case 'total_sell_amount':
      case 'total_dividend_amount':
      case 'total_pnl':
        const sum = values.reduce((prev, curr) => prev + curr, 0)
        sums[index] = formatMoney(sum)
        break
      case 'return_rate':
        // 计算总体收益率：总盈亏 / 总买入金额 * 100
        const totalBuyAmount = data.reduce((sum, item) => sum + (Number(item.total_buy_amount) || 0), 0)
        const totalPnl = data.reduce((sum, item) => sum + (Number(item.total_pnl) || 0), 0)
        const avgReturnRate = totalBuyAmount > 0 ? (totalPnl / totalBuyAmount) * 100 : 0
        sums[index] = formatPercent(avgReturnRate)
        break
      default:
        sums[index] = '--'
        break
    }
  })
  
  return sums
}

// 加载交易分析数据
const loadAnalysisData = async () => {
  analysisLoading.value = true
  try {
    const response = await transactionAPI.getClientAnalysis(groupId.value)
    analysisData.value = response
    
    console.log('分析数据:', response)
  } catch (error) {
    console.error('加载交易分析失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(`加载交易分析失败: ${errorMsg}`)
    analysisData.value = null
  } finally {
    analysisLoading.value = false
  }
}

// 显示交易明细
const showTransactionDetails = (product) => {
  selectedProduct.value = product
  detailDialogVisible.value = true
}

// 刷新数据
const refreshData = () => {
  loadAnalysisData()
}

// 格式化函数
const formatMoney = (amount) => {
  if (amount == null || amount === '') return '--'
  const num = parseFloat(amount)
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatShares = (shares) => {
  if (shares == null || shares === '') return '--'
  const num = parseFloat(shares)
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 6
  })
}

const formatNav = (nav) => {
  if (nav == null || nav === '') return '--'
  const num = parseFloat(nav)
  return num.toFixed(4)
}

const formatPercent = (rate) => {
  if (rate == null || rate === '') return '--'
  const num = parseFloat(rate)
  return `${num.toFixed(2)}%`
}

const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleDateString('zh-CN')
}

const getAmountClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  return num >= 0 ? 'profit-text' : 'loss-text'
}

const getPnlClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  return num > 0 ? 'profit-text' : num < 0 ? 'loss-text' : ''
}

const getTransactionTypeClass = (type) => {
  if (!type) return ''
  if (type.includes('申购') || type.includes('买入')) {
    return 'success'
  } else if (type.includes('赎回') || type.includes('卖出')) {
    return 'danger'
  } else if (type.includes('分红')) {
    return 'warning'
  }
  return ''
}

// 生命周期
onMounted(() => {
  loadAnalysisData()
})
</script>

<style scoped>
.trade-detail {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  color: #303133;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.client-overview {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.overview-item {
  text-align: center;
  padding: 12px 0;
}

.overview-item .label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.overview-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.overview-item .value.amount {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.overview-item .value.percent {
  font-size: 18px;
  font-weight: 600;
}

.overview-item .value.market-value {
  color: #303133;
}

.overview-item .value.dividend-income {
  color: #303133;
}

.view-toggle-section {
  margin-bottom: 24px;
  text-align: center;
}

.strategy-group {
  margin-bottom: 24px;
}

.strategy-card {
  margin-bottom: 16px;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.product-count {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 4px 8px;
  border-radius: 12px;
}

.cleared-products-card {
  margin-bottom: 24px;
}

.product-cell {
  text-align: left;
}

.product-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.4;
}

.product-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.label {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
}

.label-strategy {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.label-status {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.label-cleared {
  background-color: #fff1f0;
  color: #ff4d4f;
  border: 1px solid #ffadd2;
}

.label-qd {
  background-color: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
  font-weight: 700;
}

.strategy-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.shares-text {
  font-weight: 500;
}

.nav-cell {
  text-align: center;
}

.nav-value {
  font-weight: 600;
  color: #303133;
  margin-bottom: 2px;
}

.nav-date {
  font-size: 11px;
  color: #909399;
  line-height: 1.2;
}

.percent-text {
  font-weight: 600;
}

/* 金额和数值样式 */
.money-text {
  font-weight: 500;
}

.fee-text {
  color: #f56c6c;
  font-weight: 500;
}

.dividend-text {
  color: #303133;
  font-weight: 600;
}

.profit-text {
  color: #ff4d4f;
  font-weight: 600;
}

.loss-text {
  color: #52c41a;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
  
  .overview-item .value {
    font-size: 16px;
  }
  
  .strategy-info {
    gap: 2px;
  }
}

@media (max-width: 768px) {
  .trade-detail {
    padding: 16px;
  }
  
  .page-header h2 {
    font-size: 20px;
  }
  
  .overview-item {
    padding: 8px 0;
  }
  
  .overview-item .value {
    font-size: 14px;
  }
  
  .strategy-header {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .product-cell {
    text-align: center;
  }
  
  .product-name {
    font-size: 14px;
  }
  
  .label {
    font-size: 10px;
    padding: 1px 4px;
  }
  
  .nav-date {
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .trade-detail {
    padding: 12px;
  }
  
  .client-overview,
  .view-toggle-section,
  .strategy-group {
    margin-bottom: 16px;
  }
  
  .strategy-name {
    font-size: 14px;
  }
}

/* 日期显示统一字体 */
.el-table td {
  font-family: inherit;
}

.el-table td .cell {
  font-family: inherit;
}

/* 为日期列添加统一数字字体 */
.date-cell {
  /* 使用全局Inter字体 */
}

/* 汇总行样式 */
.el-table__footer .el-table__cell {
  background-color: #f8f9fa !important;
  font-weight: 600 !important;
  border-top: 2px solid #e4e7ed !important;
}

.el-table__footer .cell {
  font-weight: 600 !important;
  color: #303133 !important;
}

/* 空状态样式 */
.el-empty {
  padding: 60px 0;
}

/* 对话框样式 */
.el-dialog__body {
  padding: 20px;
}
</style>