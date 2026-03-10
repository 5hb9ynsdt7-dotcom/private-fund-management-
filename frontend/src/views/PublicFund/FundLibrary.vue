<template>
  <div class="fund-library-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">公募基金库</h2>
      <div class="header-actions">
        <el-button type="success" @click="handleRefreshAllNav" :loading="refreshingAll">
          <el-icon><Refresh /></el-icon>
          批量刷新净值
        </el-button>
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加基金
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" :inline="true">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="基金代码或名称"
            clearable
            style="width: 200px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 基金列表表格 -->
    <el-card class="table-card" shadow="never">
      <template #header>
        <div class="table-header">
          <span>基金列表</span>
          <div class="table-actions">
            <el-button
              v-if="selectedFunds.length > 0"
              type="primary"
              @click="showPerformanceDialog = true"
            >
              <el-icon><TrendCharts /></el-icon>
              生成阶段涨幅卡片 ({{ selectedFunds.length }}个)
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="fundList"
        border
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" fixed />
        <el-table-column prop="fund_code" label="基金代码" width="120" fixed />
        <el-table-column prop="fund_name" label="基金名称" min-width="300" show-overflow-tooltip />
        <el-table-column prop="latest_nav_date" label="最新净值日期" width="140">
          <template #default="{ row }">
            {{ row.latest_nav_date || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '运行中' : '已清盘' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="success" link size="small" @click="handleRefreshNav(row)" :loading="row._refreshing">
              刷新净值
            </el-button>
            <el-button type="primary" link size="small" @click="goToDetail(row.fund_code)">
              查看
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 添加基金对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加基金"
      width="600px"
      @close="resetAddForm"
    >
      <el-tabs v-model="addMethod">
        <el-tab-pane label="自动抓取" name="auto">
          <el-form :model="autoForm" label-width="100px">
            <el-form-item label="基金代码">
              <el-input
                v-model="autoForm.fund_code"
                placeholder="请输入6位数字基金代码"
                maxlength="6"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="fetching" @click="handleAutoFetch">
                自动抓取
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="手动录入" name="manual">
          <el-form :model="manualForm" label-width="100px">
            <el-form-item label="基金代码" required>
              <el-input v-model="manualForm.fund_code" placeholder="6位数字" maxlength="6" />
            </el-form-item>
            <el-form-item label="基金名称" required>
              <el-input v-model="manualForm.fund_name" placeholder="请输入基金名称" />
            </el-form-item>
            <el-form-item label="基金类型">
              <el-select v-model="manualForm.fund_type" placeholder="请选择">
                <el-option label="股票型" value="股票型" />
                <el-option label="债券型" value="债券型" />
                <el-option label="混合型" value="混合型" />
                <el-option label="货币型" value="货币型" />
                <el-option label="QDII" value="QDII" />
              </el-select>
            </el-form-item>
            <el-form-item label="基金公司">
              <el-input v-model="manualForm.fund_company" placeholder="请输入基金公司" />
            </el-form-item>
            <el-form-item label="基金经理">
              <el-input v-model="manualForm.fund_manager" placeholder="请输入基金经理" />
            </el-form-item>
            <el-form-item label="成立日期">
              <el-date-picker
                v-model="manualForm.establish_date"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="handleManualCreate">
                创建基金
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 阶段涨幅对话框 -->
    <el-dialog
      v-model="showPerformanceDialog"
      title="生成阶段涨幅卡片"
      width="1100px"
      @close="resetPerformanceForm"
    >
      <el-form :model="performanceForm" label-width="120px">
        <el-form-item label="时间范围">
          <el-radio-group v-model="performanceForm.dateMode" @change="handleDateModeChange">
            <el-radio value="preset">上周一到本周一</el-radio>
            <el-radio value="custom">自定义</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="performanceForm.dateMode === 'custom'" label="起始日期">
          <el-date-picker
            v-model="performanceForm.startDate"
            type="date"
            placeholder="选择起始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item v-if="performanceForm.dateMode === 'custom'" label="结束日期">
          <el-date-picker
            v-model="performanceForm.endDate"
            type="date"
            placeholder="选择结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item label="对比基准">
          <el-select v-model="performanceForm.benchmark" placeholder="请选择基准指数（可选）" clearable style="width: 200px">
            <el-option label="无" value="" />
            <el-option label="沪深300" value="000300.SH" />
            <el-option label="中证500" value="000905.SH" />
            <el-option label="中证1000" value="000852.SH" />
            <el-option label="中证2000" value="932000.CSI" />
          </el-select>
        </el-form-item>

        <el-form-item label="已选基金">
          <el-tag
            v-for="fund in selectedFunds"
            :key="fund.fund_code"
            closable
            @close="removeSelectedFund(fund)"
            style="margin-right: 8px; margin-bottom: 8px"
          >
            {{ fund.fund_code }} - {{ fund.fund_name }}
          </el-tag>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="generatePerformanceCard" :loading="generatingPerformance">
            生成卡片
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 涨幅卡片展示 -->
      <div v-if="performanceData.length > 0" class="performance-cards-section">
        <el-divider content-position="left">
          <span style="font-weight: 600">阶段涨幅数据</span>
        </el-divider>

        <el-table :data="performanceData" border stripe style="width: 100%">
          <el-table-column prop="fund_code" label="产品代码" width="100" fixed />
          <el-table-column prop="short_name" label="产品简称" width="150" show-overflow-tooltip />
          <el-table-column prop="nav_date" label="净值日期" width="110" />
          <el-table-column prop="nav" label="净值" width="100" align="right">
            <template #default="{ row }">
              {{ row.nav ? row.nav.toFixed(2) : '--' }}
            </template>
          </el-table-column>
          <el-table-column prop="stage_return" label="阶段涨跌幅" width="130" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.stage_return >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ row.stage_return !== null && row.stage_return !== undefined ? (row.stage_return > 0 ? '+' : '') + row.stage_return.toFixed(2) + '%' : '--' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="ytd_return" label="今年以来涨跌幅" width="150" align="right">
            <template #default="{ row }">
              <span :style="{ color: row.ytd_return >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ row.ytd_return !== null && row.ytd_return !== undefined ? (row.ytd_return > 0 ? '+' : '') + row.ytd_return.toFixed(2) + '%' : '--' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="compare_date" label="对比日期" width="110" />
          <el-table-column prop="compare_nav" label="对比净值" width="100" align="right">
            <template #default="{ row }">
              {{ row.compare_nav ? row.compare_nav.toFixed(2) : '--' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, TrendCharts } from '@element-plus/icons-vue'
import publicFundAPI from '@/api/publicFund'
import axios from 'axios'

const router = useRouter()
const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8003'

// 搜索表单
const searchForm = reactive({
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 基金列表
const fundList = ref([])
const loading = ref(false)
const refreshingAll = ref(false)

// 选中的基金
const selectedFunds = ref([])

// 阶段涨幅对话框
const showPerformanceDialog = ref(false)
const generatingPerformance = ref(false)
const performanceData = ref([])
const performanceForm = reactive({
  dateMode: 'preset', // 'preset' or 'custom'
  startDate: null,
  endDate: null,
  benchmark: '' // 基准指数代码
})

// 添加基金对话框
const showAddDialog = ref(false)
const addMethod = ref('auto')
const fetching = ref(false)
const submitting = ref(false)

const autoForm = reactive({
  fund_code: ''
})

const manualForm = reactive({
  fund_code: '',
  fund_name: '',
  fund_type: '',
  fund_company: '',
  fund_manager: '',
  establish_date: ''
})

// 加载基金列表
const loadFundList = async () => {
  loading.value = true
  try {
    const params = {
      keyword: searchForm.keyword || undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }

    const response = await publicFundAPI.getFundList(params)
    fundList.value = response.data.map(fund => ({
      ...fund,
      _refreshing: false  // 为每个基金添加刷新状态
    }))
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载基金列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadFundList()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  handleSearch()
}

// 刷新净值
const handleRefreshNav = async (row) => {
  row._refreshing = true
  try {
    const response = await publicFundAPI.refreshNav(row.fund_code)
    if (response.success) {
      ElMessage.success(response.message)
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('刷新失败：' + (error.message || '未知错误'))
  } finally {
    row._refreshing = false
  }
}

// 批量刷新所有净值
const handleRefreshAllNav = async () => {
  ElMessageBox.confirm(
    '确定要刷新所有基金的净值吗？这可能需要一些时间。',
    '批量刷新确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(async () => {
      refreshingAll.value = true
      try {
        const response = await publicFundAPI.refreshAllNav()
        if (response.success) {
          const data = response.data || {}
          const successCount = data.success_count || 0
          const failedCount = data.failed_count || 0

          if (failedCount > 0) {
            ElMessage.warning(`${response.message}`)
          } else {
            ElMessage.success(`批量刷新成功！共刷新 ${successCount} 个基金净值`)
          }

          // 刷新列表
          await loadFundList()
        } else {
          ElMessage.error(response.message || '批量刷新失败')
        }
      } catch (error) {
        ElMessage.error('批量刷新失败：' + (error.message || '未知错误'))
      } finally {
        refreshingAll.value = false
      }
    })
    .catch(() => {})
}

// 分页变化
const handleSizeChange = (size) => {
  pagination.page_size = size
  loadFundList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadFundList()
}

// 自动抓取
const handleAutoFetch = async () => {
  if (!autoForm.fund_code || autoForm.fund_code.length !== 6) {
    ElMessage.warning('请输入6位数字基金代码')
    return
  }

  fetching.value = true
  try {
    const response = await publicFundAPI.fetchFund(autoForm.fund_code)
    if (response.success) {
      ElMessage.success(response.message)
      showAddDialog.value = false
      loadFundList()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('自动抓取失败：' + error.message)
  } finally {
    fetching.value = false
  }
}

// 手动创建
const handleManualCreate = async () => {
  if (!manualForm.fund_code || !manualForm.fund_name) {
    ElMessage.warning('请填写基金代码和名称')
    return
  }

  submitting.value = true
  try {
    await publicFundAPI.createFund(manualForm)
    ElMessage.success('创建成功')
    showAddDialog.value = false
    loadFundList()
  } catch (error) {
    ElMessage.error('创建失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 重置添加表单
const resetAddForm = () => {
  autoForm.fund_code = ''
  manualForm.fund_code = ''
  manualForm.fund_name = ''
  manualForm.fund_type = ''
  manualForm.fund_company = ''
  manualForm.fund_manager = ''
  manualForm.establish_date = ''
}

// 删除基金
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除基金 ${row.fund_name}？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await publicFundAPI.deleteFund(row.fund_code)
        ElMessage.success('删除成功')
        loadFundList()
      } catch (error) {
        ElMessage.error('删除失败：' + error.message)
      }
    })
    .catch(() => {})
}

// 跳转详情页
const goToDetail = (fundCode) => {
  router.push({
    name: 'PublicFundDetail',
    params: { fundCode }
  })
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedFunds.value = selection
}

// 移除选中的基金
const removeSelectedFund = (fund) => {
  selectedFunds.value = selectedFunds.value.filter(f => f.fund_code !== fund.fund_code)
}

// 处理日期模式变化
const handleDateModeChange = (mode) => {
  if (mode === 'preset') {
    // 计算上周一到本周一
    const today = new Date()
    const dayOfWeek = today.getDay() // 0 is Sunday, 1 is Monday, etc.
    const daysToMonday = dayOfWeek === 0 ? 1 : (8 - dayOfWeek) // Days until next Monday

    // 本周一
    const thisMonday = new Date(today)
    thisMonday.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1))

    // 上周一
    const lastMonday = new Date(thisMonday)
    lastMonday.setDate(thisMonday.getDate() - 7)

    performanceForm.startDate = formatDate(lastMonday)
    performanceForm.endDate = formatDate(thisMonday)
  }
}

// 格式化日期
const formatDate = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 重置阶段涨幅表单
const resetPerformanceForm = () => {
  performanceForm.dateMode = 'preset'
  performanceForm.startDate = null
  performanceForm.endDate = null
  performanceData.value = []
}

// 生成阶段涨幅卡片
const generatePerformanceCard = async () => {
  if (selectedFunds.value.length === 0) {
    ElMessage.warning('请先选择基金')
    return
  }

  // 确定日期范围
  let startDate, endDate
  if (performanceForm.dateMode === 'preset') {
    handleDateModeChange('preset')
    startDate = performanceForm.startDate
    endDate = performanceForm.endDate
  } else {
    if (!performanceForm.startDate || !performanceForm.endDate) {
      ElMessage.warning('请选择起始和结束日期')
      return
    }
    startDate = performanceForm.startDate
    endDate = performanceForm.endDate
  }

  generatingPerformance.value = true
  try {
    const fundCodes = selectedFunds.value.map(f => f.fund_code)
    const response = await axios.post(`${API_BASE}/api/public-fund/stage-performance`, {
      fund_codes: fundCodes,
      start_date: startDate,
      end_date: endDate,
      benchmark: performanceForm.benchmark || undefined
    })

    if (response.data.success) {
      performanceData.value = response.data.data
      ElMessage.success('生成成功')
    } else {
      ElMessage.error(response.data.message || '生成失败')
    }
  } catch (error) {
    console.error('生成阶段涨幅卡片失败:', error)
    ElMessage.error('生成失败：' + (error.response?.data?.detail || error.message))
  } finally {
    generatingPerformance.value = false
  }
}

onMounted(() => {
  loadFundList()
})
</script>

<style scoped>
.fund-library-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: #333;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.performance-cards-section {
  margin-top: 24px;
}
</style>
