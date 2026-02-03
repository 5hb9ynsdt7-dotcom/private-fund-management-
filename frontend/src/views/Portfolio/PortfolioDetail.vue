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
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="showPositionDetail(row)"
            >
              查看明细
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 持仓明细对话框 -->
    <el-dialog
      v-model="showPositionDetailDialog"
      :title="`${selectedPosition?.fund_name || ''} - 交易明细`"
      width="900px"
    >
      <div v-if="selectedPosition" style="margin-bottom: 20px;">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="持有份额">
            {{ formatNumber(selectedPosition.shares, 2) }}
          </el-descriptions-item>
          <el-descriptions-item label="投入成本">
            {{ formatMoney(selectedPosition.cost_amount) }}
          </el-descriptions-item>
          <el-descriptions-item label="平均成本">
            {{ formatNumber(selectedPosition.avg_cost_nav, 4) }}
          </el-descriptions-item>
          <el-descriptions-item label="当前净值">
            {{ formatNumber(selectedPosition.current_nav, 4) }}
          </el-descriptions-item>
          <el-descriptions-item label="当前市值">
            {{ formatMoney(selectedPosition.current_value) }}
          </el-descriptions-item>
          <el-descriptions-item label="盈亏">
            <span :style="{ color: getReturnColor(selectedPosition.profit_loss) }">
              {{ formatMoney(selectedPosition.profit_loss) }} ({{ formatPercent(selectedPosition.profit_loss_rate) }})
            </span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <el-table :data="positionTransactions" border max-height="400">
        <el-table-column prop="transaction_date" label="日期" width="120" />
        <el-table-column prop="transaction_type" label="操作" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getTransactionTypeTag(row.transaction_type)"
              size="small"
            >
              {{ getTransactionTypeName(row.transaction_type) }}
            </el-tag>
          </template>
        </el-table-column>
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
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="handleEditTransaction(row)"
            >
              编辑
            </el-button>
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
    </el-dialog>

    <!-- 添加/编辑交易对话框 -->
    <el-dialog v-model="showTransactionDialog" :title="editingTransaction ? '编辑交易' : '添加交易'" width="600px" @open="loadFundList">
      <el-alert
        :title="portfolio.portfolio_type === 'private' ? '私募基金组合交易提示' : '公募基金组合交易提示'"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      >
        系统将自动从{{ portfolio.portfolio_type === 'private' ? '私募' : '公募' }}基金净值数据中获取交易净值，并自动计算份额。请确保已在{{ portfolio.portfolio_type === 'private' ? '私募基金净值管理' : '公募基金库' }}中添加并{{portfolio.portfolio_type === 'private' ? '录入了' : '抓取了' }}该基金的净值。
      </el-alert>

      <el-form :model="transactionForm" label-width="100px">
        <el-form-item label="交易类型" required>
          <el-radio-group v-model="transactionForm.transaction_type">
            <el-radio label="buy">买入</el-radio>
            <el-radio label="sell">卖出</el-radio>
            <el-radio label="cash_dividend">现金分红</el-radio>
            <el-radio label="reinvest_dividend">红利再投</el-radio>
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

        <!-- 买入/卖出/现金分红：显示金额输入 -->
        <el-form-item
          v-if="transactionForm.transaction_type !== 'reinvest_dividend'"
          label="交易金额"
          required
        >
          <el-input-number
            v-model="transactionForm.amount"
            :min="0"
            :precision="2"
            :controls="false"
            placeholder="请输入交易金额"
            style="width: 100%"
          />
          <span v-if="transactionForm.transaction_type === 'buy' || transactionForm.transaction_type === 'sell'" style="color: #909399; font-size: 12px;">
            系统将自动根据净值计算份额
          </span>
          <span v-else-if="transactionForm.transaction_type === 'cash_dividend'" style="color: #909399; font-size: 12px;">
            现金分红金额将减少投入成本，增加盈亏
          </span>
        </el-form-item>

        <!-- 红利再投：显示份额输入 -->
        <el-form-item
          v-if="transactionForm.transaction_type === 'reinvest_dividend'"
          label="分红份额"
          required
        >
          <el-input-number
            v-model="transactionForm.shares"
            :min="0"
            :precision="2"
            :controls="false"
            placeholder="请输入红利再投份额"
            style="width: 100%"
          />
          <span style="color: #909399; font-size: 12px;">
            红利再投份额将增加持仓，不改变成本
          </span>
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
        <el-button @click="handleCancelTransaction">取消</el-button>
        <el-button type="primary" :loading="addingTransaction" @click="handleAddTransaction">
          {{ editingTransaction ? '保存' : '确定' }}
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
import { navAPI } from '@/api/nav'  // 使用命名导入
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
const editingTransaction = ref(null)  // 正在编辑的交易记录
const transactionForm = ref({
  transaction_type: 'buy',
  fund_code: '',
  transaction_date: new Date().toISOString().split('T')[0],
  amount: 0,
  shares: 0,
  fee: 0,
  note: ''
})

