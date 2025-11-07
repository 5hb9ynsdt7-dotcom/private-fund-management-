<template>
  <div class="trade-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>交易分析</h2>
      <p class="page-description">基金交易数据上传、分析和统计</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-section">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="交易记录总数"
            :value="statistics.totalTransactions"
            suffix="笔"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><DataLine /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="涉及客户数"
            :value="statistics.totalClients"
            suffix="户"
          >
            <template #prefix>
              <el-icon style="color: #67c23a"><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="交易总金额"
            :value="statistics.totalAmount"
            :precision="0"
            suffix="万元"
          >
            <template #prefix>
              <el-icon style="color: #e6a23c"><Money /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="手续费总计"
            :value="statistics.totalFee"
            :precision="0"
            suffix="元"
          >
            <template #prefix>
              <el-icon style="color: #f56c6c"><CreditCard /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 上传区域 -->
    <el-card class="upload-section" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>批量上传交易数据</span>
          <el-tooltip content="支持Excel文件批量导入基金交易记录">
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          action=""
          :auto-upload="false"
          :file-list="fileList"
          accept=".xlsx,.xls"
          multiple
          @change="handleFileChange"
          @remove="handleFileRemove"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将交易Excel文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持.xlsx, .xls格式，包含：集团号、客户遮蔽姓名、基金名称、交易类型名称、交易确认日期、确认份额、确认金额、手续费、产品代码、产品名称
            </div>
          </template>
        </el-upload>
        
        <div class="upload-controls" v-if="fileList.length">
          <el-checkbox v-model="overrideExisting">覆盖已存在数据</el-checkbox>
          <div class="upload-buttons">
            <el-button @click="clearFiles">清空</el-button>
            <el-button 
              type="primary" 
              :loading="uploading"
              @click="uploadFiles"
            >
              {{ uploading ? '上传中...' : '开始上传' }}
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 搜索和筛选 -->
    <el-card class="filter-section">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索客户集团号或姓名"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch">
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="searchForm.transactionType"
            placeholder="交易类型筛选"
            clearable
          />
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 客户列表表格 -->
    <el-card class="table-section">
      <template #header>
        <div class="table-header">
          <span>交易客户列表</span>
          <el-button @click="refreshData" size="small">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table
        v-loading="tableLoading"
        :data="tableData"
        style="width: 100%"
        stripe
        border
        @row-click="handleRowClick"
      >
        <el-table-column
          prop="group_id"
          label="集团号"
          width="120"
          fixed="left"
          align="center"
        />
        
        <el-table-column
          prop="client_name"
          label="客户姓名(遮蔽)"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ row.client_name || '--' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="transaction_count"
          label="交易笔数"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <el-tag size="small">{{ row.transaction_count }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="fund_count"
          label="涉及基金数"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <el-tag size="small" type="success">{{ row.fund_count }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="total_amount"
          label="交易总金额"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <span class="money-text">
              {{ formatMoney(row.total_amount) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="total_fee"
          label="手续费总计"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <span class="money-text">
              {{ formatMoney(row.total_fee) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="net_amount"
          label="净交易金额"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getAmountClass(row.net_amount)">
              {{ formatMoney(row.net_amount) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="first_transaction_date"
          label="首次交易"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ formatDate(row.first_transaction_date) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="last_transaction_date"
          label="最新交易"
          min-width="1"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ formatDate(row.last_transaction_date) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          label="操作"
          width="160"
          fixed="right"
          align="center"
        >
          <template #default="{ row }">
            <el-space>
              <el-button 
                type="primary" 
                size="small"
                @click.stop="viewDetail(row)"
              >
                查看详情
              </el-button>
              <el-button 
                type="danger" 
                size="small"
                @click.stop="deleteClient(row)"
              >
                删除
              </el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { transactionAPI } from '@/api/transaction'

const router = useRouter()

// 响应式数据
const tableLoading = ref(false)
const uploading = ref(false)
const tableData = ref([])
const fileList = ref([])
const overrideExisting = ref(false)
const uploadRef = ref()

// 统计数据
const statistics = reactive({
  totalTransactions: 0,
  totalClients: 0,
  totalAmount: 0,
  totalFee: 0
})

// 搜索表单
const searchForm = reactive({
  search: '',
  dateRange: null,
  transactionType: ''
})

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 加载交易客户数据
const loadClientData = async () => {
  tableLoading.value = true
  try {
    const params = {
      search: searchForm.search,
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    // 添加日期范围参数
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0]
      params.end_date = searchForm.dateRange[1]
    }
    
    const response = await transactionAPI.getTransactionClients(params)
    
    if (Array.isArray(response)) {
      tableData.value = response
      pagination.total = response.length
    } else {
      tableData.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('加载交易客户数据失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(`加载交易客户数据失败: ${errorMsg}`)
    tableData.value = []
    pagination.total = 0
  } finally {
    tableLoading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    const params = {}
    
    // 添加日期范围参数
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0]
      params.end_date = searchForm.dateRange[1]
    }
    
    const response = await transactionAPI.getTransactionStats(params)
    
    Object.assign(statistics, {
      totalTransactions: response.total_transactions || 0,
      totalClients: response.total_clients || 0,
      totalAmount: (response.total_amount || 0) / 10000, // 转换为万元
      totalFee: response.total_fee || 0
    })
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 文件上传处理
const handleFileChange = (file, fileListParam) => {
  console.log('文件变化:', file, fileListParam)
  fileList.value = fileListParam
}

const handleFileRemove = (file, fileListParam) => {
  console.log('移除文件:', file, fileListParam)
  fileList.value = fileListParam
}

const clearFiles = () => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

const uploadFiles = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    fileList.value.forEach(file => {
      formData.append('files', file.raw)
    })
    
    const response = await transactionAPI.uploadTransactions(formData, overrideExisting.value)
    
    if (response.success_count > 0) {
      ElMessage.success(`交易数据上传成功：成功${response.success_count}条，失败${response.failed_count}条`)
      clearFiles()
      refreshData()
    } else {
      const errorMsg = response.errors?.join('; ') || response.message || '上传失败'
      ElMessage.error(`交易数据上传失败: ${errorMsg}`)
    }
  } catch (error) {
    console.error('上传失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(`上传失败: ${errorMsg}`)
  } finally {
    uploading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadClientData()
  loadStatistics()
}

const resetSearch = () => {
  Object.assign(searchForm, {
    search: '',
    dateRange: null,
    transactionType: ''
  })
  pagination.page = 1
  loadClientData()
  loadStatistics()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  loadClientData()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadClientData()
}

// 表格操作
const handleRowClick = (row) => {
  console.log('点击行:', row)
}

const viewDetail = (row) => {
  router.push(`/trade/${row.group_id}`)
}

const refreshData = () => {
  loadClientData()
  loadStatistics()
}

// 删除客户交易记录
const deleteClient = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户 ${row.group_id} (${row.client_name || '未知'}) 的所有交易记录吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )
    
    const response = await transactionAPI.deleteClientTransactions(row.group_id)
    
    if (response.success) {
      ElMessage.success(response.message || '删除成功')
      refreshData()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除交易记录失败:', error)
      const errorMsg = error.response?.data?.detail || error.message || '网络错误'
      ElMessage.error(`删除交易记录失败: ${errorMsg}`)
    }
  }
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

const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleDateString('zh-CN')
}

const getAmountClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  return num >= 0 ? 'profit-text' : 'loss-text'
}

// 生命周期
onMounted(() => {
  loadClientData()
  loadStatistics()
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

.upload-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-area {
  padding: 16px;
}

.upload-controls {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-buttons {
  display: flex;
  gap: 8px;
}

.filter-section {
  margin-bottom: 24px;
}

.table-section {
  margin-bottom: 24px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

/* 金额样式 */
.money-text {
  font-weight: 500;
}

.profit-text {
  color: #f56c6c;
  font-weight: 500;
}

.loss-text {
  color: #67c23a;
  font-weight: 500;
}

/* 表格行悬停效果 */
.el-table tbody tr:hover {
  cursor: pointer;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-section .el-col {
    margin-bottom: 16px;
  }
  
  .filter-section .el-col {
    margin-bottom: 12px;
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
  
  .upload-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .upload-buttons {
    justify-content: center;
  }
  
  .filter-section .el-row {
    flex-direction: column;
  }
  
  .filter-section .el-col {
    margin-bottom: 12px;
    width: 100%;
  }
  
  .table-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .trade-analysis {
    padding: 12px;
  }
  
  .stats-section {
    margin-bottom: 16px;
  }
  
  .upload-section,
  .filter-section,
  .table-section {
    margin-bottom: 16px;
  }
}
</style>