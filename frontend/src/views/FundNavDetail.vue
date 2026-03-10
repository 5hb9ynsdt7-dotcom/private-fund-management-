<template>
  <div class="fund-nav-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ name: 'NavManagement' }">
          净值管理
        </el-breadcrumb-item>
        <el-breadcrumb-item>基金详情</el-breadcrumb-item>
      </el-breadcrumb>

      <div class="fund-info">
        <h2>{{ fundInfo.fund_name || fundCode }}</h2>
        <div class="fund-meta">
          <span class="fund-code">基金代码: {{ fundCode }}</span>
          <span v-if="navRecords.length" class="record-count">
            · 共 {{ navRecords.length }} 条净值记录
          </span>
        </div>
      </div>
    </div>

    <!-- 数据完整性警告 -->
    <el-alert
      v-if="hasGapWarning"
      title="净值数据缺失警告"
      type="warning"
      :closable="false"
      show-icon
      class="gap-warning"
    >
      <template #default>
        <p>⚠ 该基金净值记录中存在超过 40 天未更新的区间，可能存在净值数据遗漏</p>
        <ul class="gap-list">
          <li v-for="(gap, index) in dataGaps" :key="index">
            {{ formatDate(gap.startDate) }} 至 {{ formatDate(gap.endDate) }}
            <span class="gap-days">(间隔 {{ gap.days }} 天)</span>
          </li>
        </ul>
      </template>
    </el-alert>

    <!-- 净值记录列表 -->
    <el-card class="table-section" shadow="hover">
      <template #header>
        <div class="table-header">
          <span>净值历史记录 (共 {{ navRecords.length }} 条)</span>
          <el-space>
            <el-button
              type="danger"
              :disabled="!selectedNavs.length"
              @click="handleBatchDelete"
            >
              <el-icon><Delete /></el-icon>
              批量删除 ({{ selectedNavs.length }})
            </el-button>
            <el-button @click="handleExport">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="goBack">
              <el-icon><Back /></el-icon>
              返回
            </el-button>
          </el-space>
        </div>
      </template>

      <!-- 净值数据表格 -->
      <el-table
        v-loading="tableLoading"
        :data="navRecords"
        style="width: 100%"
        stripe
        border
        highlight-current-row
        @selection-change="handleSelectionChange"
      >
        <!-- 选择列 -->
        <el-table-column
          type="selection"
          width="55"
          align="center"
        />

        <!-- 序号列 -->
        <el-table-column
          type="index"
          label="#"
          width="60"
          align="center"
        />

        <!-- 基金代码 -->
        <el-table-column
          label="基金代码"
          width="140"
          align="center"
        >
          <template #default>
            <span class="fund-code">{{ fundCode }}</span>
          </template>
        </el-table-column>

        <!-- 产品名称 -->
        <el-table-column
          label="产品名称"
          width="280"
          align="center"
        >
          <template #default>
            <span>{{ fundInfo.fund_name || fundCode }}</span>
          </template>
        </el-table-column>

        <!-- 净值日期 -->
        <el-table-column
          prop="nav_date"
          label="净值日期"
          width="180"
          sortable
          align="center"
        >
          <template #default="{ row }">
            <div class="date-cell-wrapper">
              <span class="date-cell">
                {{ formatDate(row.nav_date) }}
              </span>
              <span v-if="dividendDates.has(row.nav_date)" class="dividend-badge">
                （分红）
              </span>
            </div>
          </template>
        </el-table-column>

        <!-- 单位净值 -->
        <el-table-column
          prop="unit_nav"
          label="单位净值"
          width="140"
          sortable
          align="center"
        >
          <template #default="{ row }">
            <span class="nav-value">
              {{ formatNumber(row.unit_nav, 4) }}
            </span>
          </template>
        </el-table-column>

        <!-- 累计净值 -->
        <el-table-column
          prop="accum_nav"
          label="累计净值"
          width="140"
          sortable
          align="center"
        >
          <template #default="{ row }">
            <span class="nav-value">
              {{ formatNumber(row.accum_nav, 4) }}
            </span>
          </template>
        </el-table-column>

        <!-- 复权累计净值 -->
        <el-table-column
          prop="adjusted_accum_nav"
          label="复权累计净值"
          width="160"
          sortable
          align="center"
        >
          <template #default="{ row }">
            <span class="nav-value" style="color: #409EFF; font-weight: 600;">
              {{ row.adjusted_accum_nav ? formatNumber(row.adjusted_accum_nav, 4) : '-' }}
            </span>
          </template>
        </el-table-column>

        <!-- 涨跌幅 -->
        <el-table-column
          label="涨跌幅"
          width="120"
          align="center"
        >
          <template #default="{ row, $index }">
            <span
              v-if="$index < navRecords.length - 1"
              :class="getChangeClass(row, $index)"
            >
              {{ calculateDailyChange(row, $index) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column
          label="操作"
          width="100"
          align="center"
          fixed="right"
        >
          <template #default="{ row }">
            <el-tooltip content="删除">
              <el-button
                type="danger"
                size="small"
                circle
                @click="handleDelete(row)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { navAPI } from '@/api/nav'
import { formatDate, formatNumber } from '@/utils'

const route = useRoute()
const router = useRouter()

// 获取基金代码
const fundCode = ref(route.params.fundCode)

// 页面状态
const tableLoading = ref(false)
const fundInfo = ref({})
const navRecords = ref([])
const selectedNavs = ref([])
const dividendDates = ref(new Set()) // 存储分红日期的Set

// 计算数据缺失区间
const dataGaps = computed(() => {
  const gaps = []
  if (navRecords.value.length < 2) return gaps

  for (let i = 0; i < navRecords.value.length - 1; i++) {
    const currentDate = new Date(navRecords.value[i].nav_date)
    const nextDate = new Date(navRecords.value[i + 1].nav_date)
    const daysDiff = Math.abs((currentDate - nextDate) / (1000 * 60 * 60 * 24))

    if (daysDiff > 40) {
      gaps.push({
        startDate: navRecords.value[i + 1].nav_date,
        endDate: navRecords.value[i].nav_date,
        days: Math.floor(daysDiff)
      })
    }
  }

  return gaps
})

// 是否有数据缺失警告
const hasGapWarning = computed(() => dataGaps.value.length > 0)

// 加载基金信息和净值记录
const loadFundData = async () => {
  tableLoading.value = true
  try {
    const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8003'

    // 并发获取净值数据和分红数据
    const [navResponse, dividendResponse] = await Promise.all([
      fetch(`${API_BASE}/api/nav/fund/${fundCode.value}/with-adjusted-nav?limit=10000`),
      fetch(`${API_BASE}/api/dividend/fund/${fundCode.value}/history`)
    ])

    const navResult = await navResponse.json()
    const dividendResult = await dividendResponse.json()

    if (navResult.success) {
      navRecords.value = navResult.data.nav_records || []

      // 按日期倒序排列
      navRecords.value.sort((a, b) => {
        const dateA = new Date(a.nav_date)
        const dateB = new Date(b.nav_date)
        return dateB - dateA
      })

      // 如果有净值记录，获取基金信息
      if (navRecords.value.length > 0) {
        fundInfo.value = {
          fund_code: fundCode.value,
          fund_name: navRecords.value[0].fund_name || fundCode.value
        }
      }

      console.log(`加载完成: 基金 ${fundCode.value} 共 ${navRecords.value.length} 条净值记录`)
    } else {
      throw new Error(navResult.message || '加载失败')
    }

    // 处理分红数据
    if (dividendResult.dividend_history && dividendResult.dividend_history.length > 0) {
      const dates = new Set(
        dividendResult.dividend_history.map(d => d.ex_dividend_date)
      )
      dividendDates.value = dates
      console.log(`加载完成: 基金 ${fundCode.value} 共 ${dates.size} 次分红`)
    }

  } catch (error) {
    console.error('加载基金数据失败:', error)
    ElMessage.error('加载基金数据失败')
    navRecords.value = []
  } finally {
    tableLoading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  selectedNavs.value = []
  loadFundData()
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedNavs.value = selection
}

// 计算日涨跌幅（基于复权累计净值）
const calculateDailyChange = (row, index) => {
  if (index >= navRecords.value.length - 1) return '-'

  const currentAdjustedNav = row.adjusted_accum_nav || parseFloat(row.unit_nav)
  const previousAdjustedNav = navRecords.value[index + 1].adjusted_accum_nav || parseFloat(navRecords.value[index + 1].unit_nav)

  if (previousAdjustedNav === 0) return '-'

  const change = ((currentAdjustedNav - previousAdjustedNav) / previousAdjustedNav) * 100
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

// 获取涨跌幅样式类（基于复权累计净值）
const getChangeClass = (row, index) => {
  if (index >= navRecords.value.length - 1) return ''

  const currentAdjustedNav = row.adjusted_accum_nav || parseFloat(row.unit_nav)
  const previousAdjustedNav = navRecords.value[index + 1].adjusted_accum_nav || parseFloat(navRecords.value[index + 1].unit_nav)
  const change = currentAdjustedNav - previousAdjustedNav

  if (change > 0) return 'text-success'
  if (change < 0) return 'text-danger'
  return 'text-muted'
}

// 计算间隔天数
const calculateDayGap = (row, index) => {
  if (index >= navRecords.value.length - 1) return '-'

  const currentDate = new Date(row.nav_date)
  const nextDate = new Date(navRecords.value[index + 1].nav_date)
  const daysDiff = Math.abs((currentDate - nextDate) / (1000 * 60 * 60 * 24))

  return Math.floor(daysDiff)
}

// 处理删除单条净值
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${formatDate(row.nav_date)} 的净值记录吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await navAPI.deleteNav(row.id)
    ElMessage.success('删除成功')
    refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除净值
const handleBatchDelete = async () => {
  if (!selectedNavs.value.length) {
    ElMessage.warning('请先选择要删除的记录')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedNavs.value.length} 条净值记录吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedNavs.value.map(nav => nav.id)
    await navAPI.batchDeleteNav(ids)
    ElMessage.success(`成功删除 ${ids.length} 条记录`)
    refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 导出数据
const handleExport = () => {
  // 检查是否有选中的记录
  const dataToExport = selectedNavs.value.length > 0
    ? selectedNavs.value
    : navRecords.value

  if (dataToExport.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }

  try {
    // 创建CSV内容
    const headers = ['基金代码', '产品名称', '净值日期', '单位净值', '累计净值', '涨跌幅', '间隔天数']
    let csvContent = '\ufeff' + headers.join(',') + '\n' // \ufeff 是 BOM，确保Excel正确识别UTF-8

    // 按日期倒序排序
    const sortedData = [...dataToExport].sort((a, b) => {
      return new Date(b.nav_date) - new Date(a.nav_date)
    })

    // 添加数据行
    sortedData.forEach((row, index) => {
      const fundCodeValue = fundCode.value
      const fundName = fundInfo.value.fund_name || fundCode.value
      const navDate = formatDate(row.nav_date)
      const unitNav = formatNumber(row.unit_nav, 4)
      const accumNav = formatNumber(row.accum_nav, 4)

      // 计算涨跌幅
      let changePercent = '-'
      if (index < sortedData.length - 1) {
        const currentNav = parseFloat(row.unit_nav)
        const previousNav = parseFloat(sortedData[index + 1].unit_nav)
        if (previousNav !== 0) {
          const change = ((currentNav - previousNav) / previousNav) * 100
          const sign = change > 0 ? '+' : ''
          changePercent = `${sign}${change.toFixed(2)}%`
        }
      }

      // 计算间隔天数
      let dayGap = '-'
      if (index < sortedData.length - 1) {
        const currentDate = new Date(row.nav_date)
        const nextDate = new Date(sortedData[index + 1].nav_date)
        const daysDiff = Math.abs((currentDate - nextDate) / (1000 * 60 * 60 * 24))
        dayGap = Math.floor(daysDiff).toString()
      }

      const rowData = [fundCodeValue, fundName, navDate, unitNav, accumNav, changePercent, dayGap]
      csvContent += rowData.join(',') + '\n'
    })

    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    // 设置文件名
    const today = new Date().toISOString().split('T')[0]
    const recordCount = dataToExport.length
    const fileName = selectedNavs.value.length > 0
      ? `${fundCode.value}_净值记录_已选${recordCount}条_${today}.csv`
      : `${fundCode.value}_净值记录_全部${recordCount}条_${today}.csv`

    link.setAttribute('href', url)
    link.setAttribute('download', fileName)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success(`成功导出 ${recordCount} 条净值记录`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  }
}

// 返回上一页
const goBack = () => {
  router.push({ name: 'NavManagement' })
}

// 初始化
onMounted(() => {
  loadFundData()
})
</script>

<style scoped>
.fund-nav-detail {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header .el-breadcrumb {
  margin-bottom: 16px;
}

.fund-info h2 {
  color: #303133;
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 600;
}

.fund-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.fund-code {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.record-count {
  color: #909399;
}

.gap-warning {
  margin-bottom: 24px;
}

.gap-warning :deep(.el-alert__content) {
  width: 100%;
}

.gap-warning p {
  margin: 0 0 12px 0;
  font-weight: 600;
  color: #E6A23C;
}

.gap-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.gap-list li {
  margin-bottom: 6px;
}

.gap-days {
  font-weight: 600;
  color: #F56C6C;
}

.table-section {
  margin-bottom: 24px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header span {
  font-weight: 600;
  color: #303133;
}

.date-cell {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.date-cell-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.dividend-badge {
  font-size: 11px;
  color: #F56C6C;
  font-weight: 600;
}

.nav-value {
  font-weight: 500;
}

.text-success {
  color: #F56C6C;
  font-weight: 600;
}

.text-danger {
  color: #67C23A;
  font-weight: 600;
}

.text-muted {
  color: #909399;
}

/* 表格样式优化 */
.el-table {
  font-size: 13px;
}

.el-table th {
  background-color: #fafafa;
  color: #303133;
  font-weight: 600;
}

.el-table td {
  padding: 12px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .fund-nav-detail {
    padding: 16px;
  }

  .page-header {
    margin-bottom: 16px;
  }

  .fund-info h2 {
    font-size: 20px;
  }

  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .table-header .el-space {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .fund-nav-detail {
    padding: 12px;
  }

  .gap-warning {
    margin-bottom: 16px;
  }
}
</style>