// 持仓明细对话框
const showPositionDetailDialog = ref(false)
const selectedPosition = ref(null)
const positionTransactions = ref([])

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
    if (portfolio.value.portfolio_type === 'public') {
      // 加载公募基金列表
      const response = await publicFundAPI.getFundList({ page_size: 1000 })
      fundList.value = response.data
    } else {
      // 加载私募基金列表（从私募基金净值接口）
      const response = await navAPI.getFundsWithNav()
      fundList.value = response.data.funds
    }
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

// 编辑交易
const handleEditTransaction = (transaction) => {
  editingTransaction.value = transaction
  transactionForm.value = {
    transaction_type: transaction.transaction_type,
    fund_code: transaction.fund_code,
    transaction_date: transaction.transaction_date,
    amount: parseFloat(transaction.amount),
    shares: parseFloat(transaction.shares),
    fee: parseFloat(transaction.fee || 0),
    note: transaction.note || ''
  }
  showTransactionDialog.value = true
}

// 取消添加/编辑交易
const handleCancelTransaction = () => {
  showTransactionDialog.value = false
  editingTransaction.value = null
  // 重置表单
  transactionForm.value = {
    transaction_type: 'buy',
    fund_code: '',
    transaction_date: new Date().toISOString().split('T')[0],
    amount: 0,
    shares: 0,
    fee: 0,
    note: ''
  }
}

// 添加/更新交易
const handleAddTransaction = async () => {
  if (!transactionForm.value.fund_code) {
    ElMessage.warning('请选择基金')
    return
  }

  if (!transactionForm.value.transaction_date) {
    ElMessage.warning('请选择交易日期')
    return
  }

  // 根据交易类型验证必填字段
  if (transactionForm.value.transaction_type === 'reinvest_dividend') {
    // 红利再投：验证份额
    if (!transactionForm.value.shares || transactionForm.value.shares <= 0) {
      ElMessage.warning('请输入有效的分红份额')
      return
    }
  } else {
    // 买入/卖出/现金分红：验证金额
    if (!transactionForm.value.amount || transactionForm.value.amount <= 0) {
      ElMessage.warning('请输入有效的交易金额')
      return
    }
  }

  addingTransaction.value = true
  try {
    if (editingTransaction.value) {
      // 编辑模式：先删除旧记录，再添加新记录
      await portfolioAPI.deleteTransaction(route.params.id, editingTransaction.value.id)
      await portfolioAPI.addTransaction(route.params.id, transactionForm.value)
      ElMessage.success('修改成功')
    } else {
      // 新增模式
      await portfolioAPI.addTransaction(route.params.id, transactionForm.value)
      ElMessage.success('添加成功，系统已自动获取净值并计算份额')
    }

    showTransactionDialog.value = false

    // 重置表单
    transactionForm.value = {
      transaction_type: 'buy',
      fund_code: '',
      transaction_date: new Date().toISOString().split('T')[0],
      amount: 0,
      shares: 0,
      fee: 0,
      note: ''
    }
    editingTransaction.value = null

    // 重新加载数据
    await loadPortfolioDetail()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(error.response?.data?.detail || (editingTransaction.value ? '修改交易失败' : '添加交易失败'))
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

    // 如果明细对话框打开，更新明细数据
    if (showPositionDetailDialog.value && selectedPosition.value) {
      positionTransactions.value = transactions.value.filter(
        t => t.fund_code === selectedPosition.value.fund_code
      )
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除交易失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除交易失败')
    }
  }
}

// 显示持仓明细
const showPositionDetail = (position) => {
  selectedPosition.value = position
  // 筛选该基金的所有交易记录
  positionTransactions.value = transactions.value.filter(
    t => t.fund_code === position.fund_code
  )
  showPositionDetailDialog.value = true
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

// 获取交易类型名称
const getTransactionTypeName = (type) => {
  const typeMap = {
    'buy': '买入',
    'sell': '卖出',
    'cash_dividend': '现金分红',
    'reinvest_dividend': '红利再投'
  }
  return typeMap[type] || type
}

// 获取交易类型标签颜色
const getTransactionTypeTag = (type) => {
  const tagMap = {
    'buy': 'danger',
    'sell': 'success',
    'cash_dividend': 'warning',
    'reinvest_dividend': 'info'
  }
  return tagMap[type] || ''
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
