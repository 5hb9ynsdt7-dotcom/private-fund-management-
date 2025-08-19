<template>
  <div class="strategy-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>策略管理</h2>
      <p class="page-description">管理基金投资策略分类和配置</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-section">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="策略总数"
            :value="statistics.totalStrategies"
            suffix="个"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="成长策略"
            :value="statistics.growthStrategies"
            suffix="个"
          >
            <template #prefix>
              <el-icon style="color: #67c23a"><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="固收策略"
            :value="statistics.fixedIncomeStrategies"
            suffix="个"
          >
            <template #prefix>
              <el-icon style="color: #e6a23c"><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="QD策略"
            :value="statistics.qdStrategies"
            suffix="个"
          >
            <template #prefix>
              <el-icon style="color: #f56c6c"><TrendCharts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 批量上传区域 -->
    <el-card class="upload-section" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>批量上传策略配置</span>
          <el-tooltip content="支持Excel文件批量导入策略配置">
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      
      <ExcelUploader
        ref="strategyUploaderRef"
        :upload-api="uploadStrategyFiles"
        template-url="/templates/strategy_template.xlsx"
        accept=".xlsx,.xls"
        @success="handleUploadSuccess"
        @error="handleUploadError"
        @progress="handleUploadProgress"
      />
    </el-card>
    
    <!-- 操作工具栏 -->
    <el-card class="toolbar-section" shadow="hover">
      <el-row justify="space-between">
        <el-col :span="18">
          <el-space wrap>
            <el-button
              type="primary"
              @click="handleCreate"
            >
              <el-icon><Plus /></el-icon>
              新增策略
            </el-button>
            
            <el-button
              type="success"
              :disabled="!selectedRows.length"
              @click="handleBatchEdit"
            >
              <el-icon><Edit /></el-icon>
              批量编辑 ({{ selectedRows.length }})
            </el-button>
            
            <el-button
              type="danger"
              :disabled="!selectedRows.length"
              @click="handleBatchDelete"
            >
              <el-icon><Delete /></el-icon>
              批量删除
            </el-button>
            
            <el-button
              type="info"
              @click="handleExport"
            >
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
            
            <el-button @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </el-space>
        </el-col>
        <el-col :span="6">
          <el-input
            v-model="searchText"
            placeholder="搜索基金代码或名称"
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
      </el-row>
    </el-card>
    
    <!-- 筛选工具栏 -->
    <StrategyFilterBar
      v-model:filters="filters"
      @search="handleFilterSearch"
      @reset="handleFilterReset"
    />
    
    <!-- 策略数据表格 -->
    <el-card class="table-section" shadow="hover">
      <StrategyDataTable
        v-model:selection="selectedRows"
        :loading="tableLoading"
        :data="tableData"
        :pagination="pagination"
        @refresh="refreshData"
        @sort-change="handleSortChange"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        @edit="handleEdit"
        @delete="handleDelete"
        @row-dblclick="handleRowDoubleClick"
      />
    </el-card>
    
    <!-- 策略编辑对话框 -->
    <StrategyEditDialog
      v-model="editDialogVisible"
      :strategy-data="currentStrategy"
      :mode="editMode"
      @success="handleEditSuccess"
    />
    
    <!-- 批量编辑对话框 -->
    <StrategyBatchEditDialog
      v-model="batchEditDialogVisible"
      :selected-strategies="selectedRows"
      @success="handleBatchEditSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ExcelUploader from '@/components/ExcelUploader.vue'
import StrategyFilterBar from '@/components/StrategyFilterBar.vue'
import StrategyDataTable from '@/components/StrategyDataTable.vue'
import StrategyEditDialog from '@/components/StrategyEditDialog.vue'
import StrategyBatchEditDialog from '@/components/StrategyBatchEditDialog.vue'
import { strategyAPI } from '@/api/strategy'
import { downloadFile } from '@/utils'

// 页面状态
const tableLoading = ref(false)
const selectedRows = ref([])
const tableData = ref([])
const searchText = ref('')
const strategyUploaderRef = ref()

// 统计数据
const statistics = reactive({
  totalStrategies: 0,
  growthStrategies: 0,
  fixedIncomeStrategies: 0,
  qdStrategies: 0
})

// 筛选条件
const filters = reactive({
  majorStrategy: '',
  subStrategy: '',
  isQd: null,
  status: ''
})

// 分页配置
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 排序配置
const sortConfig = reactive({
  prop: 'created_at',
  order: 'descending'
})

// 编辑对话框
const editDialogVisible = ref(false)
const currentStrategy = ref(null)
const editMode = ref('create') // create | edit

// 批量编辑对话框
const batchEditDialogVisible = ref(false)

