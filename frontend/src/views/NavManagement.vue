<template>
  <div class="nav-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>净值管理</h2>
      <p class="page-description">批量上传和管理基金净值数据</p>
    </div>

    <!-- 操作区域 -->
    <el-row :gutter="24" class="action-section">
      <!-- 文件上传 -->
      <el-col :lg="12" :md="24">
        <el-card title="批量上传" shadow="hover" class="upload-card">
          <template #header>
            <div class="card-header">
              <span>批量上传</span>
              <el-tooltip content="下载模板可以确保数据格式正确">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <ExcelUploader
            ref="uploaderRef"
            :upload-api="uploadNavFiles"
            template-url="/templates/nav_template.xlsx"
            @success="handleUploadSuccess"
            @error="handleUploadError"
            @progress="handleUploadProgress"
          />
        </el-card>
      </el-col>

      <!-- 手动添加 -->
      <el-col :lg="12" :md="24">
        <el-card title="手动添加" shadow="hover" class="manual-add-card">
          <template #header>
            <div class="card-header">
              <span>手动添加</span>
              <el-tooltip content="单个基金净值快速录入">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          <NavManualForm @success="handleAddSuccess" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 基金产品列表 -->
    <el-card class="table-section" shadow="hover">
      <template #header>
        <div class="table-header">
          <span>基金产品列表</span>
          <el-space>
            <el-button
              type="success"
              :disabled="!selectedFunds.length"
              @click="handleBatchExport"
            >
              <el-icon><Download /></el-icon>
              导出净值 ({{ selectedFunds.length }})
            </el-button>
            <el-button
              type="danger"
              :disabled="!selectedFunds.length"
              @click="handleBatchDeleteFunds"
            >
              <el-icon><Delete /></el-icon>
              删除基金 ({{ selectedFunds.length }})
            </el-button>
            <el-button @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button
              type="warning"
              @click="handleRecalculateAdjusted"
              :loading="recalculatingAdjusted"
            >
              <el-icon><Tools /></el-icon>
              计算复权净值
            </el-button>
          </el-space>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索基金代码或基金名称"
          clearable
          style="max-width: 400px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 基金列表表格 -->
      <el-table
        v-loading="tableLoading"
        :data="filteredFundList"
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
          prop="fund_code"
          label="基金代码"
          width="140"
          sortable
        >
          <template #default="{ row }">
            <el-link
              type="primary"
              @click.stop="viewFundDetail(row.fund_code)"
            >
              {{ row.fund_code }}
            </el-link>
          </template>
        </el-table-column>

        <!-- 基金名称 -->
        <el-table-column
          prop="fund_name"
          label="基金名称"
          sortable
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ row.fund_name }}
            <span v-if="row.dividend_count > 0" class="dividend-badge">
              (分红{{ row.dividend_count }}次)
            </span>
          </template>
        </el-table-column>

        <!-- 产品特征 -->
        <el-table-column
          prop="product_features"
          label="产品特征"
          align="center"
        >
          <template #default="{ row }">
            <div
              class="product-features-cell"
              @click.stop="openProductFeaturesDialog(row)"
            >
              <span v-if="row.product_features" class="features-text">
                {{ row.product_features }}
              </span>
              <span v-else class="features-placeholder">
                点击编辑产品特征
              </span>
              <el-icon class="edit-icon">
                <Edit />
              </el-icon>
            </div>
          </template>
        </el-table-column>

        <!-- 最新净值日期 -->
        <el-table-column
          prop="latest_nav_date"
          label="最新净值日期"
          width="150"
          sortable
          :sort-method="sortByDate"
          :default-sort="{ prop: 'latest_nav_date', order: 'descending' }"
          align="center"
        >
          <template #default="{ row }">
            <span class="date-cell">
              {{ formatDate(row.latest_nav_date) }}
            </span>
          </template>
        </el-table-column>

        <!-- 操作列 -->
        <el-table-column
          label="操作"
          width="250"
          align="center"
        >
          <template #default="{ row }">
            <el-space>
              <el-tooltip content="查看详情">
                <el-button
                  type="primary"
                  size="small"
                  @click.stop="viewFundDetail(row.fund_code)"
                >
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
              </el-tooltip>

              <el-tooltip content="分红录入">
                <el-button
                  type="warning"
                  size="small"
                  @click.stop="handleDividendManage(row)"
                >
                  <el-icon><Money /></el-icon>
                  分红
                </el-button>
              </el-tooltip>

              <el-tooltip content="删除基金">
                <el-button
                  type="danger"
                  size="small"
                  circle
                  @click.stop="handleDeleteFund(row)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 分红管理对话框 -->
    <el-dialog
      v-model="dividendDialogVisible"
      :title="`分红管理 - ${currentFund?.fund_code} ${currentFund?.fund_name}`"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="dividend-management">
        <!-- 添加分红按钮 -->
        <div class="dividend-header">
          <el-button
            type="primary"
            @click="handleAddDividend"
          >
            <el-icon><Plus /></el-icon>
            新增分红记录
          </el-button>
        </div>

        <!-- 分红记录列表 -->
        <el-table
          :data="dividendList"
          v-loading="dividendLoading"
          stripe
          border
          style="margin-top: 16px"
        >
          <el-table-column
            type="index"
            label="#"
            width="60"
            align="center"
          />

          <el-table-column
            prop="ex_dividend_date"
            label="基准日（除息日）"
            width="150"
            align="center"
          >
            <template #default="{ row }">
              {{ row.ex_dividend_date || '--' }}
            </template>
          </el-table-column>

          <el-table-column
            prop="dividend_date"
            label="分红日期"
            width="150"
            align="center"
          >
            <template #default="{ row }">
              {{ row.dividend_date || '--' }}
            </template>
          </el-table-column>

          <el-table-column
            prop="pre_dividend_nav"
            label="除权前净值"
            width="140"
            align="center"
          >
            <template #default="{ row }">
              {{ row.pre_dividend_nav ? Number(row.pre_dividend_nav).toFixed(4) : '--' }}
            </template>
          </el-table-column>

          <el-table-column
            prop="dividend_per_share"
            label="分红方案（元/份）"
            width="160"
            align="center"
          >
            <template #default="{ row }">
              <span style="color: #F56C6C; font-weight: 500;">
                {{ Number(row.dividend_per_share).toFixed(4) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column
            label="操作"
            width="160"
            align="center"
          >
            <template #default="{ row }">
              <el-space>
                <el-button
                  type="primary"
                  size="small"
                  link
                  @click="handleEditDividend(row)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  link
                  @click="handleDeleteDividend(row)"
                >
                  删除
                </el-button>
              </el-space>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <el-empty
          v-if="!dividendLoading && dividendList.length === 0"
          description="暂无分红记录"
          :image-size="100"
        />
      </div>

      <template #footer>
        <el-button @click="dividendDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 产品特征编辑对话框 -->
    <el-dialog
      v-model="productFeaturesDialogVisible"
      :title="`编辑产品特征 - ${currentEditFund?.fund_code} ${currentEditFund?.fund_name}`"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="基金代码">
          <el-text>{{ currentEditFund?.fund_code }}</el-text>
        </el-form-item>

        <el-form-item label="基金名称">
          <el-text>{{ currentEditFund?.fund_name }}</el-text>
        </el-form-item>

        <el-form-item label="产品特征">
          <el-input
            v-model="editingProductFeatures"
            type="textarea"
            :rows="8"
            placeholder="请输入产品特征描述"
            maxlength="1000"
            show-word-limit
          />
          <div class="form-tip">
            可以输入产品的主要特征、投资策略、风险等级等信息
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="productFeaturesDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleSaveProductFeatures"
          :loading="productFeaturesSubmitting"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 分红录入/编辑对话框 -->
    <el-dialog
      v-model="dividendFormDialogVisible"
      :title="dividendFormMode === 'add' ? '新增分红记录' : '编辑分红记录'"
      width="550px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="dividendFormRef"
        :model="dividendForm"
        :rules="dividendFormRules"
        label-width="140px"
      >
        <el-form-item label="基金代码">
          <el-text>{{ currentFund?.fund_code }}</el-text>
        </el-form-item>

        <el-form-item label="基金名称">
          <el-text>{{ currentFund?.fund_name }}</el-text>
        </el-form-item>

        <el-form-item label="基准日（除息日）" prop="exDividendDate">
          <el-date-picker
            v-model="dividendForm.exDividendDate"
            type="date"
            placeholder="选择基准日（除息日）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="除权前净值" prop="preDividendNav">
          <el-input-number
            v-model="dividendForm.preDividendNav"
            :precision="4"
            :step="0.0001"
            :min="0"
            placeholder="请输入除权前净值"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="分红方案（元/份）" prop="dividendPerShare">
          <el-input-number
            v-model="dividendForm.dividendPerShare"
            :precision="4"
            :step="0.0001"
            :min="0"
            placeholder="请输入每份分红金额"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dividendFormDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleSubmitDividend"
          :loading="dividendSubmitting"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import ExcelUploader from '@/components/ExcelUploader.vue'
import NavManualForm from '@/components/NavManualForm.vue'
import { navAPI } from '@/api/nav'
import { formatDate, formatNumber } from '@/utils'
import axios from 'axios'

const router = useRouter()
const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000'

// 页面状态
const uploaderRef = ref()
const tableLoading = ref(false)
const selectedFunds = ref([])
const fundList = ref([])
const searchKeyword = ref('')
const recalculatingAdjusted = ref(false) // 计算复权净值loading状态

// 分红管理相关状态
const dividendDialogVisible = ref(false)
const dividendFormDialogVisible = ref(false)
const dividendLoading = ref(false)
const dividendSubmitting = ref(false)
const currentFund = ref(null)
const dividendList = ref([])
const dividendFormMode = ref('add') // 'add' 或 'edit'
const dividendFormRef = ref(null)
const currentDividend = ref(null)

// 产品特征编辑相关状态
const productFeaturesDialogVisible = ref(false)
const productFeaturesSubmitting = ref(false)
const currentEditFund = ref(null)
const editingProductFeatures = ref('')

// 分红表单
const dividendForm = ref({
  exDividendDate: '',
  preDividendNav: null,
  dividendPerShare: null
})

// 分红表单验证规则
const dividendFormRules = {
  exDividendDate: [
    { required: true, message: '请选择基准日（除息日）', trigger: 'change' }
  ],
  preDividendNav: [
    { required: true, message: '请输入除权前净值', trigger: 'blur' },
    { type: 'number', min: 0.0001, message: '除权前净值必须大于0', trigger: 'blur' }
  ],
  dividendPerShare: [
    { required: true, message: '请输入分红方案', trigger: 'blur' },
    { type: 'number', min: 0.0001, message: '分红金额必须大于0', trigger: 'blur' }
  ]
}

// 过滤后的基金列表
const filteredFundList = computed(() => {
  if (!searchKeyword.value) {
    return fundList.value
  }

  const keyword = searchKeyword.value.toLowerCase()
  return fundList.value.filter(fund => {
    return fund.fund_code.toLowerCase().includes(keyword) ||
           fund.fund_name.toLowerCase().includes(keyword)
  })
})

// 上传净值文件
const uploadNavFiles = async (files) => {
  try {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append(`files`, file)
    })

    const response = await navAPI.uploadNavFiles(formData)
    return response
  } catch (error) {
    throw new Error(error.message || '上传失败')
  }
}

