<template>
  <div class="portfolio-detail">
    <div class="page-header">
      <div class="header-left">
        <el-icon class="back-icon" @click="goBack" style="cursor: pointer; margin-right: 12px;">
          <ArrowLeft />
        </el-icon>
        <el-input
          v-if="editingName"
          v-model="editPortfolioName"
          @blur="handleSaveNameconfirm"
          @keyup.enter="handleSaveName"
          style="width: 300px;"
          autofocus
        />
        <h2 v-else @click="startEditName" style="cursor: pointer; display: inline-flex; align-items: center;">
          {{ portfolio.portfolio_name }}
          <el-icon style="margin-left: 8px; font-size: 16px;"><Edit /></el-icon>
        </h2>
      </div>
      <div class="header-actions">
        <el-button @click="showTransactionDialog = true" type="primary">
          <el-icon><Plus /></el-icon>
          添加交易
        </el-button>
        <el-button @click="goBack">
          返回列表
        </el-button>
      </div>
    </div>

    <!-- 组合概览 -->
    <el-row :gutter="24" v-loading="loading">
      <el-col :span="6">
        <el-card>
          <el-statistic title="累计投入" :value="formatStatValue(portfolio.total_invested)" :precision="2" suffix="元" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="当前市值" :value="formatStatValue(portfolio.current_value)" :precision="2" suffix="元" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic title="累计收益" :value="formatStatValue(portfolio.total_return)" :precision="2" suffix="元" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <el-statistic
            title="收益率"
            :value="formatStatValue(portfolio.total_return_rate)"
            :precision="2"
            suffix="%"
            :value-style="{ color: getReturnColor(portfolio.total_return_rate) }"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 收益曲线 -->
    <el-card style="margin-top: 20px;">
      <template #header><span>收益曲线</span></template>
      <div ref="chartRef" style="height: 400px;"></div>
    </el-card>

    <!-- 当前持仓 -->
    <el-card style="margin-top: 20px;">
      <template #header><span>当前持仓</span></template>
      <el-table :data="positions" border>
        <el-table-column prop="fund_name" label="基金名称" width="180" show-overflow-tooltip />
        <el-table-column prop="shares" label="持有份额" align="center">
          <template #default="{ row }">{{ formatNumber(row.shares, 2) }}</template>
        </el-table-column>
        <el-table-column prop="cost_amount" label="投入成本" align="center">
          <template #default="{ row }">{{ formatMoney(row.cost_amount) }}</template>
        </el-table-column>
        <el-table-column prop="current_nav" label="最新净值" align="center">
          <template #default="{ row }">{{ formatNumber(row.current_nav, 4) }}</template>
        </el-table-column>
        <el-table-column prop="current_nav_date" label="净值日期" align="center" />
        <el-table-column prop="current_value" label="当前市值" align="center">
          <template #default="{ row }">{{ formatMoney(row.current_value) }}</template>
        </el-table-column>
        <el-table-column prop="weight" label="权重" align="center">
          <template #default="{ row }">{{ formatPercent(row.weight) }}</template>
        </el-table-column>
        <el-table-column prop="profit_loss" label="盈亏金额" align="center">
          <template #default="{ row }">
            <span :style="{ color: getReturnColor(row.profit_loss) }">
              {{ formatMoney(row.profit_loss) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="profit_loss_rate" label="盈亏率" align="center">
          <template #default="{ row }">
            <span :style="{ color: getReturnColor(row.profit_loss_rate) }">
              {{ formatPercent(row.profit_loss_rate) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 调仓记录 -->
    <el-card style="margin-top: 20px;">
      <template #header><span>调仓记录</span></template>
      <el-table :data="transactions" border>
        <el-table-column prop="transaction_date" label="日期" width="120" />
        <el-table-column prop="transaction_type" label="操作" width="80">
          <template #default="{ row }">
            <el-tag :type="row.transaction_type === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.transaction_type === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fund_name" label="基金" min-width="200" />
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">{{ formatMoney(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="shares" label="份额" width="120" align="right">
          <template #default="{ row }">{{ formatNumber(row.shares, 2) }}</template>
        </el-table-column>
        <el-table-column prop="nav" label="净值" width="100" align="right">
          <template #default="{ row }">{{ formatNumber(row.nav, 4) }}</template>
        </el-table-column>
        <el-table-column prop="note" label="备注" min-width="150" />
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              text
              @click="handleDeleteTransaction(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加交易对话框 -->
    <el-dialog v-model="showTransactionDialog" title="添加交易" width="600px" @open="loadFundList">
      <el-alert
        title="提示"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        系统将自动从公募基金净值数据中获取交易净值，并自动计算份额。请确保已在公募基金库中添加并抓取了该基金的净值。
      </el-alert>

      <el-form :model="transactionForm" label-width="100px">
        <el-form-item label="交易类型" required>
          <el-radio-group v-model="transactionForm.transaction_type">
            <el-radio label="buy">买入</el-radio>
            <el-radio label="sell">卖出</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="选择基金" required>
          <el-select
            v-model="transactionForm.fund_code"
            filterable
            placeholder="请选择基金"
            style="width: 100%"
          >
            <el-option
              v-for="fund in fundList"
              :key="fund.fund_code"
              :label="`${fund.fund_name} (${fund.fund_code})`"
              :value="fund.fund_code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="交易日期" required>
          <el-date-picker
            v-model="transactionForm.transaction_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择交易日期"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="交易金额" required>
          <el-input-number
            v-model="transactionForm.amount"
            :min="0"
            :precision="2"
            :controls="false"
            placeholder="请输入交易金额"
            style="width: 100%"
          />
          <span style="color: #909399; font-size: 12px;">系统将自动根据净值计算份额</span>
        </el-form-item>

        <el-form-item label="手续费">
          <el-input-number
            v-model="transactionForm.fee"
            :min="0"
            :precision="2"
            :controls="false"
            placeholder="手续费（可选）"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="transactionForm.note" type="textarea" :rows="2" placeholder="备注信息（可选）" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showTransactionDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingTransaction" @click="handleAddTransaction">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft, Edit } from '@element-plus/icons-vue'
import portfolioAPI from '@/api/portfolio'
import publicFundAPI from '@/api/publicFund'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const addingTransaction = ref(false)
const portfolio = ref({})
const positions = ref([])
const transactions = ref([])
const navHistory = ref([])
const fundList = ref([])

const showTransactionDialog = ref(false)
const transactionForm = ref({
  transaction_type: 'buy',
  fund_code: '',
  transaction_date: new Date().toISOString().split('T')[0],
  amount: 0,
  fee: 0,
  note: ''
})

const chartRef = ref()
let chartInstance = null

// 编辑组合名称
const editingName = ref(false)
const editPortfolioName = ref('')

const startEditName = () => {
  editingName.value = true
  editPortfolioName.value = portfolio.value.portfolio_name
}

const handleSaveName = async () => {
  if (!editPortfolioName.value || editPortfolioName.value.trim() === '') {
    ElMessage.warning('组合名称不能为空')
    return
  }

  try {
    await portfolioAPI.updatePortfolio(route.params.id, {
      portfolio_name: editPortfolioName.value.trim()
    })
    portfolio.value.portfolio_name = editPortfolioName.value.trim()
    editingName.value = false
    ElMessage.success('组合名称已更新')
  } catch (error) {
    console.error('更新组合名称失败:', error)
    ElMessage.error('更新失败')
  }
}

const handleSaveNameconfirm = () => {
  if (editPortfolioName.value !== portfolio.value.portfolio_name) {
    handleSaveName()
  } else {
    editingName.value = false
  }
}

// 加载基金列表
const loadFundList = async () => {
  try {
    const response = await publicFundAPI.getFundList({ page_size: 1000 })
    fundList.value = response.data
  } catch (error) {
    console.error('加载基金列表失败:', error)
  }
}

// 加载组合详情
const loadPortfolioDetail = async () => {
  loading.value = true
  try {
    const response = await portfolioAPI.getPortfolioDetail(route.params.id)
    portfolio.value = response.portfolio
    positions.value = response.positions
    transactions.value = response.transactions
    navHistory.value = response.nav_history

    await nextTick()
    renderChart()
  } catch (error) {
    console.error('加载组合详情失败:', error)
    ElMessage.error('加载组合详情失败')
  } finally {
    loading.value = false
  }
}

// 添加交易
const handleAddTransaction = async () => {
  if (!transactionForm.value.fund_code) {
    ElMessage.warning('请选择基金')
    return
  }

  if (!transactionForm.value.transaction_date) {
    ElMessage.warning('请选择交易日期')
    return
  }

  if (!transactionForm.value.amount || transactionForm.value.amount <= 0) {
    ElMessage.warning('请输入有效的交易金额')
    return
  }

  addingTransaction.value = true
  try {
    await portfolioAPI.addTransaction(route.params.id, transactionForm.value)
    ElMessage.success('添加成功，系统已自动获取净值并计算份额')
    showTransactionDialog.value = false

    // 重置表单
    transactionForm.value = {
      transaction_type: 'buy',
      fund_code: '',
      transaction_date: new Date().toISOString().split('T')[0],
      amount: 0,
      fee: 0,
      note: ''
    }

    // 重新加载数据
    await loadPortfolioDetail()
  } catch (error) {
    console.error('添加交易失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加交易失败')
  } finally {
    addingTransaction.value = false
  }
}

// 删除交易
const handleDeleteTransaction = async (transaction) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除该交易记录吗？删除后系统将自动回滚持仓和现金余额。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await portfolioAPI.deleteTransaction(route.params.id, transaction.id)
    ElMessage.success('删除成功')

    // 重新加载数据
    await loadPortfolioDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除交易失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除交易失败')
    }
  }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || navHistory.value.length === 0) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)

  const dates = navHistory.value.map(item => item.nav_date)
  const values = navHistory.value.map(item => parseFloat(item.total_assets))

  const option = {
    grid: {
      left: '80px',
      right: '40px',
      top: '40px',
      bottom: '60px'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = params[0].axisValue
        const value = params[0].value
        return `${date}<br/>持仓市值: ¥${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      }
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: {
        lineStyle: {
          color: '#999'
        }
      },
      axisLabel: {
        color: '#666'
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        show: true,
        lineStyle: {
          color: '#999'
        }
      },
      axisLabel: {
        color: '#666',
        formatter: (value) => '¥' + value.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
      },
      splitLine: {
        lineStyle: {
          color: '#e6e6e6'
        }
      }
    },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0,
            color: 'rgba(64, 158, 255, 0.3)'
          }, {
            offset: 1,
            color: 'rgba(64, 158, 255, 0.05)'
          }]
        }
      },
      lineStyle: {
        color: '#409EFF',
        width: 2
      }
    }]
  }

  chartInstance.setOption(option)
}

// 返回列表
const goBack = () => {
  router.push('/portfolio')
}

// 格式化函数 - 用于el-statistic组件
const formatStatValue = (value) => {
  if (value == null || value === '') return 0
  // 转换为数字并保留2位小数，返回数字类型
  return parseFloat(parseFloat(value).toFixed(2))
}

// 格式化金额 - 用于表格显示
const formatMoney = (value) => {
  if (value == null) return '--'
  return '¥' + parseFloat(value).toLocaleString('zh-CN', { 
    minimumFractionDigits: 2,
    maximumFractionDigits: 2 
  })
}

// 格式化百分比
const formatPercent = (value) => {
  if (value == null) return '--'
  return parseFloat(value).toFixed(2) + '%'
}

// 格式化数字
const formatNumber = (value, precision = 2) => {
  if (value == null) return '--'
  return parseFloat(value).toFixed(precision)
}

// 获取收益颜色
const getReturnColor = (value) => {
  if (value == null) return '#909399'
  return parseFloat(value) >= 0 ? '#f56c6c' : '#67c23a'
}

onMounted(() => {
  loadPortfolioDetail()
})
</script>

<style scoped>
.portfolio-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-left h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
  transition: color 0.3s;
}

.header-left h2:hover {
  color: #409EFF;
}

.back-icon {
  font-size: 24px;
  color: #606266;
  transition: color 0.3s;
}

.back-icon:hover {
  color: #409EFF;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>