// 加载策略统计数据
const loadStatistics = async () => {
  try {
    const response = await strategyAPI.getStrategyStatistics()
    if (response.success) {
      Object.assign(statistics, response.data)
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载策略数据
const loadStrategyData = async () => {
  tableLoading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      search: searchText.value,
      ...filters,
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order === 'ascending' ? 'asc' : 'desc'
    }
    
    const response = await strategyAPI.getStrategyList(params)
    if (response.data) {
      tableData.value = response.data || []
      pagination.total = response.total || 0
    }
  } catch (error) {
    console.error('加载策略数据失败:', error)
    ElMessage.error('加载数据失败')
    tableData.value = []
    pagination.total = 0
  } finally {
    tableLoading.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  selectedRows.value = []
  await Promise.all([
    loadStrategyData(),
    loadStatistics()
  ])
}

// 处理搜索
const handleSearch = () => {
  pagination.currentPage = 1
  loadStrategyData()
}

// 处理筛选搜索
const handleFilterSearch = () => {
  pagination.currentPage = 1
  loadStrategyData()
}

// 重置筛选条件
const handleFilterReset = () => {
  Object.assign(filters, {
    majorStrategy: '',
    subStrategy: '',
    isQd: null,
    status: ''
  })
  pagination.currentPage = 1
  loadStrategyData()
}

// 处理排序变化
const handleSortChange = ({ prop, order }) => {
  sortConfig.prop = prop
  sortConfig.order = order
  loadStrategyData()
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  loadStrategyData()
}

// 处理当前页变化
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  loadStrategyData()
}

// 处理新增策略
const handleCreate = () => {
  currentStrategy.value = null
  editMode.value = 'create'
  editDialogVisible.value = true
}

// 处理编辑策略
const handleEdit = (row) => {
  currentStrategy.value = { ...row }
  editMode.value = 'edit'
  editDialogVisible.value = true
}

// 处理行双击
const handleRowDoubleClick = (row) => {
  handleEdit(row)
}

// 处理删除策略
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除基金 ${row.fund_code} 的策略配置吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await strategyAPI.deleteStrategy(row.fund_code)
    ElMessage.success('删除成功')
    refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 处理批量编辑
const handleBatchEdit = () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要编辑的策略')
    return
  }
  
  batchEditDialogVisible.value = true
}

// 处理批量删除
const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的策略')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个策略配置吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const fundCodes = selectedRows.value.map(row => row.fund_code)
    await strategyAPI.batchDeleteStrategy(fundCodes)
    ElMessage.success(`成功删除 ${fundCodes.length} 个策略配置`)
    refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 处理编辑成功
const handleEditSuccess = (data) => {
  const action = data.action || 'updated'
  const actionText = action === 'created' ? '创建' : '更新'
  ElMessage.success(`策略${actionText}成功`)
  refreshData()
}

// 处理批量编辑成功
const handleBatchEditSuccess = (result) => {
  ElMessage.success(`批量更新了 ${result.updated_count} 个策略配置`)
  refreshData()
}

// 上传策略文件
const uploadStrategyFiles = async (files) => {
  try {
    const formData = new FormData()
    files.forEach((file, index) => {
      formData.append(`files`, file)
    })
    
    const response = await strategyAPI.uploadStrategyFiles(formData)
    return response
  } catch (error) {
    throw new Error(error.message || '上传失败')
  }
}

// 处理上传成功
const handleUploadSuccess = (result) => {
  console.log('策略上传成功:', result)
  ElMessage.success('策略配置上传成功')
  refreshData()
}

// 处理上传错误
const handleUploadError = (error) => {
  console.error('策略上传失败:', error)
  ElMessage.error('策略配置上传失败')
}

// 处理上传进度
const handleUploadProgress = ({ uploading }) => {
  // 可以在这里显示进度条
}

// 导出数据
const handleExport = async () => {
  try {
    const params = {
      search: searchText.value,
      ...filters,
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order === 'ascending' ? 'asc' : 'desc'
    }
    
    const response = await strategyAPI.exportStrategyData(params)
    
    // 下载文件
    const filename = `策略配置_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.xlsx`
    downloadFile(response.data, filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 初始化
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.strategy-management {
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

.toolbar-section {
  margin-bottom: 16px;
}

.table-section {
  margin-bottom: 24px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-section .el-col {
    margin-bottom: 16px;
  }
}

@media (max-width: 768px) {
  .strategy-management {
    padding: 16px;
  }
  
  .page-header h2 {
    font-size: 20px;
  }
  
  .stats-section .el-col {
    margin-bottom: 12px;
  }
  
  .toolbar-section .el-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .toolbar-section .el-col {
    flex: 1;
  }
}

@media (max-width: 480px) {
  .strategy-management {
    padding: 12px;
  }
  
  .page-header {
    margin-bottom: 16px;
  }
  
  .stats-section {
    margin-bottom: 16px;
  }
  
  .stats-section .el-col {
    margin-bottom: 8px;
  }
}
</style>