// 处理上传成功
const handleUploadSuccess = (result) => {
  console.log('上传成功:', result)
  ElMessage.success('净值数据上传成功')
  refreshData()
}

// 处理上传错误
const handleUploadError = (error) => {
  console.error('上传失败:', error)
  ElMessage.error('净值数据上传失败')
}

// 处理上传进度
const handleUploadProgress = ({ uploading }) => {
  // 可以在这里显示进度条
}

// 处理手动添加成功
const handleAddSuccess = (data) => {
  console.log('手动添加成功:', data)
  ElMessage.success('净值记录添加成功')
  refreshData()
}

// 加载基金列表
const loadFundList = async () => {
  tableLoading.value = true
  try {
    const response = await navAPI.getFundsWithNav()
    fundList.value = response.data.funds || []

    // 按最新净值日期倒序排列
    fundList.value.sort((a, b) => {
      const dateA = new Date(a.latest_nav_date || '1970-01-01')
      const dateB = new Date(b.latest_nav_date || '1970-01-01')
      return dateB - dateA
    })

    console.log(`加载完成: 共 ${fundList.value.length} 个基金`)
  } catch (error) {
    console.error('加载基金列表失败:', error)
    ElMessage.error('加载基金列表失败')
    fundList.value = []
  } finally {
    tableLoading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  selectedFunds.value = []
  loadFundList()
}

// 计算复权净值
const handleRecalculateAdjusted = async () => {
  try {
    await ElMessageBox.confirm(
      '是否重新计算所有基金的复权累计净值？此操作可能需要一些时间。',
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    recalculatingAdjusted.value = true

    const response = await fetch(`${API_BASE}/api/nav/recalculate-adjusted`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const result = await response.json()

    if (result.success) {
      ElMessage.success(result.message || '复权净值计算完成')
      // 刷新基金列表
      await loadFundList()
    } else {
      ElMessage.error(result.message || '复权净值计算失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('计算复权净值失败:', error)
      ElMessage.error('计算复权净值失败，请稍后重试')
    }
  } finally {
    recalculatingAdjusted.value = false
  }
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedFunds.value = selection
}

// 处理行点击
const handleRowClick = (row) => {
  viewFundDetail(row.fund_code)
}

// 查看基金详情
const viewFundDetail = (fundCode) => {
  router.push({
    name: 'FundNavDetail',
    params: { fundCode }
  })
}

// 打开产品特征编辑对话框
const openProductFeaturesDialog = (fund) => {
  currentEditFund.value = fund
  editingProductFeatures.value = fund.product_features || ''
  productFeaturesDialogVisible.value = true
}

// 保存产品特征
const handleSaveProductFeatures = async () => {
  productFeaturesSubmitting.value = true

  try {
    const response = await fetch(`http://localhost:8000/api/funds/${currentEditFund.value.fund_code}/product-features`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        product_features: editingProductFeatures.value || null
      })
    })

    const result = await response.json()

    if (result.success) {
      // 更新本地数据
      const fund = fundList.value.find(f => f.fund_code === currentEditFund.value.fund_code)
      if (fund) {
        fund.product_features = editingProductFeatures.value
      }

      ElMessage.success('产品特征更新成功')
      productFeaturesDialogVisible.value = false
    } else {
      ElMessage.error(`更新失败: ${result.message}`)
    }
  } catch (error) {
    console.error('更新产品特征失败:', error)
    ElMessage.error(`更新产品特征失败: ${error.message}`)
  } finally {
    productFeaturesSubmitting.value = false
  }
}

// 更新产品特征 (保留旧方法以防其他地方使用)
const updateProductFeatures = async (row) => {
  try {
    const response = await fetch(`http://localhost:8000/api/funds/${row.fund_code}/product-features`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        product_features: row.product_features || null
      })
    })

    const result = await response.json()

    if (result.success) {
      ElMessage.success(`成功更新 ${row.fund_code} 的产品特征`)
    } else {
      ElMessage.error(`更新失败: ${result.message}`)
    }
  } catch (error) {
    console.error('更新产品特征失败:', error)
    ElMessage.error(`更新产品特征失败: ${error.message}`)
  }
}

