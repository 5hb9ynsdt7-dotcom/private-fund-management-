<template>
  <div class="client-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>客户持仓管理</h2>
      <p class="page-description">客户持仓数据查看和分析</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-section">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="客户总数"
            :value="statistics.totalClients"
            suffix="户"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><User /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="总持仓市值"
            :value="statistics.totalValue"
            :precision="0"
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
            title="总浮动盈亏"
            :value="statistics.totalPnl"
            :precision="0"
            suffix="万元"
          >
            <template #prefix>
              <el-icon :style="`color: ${statistics.totalPnl >= 0 ? '#67c23a' : '#f56c6c'}`">
                <TrendCharts />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="平均收益率"
            :value="statistics.avgReturn"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon :style="`color: ${statistics.avgReturn >= 0 ? '#67c23a' : '#f56c6c'}`">
                <DataAnalysis />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 上传区域 -->
    <el-row :gutter="24">
      <el-col :span="12">
        <el-card class="upload-section" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>批量上传持仓数据</span>
              <el-tooltip content="支持Excel文件批量导入客户持仓数据">
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
                将Excel文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持.xlsx, .xls格式，可同时上传多个文件
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
      </el-col>
      
      <el-col :span="12">
        <el-card class="upload-section" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>批量上传客户分红数据</span>
              <el-tooltip content="支持Excel文件批量导入客户分红交易记录">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </div>
          </template>
          
          <div class="upload-area">
            <el-upload
              ref="dividendUploadRef"
              class="upload-dragger"
              drag
              action=""
              :auto-upload="false"
              :file-list="dividendFileList"
              accept=".xlsx,.xls"
              multiple
              @change="handleDividendFileChange"
              @remove="handleDividendFileRemove"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将分红Excel文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持.xlsx, .xls格式，包含：集团号、产品代码、交易类型、确认金额、确认份额、确认日期
                </div>
              </template>
            </el-upload>
            
            <div class="upload-controls" v-if="dividendFileList.length">
              <el-checkbox v-model="overrideDividendExisting">覆盖已存在数据</el-checkbox>
              <div class="upload-buttons">
                <el-button @click="clearDividendFiles">清空</el-button>
                <el-button 
                  type="success" 
                  :loading="dividendUploading"
                  @click="uploadDividendFiles"
                >
                  {{ dividendUploading ? '上传中...' : '上传分红数据' }}
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
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
          <el-input
            v-model="searchForm.planner"
            placeholder="理财师筛选"
            clearable
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="searchForm.sortBy"
            placeholder="排序方式"
            style="width: 100%"
          >
            <el-option label="按理财师排序" value="domestic_planner" />
            <el-option label="按市值排序" value="total_market_value" />
            <el-option label="按成本排序" value="total_cost" />
            <el-option label="按基金数排序" value="fund_count" />
          </el-select>
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
          <span>客户列表</span>
          <div class="table-actions">
            <el-button 
              v-if="selectedRows.length > 0" 
              type="danger" 
              size="small"
              @click="batchDeleteClients"
            >
              <el-icon><Delete /></el-icon>
              批量删除 ({{ selectedRows.length }})
            </el-button>
            <el-button @click="refreshData" size="small">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        v-loading="tableLoading"
        :data="tableData"
        style="width: 100%"
        stripe
        border
        @row-click="handleRowClick"
        @selection-change="handleSelectionChange"
      >
        <el-table-column 
          type="selection" 
          width="55" 
          fixed="left"
          :selectable="() => true"
        />
        
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
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ row.client_name || '--' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="domestic_planner"
          label="理财师"
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ row.domestic_planner || '--' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="fund_count"
          label="基金数量"
          min-width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag size="small">{{ row.fund_count }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="total_cost"
          label="总成本"
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <span class="money-text">
              {{ formatMoney(row.total_cost) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="total_market_value"
          label="总市值"
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <span class="money-text">
              {{ formatMoney(row.total_market_value) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="total_unrealized_pnl"
          label="浮动盈亏"
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getPnlClass(row.total_unrealized_pnl)">
              {{ formatMoney(row.total_unrealized_pnl) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="unrealized_pnl_ratio"
          label="盈亏比例"
          min-width="100"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getPnlClass(row.unrealized_pnl_ratio)">
              {{ formatPercent(row.unrealized_pnl_ratio) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="latest_update"
          label="最新更新"
          min-width="120"
          align="center"
        >
          <template #default="{ row }">
            <span>{{ formatDate(row.latest_update) }}</span>
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
import { positionAPI } from '@/api/position'

const router = useRouter()

// 响应式数据
const tableLoading = ref(false)
const uploading = ref(false)
const tableData = ref([])
const fileList = ref([])
const overrideExisting = ref(false)
const uploadRef = ref()

// 批量选择相关
const selectedRows = ref([])
const selectAll = ref(false)
const isIndeterminate = ref(false)

// 分红数据上传相关
const dividendFileList = ref([])
const overrideDividendExisting = ref(false)
const dividendUploading = ref(false)
const dividendUploadRef = ref()

// 统计数据
const statistics = reactive({
  totalClients: 0,
  totalValue: 0,
  totalPnl: 0,
  avgReturn: 0
})

// 搜索表单
const searchForm = reactive({
  search: '',
  planner: '',
  sortBy: 'domestic_planner'
})

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 加载客户列表数据
const loadClientData = async () => {
  tableLoading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchForm.search,
      planner: searchForm.planner,
      sort_by: searchForm.sortBy,
      sort_order: 'desc'
    }
    
    const response = await positionAPI.getClientList(params)
    
    if (response.data) {
      tableData.value = response.data || []
      pagination.total = response.total || 0
      
      // 计算统计数据
      updateStatistics()
    }
  } catch (error) {
    console.error('加载客户数据失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(`加载客户数据失败: ${errorMsg}`)
    tableData.value = []
    pagination.total = 0
  } finally {
    tableLoading.value = false
  }
}

// 更新统计数据
const updateStatistics = () => {
  if (tableData.value.length === 0) {
    Object.assign(statistics, {
      totalClients: 0,
      totalValue: 0,
      totalPnl: 0,
      avgReturn: 0
    })
    return
  }
  
  const totalValue = tableData.value.reduce((sum, item) => sum + (parseFloat(item.total_market_value) || 0), 0)
  const totalPnl = tableData.value.reduce((sum, item) => sum + (parseFloat(item.total_unrealized_pnl) || 0), 0)
  const totalCost = tableData.value.reduce((sum, item) => sum + (parseFloat(item.total_cost) || 0), 0)
  
  Object.assign(statistics, {
    totalClients: pagination.total,
    totalValue: totalValue / 10000, // 转换为万元
    totalPnl: totalPnl / 10000, // 转换为万元
    avgReturn: totalCost > 0 ? (totalPnl / totalCost * 100) : 0
  })
}

// 文件上传处理
const handleFileChange = (file, fileListParam) => {
  console.log('文件变化:', file, fileListParam)
  // 更新文件列表
  fileList.value = fileListParam
}

const handleFileRemove = (file, fileListParam) => {
  console.log('移除文件:', file, fileListParam)
  // 更新文件列表
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
    
    const response = await positionAPI.uploadPositions(formData, overrideExisting.value)
    
    if (response.success) {
      ElMessage.success('持仓数据上传成功')
      clearFiles()
      refreshData()
    } else {
      ElMessage.error('上传失败: ' + (response.message || '未知错误'))
    }
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败: ' + (error.message || '网络错误'))
  } finally {
    uploading.value = false
  }
}

// 分红文件上传处理
const handleDividendFileChange = (file, fileListParam) => {
  console.log('分红文件变化:', file, fileListParam)
  dividendFileList.value = fileListParam
}

const handleDividendFileRemove = (file, fileListParam) => {
  console.log('移除分红文件:', file, fileListParam)
  dividendFileList.value = fileListParam
}

const clearDividendFiles = () => {
  dividendFileList.value = []
  dividendUploadRef.value?.clearFiles()
}

const uploadDividendFiles = async () => {
  if (dividendFileList.value.length === 0) {
    ElMessage.warning('请先选择要上传的分红文件')
    return
  }
  
  dividendUploading.value = true
  try {
    const formData = new FormData()
    dividendFileList.value.forEach(file => {
      formData.append('files', file.raw)
    })
    
    const response = await positionAPI.uploadClientDividends(formData, overrideDividendExisting.value)
    
    if (response.success_count > 0) {
      ElMessage.success(`分红数据上传成功：成功${response.success_count}条，失败${response.failed_count}条`)
      clearDividendFiles()
      refreshData()
    } else {
      ElMessage.error('分红数据上传失败: ' + (response.errors?.join('; ') || '未知错误'))
    }
  } catch (error) {
    console.error('分红数据上传失败:', error)
    ElMessage.error('分红数据上传失败: ' + (error.message || '网络错误'))
  } finally {
    dividendUploading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadClientData()
}

const resetSearch = () => {
  Object.assign(searchForm, {
    search: '',
    planner: '',
    sortBy: 'domestic_planner'
  })
  pagination.page = 1
  loadClientData()
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
  router.push(`/position/detail/${row.group_id}`)
}

const refreshData = () => {
  loadClientData()
}

// 选择处理
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 批量删除客户
const batchDeleteClients = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要删除的客户')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个客户及其所有持仓数据吗？<br/>
      <strong>此操作不可恢复，请谨慎操作！</strong>`,
      '批量删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )
    
    const groupIds = selectedRows.value.map(row => row.group_id)
    const response = await positionAPI.batchDeleteClients(groupIds)
    
    if (response.success) {
      ElMessage.success(`批量删除成功：成功删除 ${response.deleted_count} 个客户`)
      selectedRows.value = []
      refreshData()
    } else {
      ElMessage.error(response.message || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除客户失败:', error)
      ElMessage.error('批量删除客户失败: ' + (error.message || '网络错误'))
    }
  }
}

// 删除单个客户
const deleteClient = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除客户 ${row.group_id} (${row.client_name || '未知'}) 及其所有持仓数据吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )
    
    const response = await positionAPI.deleteClient(row.group_id)
    
    if (response.success) {
      ElMessage.success(response.message || '删除成功')
      refreshData()
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除客户失败:', error)
      ElMessage.error('删除客户失败: ' + (error.message || '网络错误'))
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

const formatPercent = (ratio) => {
  if (ratio == null || ratio === '') return '--'
  const num = parseFloat(ratio)
  return num.toFixed(2) + '%'
}

const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleDateString('zh-CN')
}

const getPnlClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  return num >= 0 ? 'profit-text' : 'loss-text'
}

// 生命周期
onMounted(() => {
  loadClientData()
})
</script>

<style scoped>
.client-list {
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

.table-actions {
  display: flex;
  gap: 8px;
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
  .client-list {
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
  .client-list {
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