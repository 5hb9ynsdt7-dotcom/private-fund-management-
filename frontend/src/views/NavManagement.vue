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
    
    <!-- 数据表格 -->
    <el-card class="table-section" shadow="hover">
      <template #header>
        <div class="table-header">
          <span>净值数据</span>
          <el-space>
            <el-button 
              type="danger" 
              :disabled="!selectedRows.length"
              @click="handleBatchDelete"
            >
              <el-icon><Delete /></el-icon>
              批量删除 ({{ selectedRows.length }})
            </el-button>
            <el-button @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button @click="exportData">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </el-space>
        </div>
      </template>
      
      <!-- 筛选工具栏 -->
      <NavFilterBar 
        @filter="handleFilter"
        @reset="handleResetFilter"
        @show-all="handleShowAllRecords"
      />
      
      <!-- 数据表格 -->
      <NavDataTable 
        v-model:selection="selectedRows"
        :loading="tableLoading"
        :data="tableData"
        :pagination="pagination"
        @refresh="refreshData"
        @sort-change="handleSortChange"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        @edit="handleEditNav"
        @delete="handleDeleteNav"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ExcelUploader from '@/components/ExcelUploader.vue'
import NavManualForm from '@/components/NavManualForm.vue'
import NavFilterBar from '@/components/NavFilterBar.vue'
import NavDataTable from '@/components/NavDataTable.vue'
import { navAPI } from '@/api/nav'
import { formatDate, downloadFile } from '@/utils'

// 页面状态
const uploaderRef = ref()
const tableLoading = ref(false)
const selectedRows = ref([])
const tableData = ref([])

// 页面状态（恢复正常分页模式）

// 分页配置
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 排序配置
const sortConfig = reactive({
  prop: 'nav_date',
  order: 'descending'
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

// 加载净值数据（只加载第一页，优化性能）
const loadNavData = async () => {
  tableLoading.value = true
  try {
    const params = {
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order === 'ascending' ? 'asc' : 'desc'
    }
    
    console.log('加载净值数据，参数:', params)
    const response = await navAPI.getNavList(params)
    tableData.value = response.nav_records || []
    pagination.total = response.total || 0
    
    console.log(`加载完成: 当前页 ${tableData.value.length} 条记录，总计 ${pagination.total} 条`)
  } catch (error) {
    console.error('加载净值数据失败:', error)
    ElMessage.error('加载数据失败')
    tableData.value = []
    pagination.total = 0
  } finally {
    tableLoading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  selectedRows.value = []
  loadNavData()
}

// 处理前端筛选
const handleFilter = (searchTerm) => {
  console.log('NavManagement - 前端筛选:', searchTerm)
  // 筛选逻辑已在 NavFilterBar 组件中处理，这里可以记录日志
}

// 显示特定基金的所有记录
const handleShowAllRecords = async (searchTerm) => {
  console.log('NavManagement - 显示所有记录:', searchTerm)
  
  tableLoading.value = true
  try {
    // 判断搜索词是基金代码还是基金名称
    const isCodePattern = /^L\d{5}/.test(searchTerm)
    
    const params = {
      page: 1,
      page_size: 1000, // 使用较大的页面大小
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order === 'ascending' ? 'asc' : 'desc'
    }
    
    if (isCodePattern) {
      params.fund_code = searchTerm
    } else {
      params.fund_name = searchTerm
    }
    
    console.log('加载筛选的所有净值数据，参数:', params)
    const response = await navAPI.getNavList(params)
    
    // 更新表格数据，关闭分页
    tableData.value = response.nav_records || []
    pagination.total = response.total || 0
    pagination.currentPage = 1
    pagination.pageSize = Math.max(50, tableData.value.length) // 设置足够大的页面大小以显示所有记录
    
    const filterType = isCodePattern ? '基金代码' : '基金名称'
    ElMessage.success(`加载完成：共找到 ${tableData.value.length} 条包含"${searchTerm}"的净值记录（按${filterType}筛选）`)
    console.log(`加载完成: ${searchTerm} 共 ${tableData.value.length} 条记录`)
    
  } catch (error) {
    console.error('加载筛选数据失败:', error)
    ElMessage.error(`加载包含"${searchTerm}"的数据失败`)
  } finally {
    tableLoading.value = false
  }
}

// 重置筛选
const handleResetFilter = () => {
  console.log('NavManagement - 重置筛选')
  // 重置为正常分页模式
  pagination.currentPage = 1
  pagination.pageSize = 20
  loadNavData()
}

// 处理排序变化（纯前端排序）
const handleSortChange = ({ prop, order }) => {
  sortConfig.prop = prop
  sortConfig.order = order
  // Element Plus 表格会自动处理前端排序，无需重新加载数据
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  loadNavData()
}

// 处理当前页变化
const handleCurrentChange = (page) => {
  pagination.currentPage = page
  loadNavData()
}

// 处理编辑净值
const handleEditNav = (row) => {
  // TODO: 实现编辑对话框
  console.log('编辑净值:', row)
  ElMessage.info('编辑功能开发中')
}

// 处理删除净值
const handleDeleteNav = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除基金 ${row.fund_code} 在 ${formatDate(row.nav_date)} 的净值记录吗？`,
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

// 批量删除
const handleBatchDelete = async () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要删除的记录')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 条净值记录吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedRows.value.map(row => row.id)
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
const exportData = async () => {
  try {
    const params = {
      ...filters,
      sort_by: sortConfig.prop,
      sort_order: sortConfig.order === 'ascending' ? 'asc' : 'desc'
    }
    
    // 处理日期范围
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = formatDate(filters.dateRange[0])
      params.end_date = formatDate(filters.dateRange[1])
    }
    
    const response = await navAPI.exportNavData(params)
    
    // 下载文件
    const filename = `净值数据_${formatDate(new Date(), 'YYYYMMDD')}.xlsx`
    downloadFile(response.data, filename, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 初始化
onMounted(() => {
  loadNavData()
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

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header span {
  font-weight: 600;
  color: #303133;
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