// 日期排序方法
const sortByDate = (a, b) => {
  const dateA = new Date(a.latest_nav_date || '1970-01-01')
  const dateB = new Date(b.latest_nav_date || '1970-01-01')
  return dateA - dateB
}

// 处理删除基金
const handleDeleteFund = async (fund) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除基金 ${fund.fund_code} - ${fund.fund_name} 及其所有净值记录吗？此操作不可恢复！`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )

    // 获取该基金的所有净值记录ID
    const navResponse = await navAPI.getNavByFund(fund.fund_code, 10000)
    const navIds = navResponse.data.nav_records.map(nav => nav.id)

    if (navIds.length > 0) {
      await navAPI.batchDeleteNav(navIds)
      ElMessage.success(`成功删除基金 ${fund.fund_code} 的 ${navIds.length} 条净值记录`)
    } else {
      ElMessage.warning(`基金 ${fund.fund_code} 没有净值记录`)
    }

    refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除基金失败:', error)
      ElMessage.error('删除基金失败')
    }
  }
}

// 批量导出净值
const handleBatchExport = async () => {
  if (!selectedFunds.value.length) {
    ElMessage.warning('请先选择要导出的基金')
    return
  }

  try {
    ElMessage.info('正在获取净值数据...')

    // 收集所有选中基金的净值数据
    const allNavData = []
    let totalRecords = 0

    for (const fund of selectedFunds.value) {
      try {
        const response = await navAPI.getNavByFund(fund.fund_code, 10000)
        const navRecords = response.data.nav_records || []

        // 按日期倒序排序
        navRecords.sort((a, b) => new Date(b.nav_date) - new Date(a.nav_date))

        // 添加基金信息到每条记录
        navRecords.forEach(nav => {
          allNavData.push({
            fundCode: fund.fund_code,
            fundName: nav.fund_name || fund.fund_name,
            navDate: nav.nav_date,
            unitNav: nav.unit_nav,
            accumNav: nav.accum_nav,
            navRecord: nav
          })
        })

        totalRecords += navRecords.length
      } catch (error) {
        console.error(`获取基金 ${fund.fund_code} 净值失败:`, error)
      }
    }

    if (allNavData.length === 0) {
      ElMessage.warning('选中的基金没有净值数据可导出')
      return
    }

    // 按基金代码和日期排序
    allNavData.sort((a, b) => {
      // 先按基金代码排序
      if (a.fundCode !== b.fundCode) {
        return a.fundCode.localeCompare(b.fundCode)
      }
      // 同一基金按日期倒序
      return new Date(b.navDate) - new Date(a.navDate)
    })

    // 创建CSV内容
    const headers = ['基金代码', '产品名称', '净值日期', '单位净值', '累计净值', '涨跌幅', '间隔天数']
    let csvContent = '\ufeff' + headers.join(',') + '\n'

    // 按基金分组计算涨跌幅和间隔天数
    let currentFundCode = null
    let fundNavList = []

    allNavData.forEach((data, index) => {
      // 当切换到新基金或最后一条记录时，处理上一个基金的数据
      if (currentFundCode !== data.fundCode) {
        if (fundNavList.length > 0) {
          // 处理上一个基金的净值数据
          addFundNavToCSV(fundNavList, csvContent)
        }
        currentFundCode = data.fundCode
        fundNavList = [data]
      } else {
        fundNavList.push(data)
      }

      // 最后一条记录
      if (index === allNavData.length - 1 && fundNavList.length > 0) {
        addFundNavToCSV(fundNavList, csvContent)
      }
    })

    // 辅助函数：将基金净值数据添加到CSV
    function addFundNavToCSV(navList, csv) {
      navList.forEach((data, idx) => {
        const fundCode = data.fundCode
        const fundName = data.fundName
        const navDate = formatDate(data.navDate)
        const unitNav = formatNumber(data.unitNav, 4)
        const accumNav = formatNumber(data.accumNav, 4)

        // 计算涨跌幅
        let changePercent = '-'
        if (idx < navList.length - 1) {
          const currentNav = parseFloat(data.unitNav)
          const previousNav = parseFloat(navList[idx + 1].unitNav)
          if (previousNav !== 0) {
            const change = ((currentNav - previousNav) / previousNav) * 100
            const sign = change > 0 ? '+' : ''
            changePercent = `${sign}${change.toFixed(2)}%`
          }
        }

        // 计算间隔天数
        let dayGap = '-'
        if (idx < navList.length - 1) {
          const currentDate = new Date(data.navDate)
          const nextDate = new Date(navList[idx + 1].navDate)
          const daysDiff = Math.abs((currentDate - nextDate) / (1000 * 60 * 60 * 24))
          dayGap = Math.floor(daysDiff).toString()
        }

        const rowData = [fundCode, fundName, navDate, unitNav, accumNav, changePercent, dayGap]
        csvContent += rowData.join(',') + '\n'
      })
    }

    // 修正CSV生成（上面的逻辑有问题，重写）
    csvContent = '\ufeff' + headers.join(',') + '\n'

    let lastFundCode = null
    let fundRecords = []

    for (let i = 0; i < allNavData.length; i++) {
      const data = allNavData[i]

      if (lastFundCode !== data.fundCode && lastFundCode !== null) {
        // 处理完整的基金记录
        processFundRecords(fundRecords)
        fundRecords = []
      }

      fundRecords.push(data)
      lastFundCode = data.fundCode

      // 最后一个基金
      if (i === allNavData.length - 1) {
        processFundRecords(fundRecords)
      }
    }

    function processFundRecords(records) {
      records.forEach((data, idx) => {
        const fundCode = data.fundCode
        const fundName = data.fundName
        const navDate = formatDate(data.navDate)
        const unitNav = formatNumber(data.unitNav, 4)
        const accumNav = formatNumber(data.accumNav, 4)

        // 计算涨跌幅
        let changePercent = '-'
        if (idx < records.length - 1) {
          const currentNav = parseFloat(data.unitNav)
          const previousNav = parseFloat(records[idx + 1].unitNav)
          if (previousNav !== 0) {
            const change = ((currentNav - previousNav) / previousNav) * 100
            const sign = change > 0 ? '+' : ''
            changePercent = `${sign}${change.toFixed(2)}%`
          }
        }

        // 计算间隔天数
        let dayGap = '-'
        if (idx < records.length - 1) {
          const currentDate = new Date(data.navDate)
          const nextDate = new Date(records[idx + 1].navDate)
          const daysDiff = Math.abs((currentDate - nextDate) / (1000 * 60 * 60 * 24))
          dayGap = Math.floor(daysDiff).toString()
        }

        const rowData = [fundCode, fundName, navDate, unitNav, accumNav, changePercent, dayGap]
        csvContent += rowData.join(',') + '\n'
      })
    }

    // 创建下载链接
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)

    // 设置文件名
    const today = new Date().toISOString().split('T')[0]
    const fundCount = selectedFunds.value.length
    const fileName = `净值数据_${fundCount}只基金_共${totalRecords}条_${today}.csv`

    link.setAttribute('href', url)
    link.setAttribute('download', fileName)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success(`成功导出 ${fundCount} 只基金的 ${totalRecords} 条净值记录`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  }
}

// 批量删除基金
const handleBatchDeleteFunds = async () => {
  if (!selectedFunds.value.length) {
    ElMessage.warning('请先选择要删除的基金')
    return
  }

  try {
    const fundCodes = selectedFunds.value.map(f => f.fund_code).join('、')
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFunds.value.length} 个基金及其所有净值记录吗？<br/>
      <span style="color: #E6A23C;">包括: ${fundCodes}</span><br/>
      <span style="color: #F56C6C; font-weight: bold;">此操作不可恢复！</span>`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )

    let totalDeleted = 0
    for (const fund of selectedFunds.value) {
      try {
        const navResponse = await navAPI.getNavByFund(fund.fund_code, 10000)
        const navIds = navResponse.data.nav_records.map(nav => nav.id)

        if (navIds.length > 0) {
          await navAPI.batchDeleteNav(navIds)
          totalDeleted += navIds.length
        }
      } catch (error) {
        console.error(`删除基金 ${fund.fund_code} 失败:`, error)
      }
    }

    ElMessage.success(`成功删除 ${selectedFunds.value.length} 个基金，共 ${totalDeleted} 条净值记录`)
    refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除基金失败:', error)
      ElMessage.error('批量删除基金失败')
    }
  }
}

// ============ 分红管理功能 ============

// 打开分红管理对话框
const handleDividendManage = async (fund) => {
  currentFund.value = fund
  dividendDialogVisible.value = true
  await loadDividendList(fund.fund_code)
}

// 加载分红列表
const loadDividendList = async (fundCode) => {
  dividendLoading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/dividend/fund/${fundCode}/history`)
    dividendList.value = response.data.dividend_history || []
    console.log('分红记录:', dividendList.value)
  } catch (error) {
    console.error('获取分红记录失败:', error)
    ElMessage.error('获取分红记录失败')
    dividendList.value = []
  } finally {
    dividendLoading.value = false
  }
}

// 新增分红
const handleAddDividend = () => {
  dividendFormMode.value = 'add'
  currentDividend.value = null
  dividendForm.value = {
    exDividendDate: '',
    preDividendNav: null,
    dividendPerShare: null
  }
  dividendFormDialogVisible.value = true
}

// 编辑分红
const handleEditDividend = (dividend) => {
  dividendFormMode.value = 'edit'
  currentDividend.value = dividend
  dividendForm.value = {
    exDividendDate: dividend.ex_dividend_date,
    preDividendNav: dividend.pre_dividend_nav,
    dividendPerShare: dividend.dividend_per_share
  }
  dividendFormDialogVisible.value = true
}

// 提交分红表单
const handleSubmitDividend = async () => {
  if (!dividendFormRef.value) return

  try {
    await dividendFormRef.value.validate()
  } catch (error) {
    return
  }

  dividendSubmitting.value = true

  try {
    if (dividendFormMode.value === 'add') {
      // 新增分红
      await axios.post(
        `${API_BASE}/api/dividend/create`,
        null,
        {
          params: {
            fund_code: currentFund.value.fund_code,
            ex_dividend_date: dividendForm.value.exDividendDate,
            pre_dividend_nav: dividendForm.value.preDividendNav,
            dividend_per_share: dividendForm.value.dividendPerShare
          }
        }
      )
      ElMessage.success('分红记录创建成功')
    } else {
      // 编辑分红
      await axios.put(
        `${API_BASE}/api/dividend/${currentDividend.value.id}`,
        null,
        {
          params: {
            ex_dividend_date: dividendForm.value.exDividendDate,
            pre_dividend_nav: dividendForm.value.preDividendNav,
            dividend_per_share: dividendForm.value.dividendPerShare
          }
        }
      )
      ElMessage.success('分红记录更新成功')
    }

    dividendFormDialogVisible.value = false
    await loadDividendList(currentFund.value.fund_code)
  } catch (error) {
    console.error('保存分红记录失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败，请重试')
  } finally {
    dividendSubmitting.value = false
  }
}

// 删除分红
const handleDeleteDividend = async (dividend) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除该分红记录吗？\n基准日：${dividend.ex_dividend_date}\n分红方案：${dividend.dividend_per_share} 元/份`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 调用删除API
    await axios.delete(`${API_BASE}/api/dividend/${dividend.id}`)
    ElMessage.success('分红记录已删除')
    await loadDividendList(currentFund.value.fund_code)

  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除分红记录失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 初始化
onMounted(() => {
  loadFundList()
})
</script>

<style scoped>
.nav-management {
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

.action-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 统一卡片高度 */
.upload-card,
.manual-add-card {
  height: 100%;
  min-height: 320px;
}

.upload-card .el-card__body,
.manual-add-card .el-card__body {
  height: calc(100% - 60px);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.table-section {
  margin-bottom: 24px;
}

/* 分红标记样式 */
.dividend-badge {
  color: #F56C6C;
  font-size: 12px;
  margin-left: 4px;
  font-weight: 500;
}

/* 产品特征单元格样式 */
.product-features-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
  min-height: 36px;
}

.product-features-cell:hover {
  background-color: #ecf5ff;
}

.product-features-cell .features-text {
  flex: 1;
  color: #303133;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-features-cell .features-placeholder {
  flex: 1;
  color: #909399;
  font-style: italic;
  text-align: center;
}

.product-features-cell .edit-icon {
  color: #409EFF;
  font-size: 16px;
  flex-shrink: 0;
}

.product-features-cell:hover .edit-icon {
  transform: scale(1.1);
}

.form-tip {
  margin-top: 8px;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
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

.search-bar {
  margin-bottom: 16px;
}

.date-cell {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
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
  padding: 8px 0;
}

/* 行悬停样式 */
.el-table :deep(.el-table__row) {
  transition: background-color 0.2s;
}

.el-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}

/* 分红管理样式 */
.dividend-management {
  min-height: 300px;
}

.dividend-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-management {
    padding: 16px;
  }

  .page-header h2 {
    font-size: 20px;
  }

  .action-section {
    margin-bottom: 16px;
  }

  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .table-header .el-space {
    flex-wrap: wrap;
  }

  .search-bar {
    margin-bottom: 12px;
  }

  .search-bar .el-input {
    max-width: 100% !important;
  }
}

@media (max-width: 480px) {
  .nav-management {
    padding: 12px;
  }

  .page-header {
    margin-bottom: 16px;
  }

  .action-section .el-col {
    margin-bottom: 16px;
  }
}
</style>
