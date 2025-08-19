<template>
  <div class="nav-data-table">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="data"
      style="width: 100%"
      stripe
      border
      highlight-current-row
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
    >
      <!-- 选择列 -->
      <el-table-column
        type="selection"
        width="55"
        align="center"
        fixed="left"
      />
      
      <!-- 序号列 -->
      <el-table-column
        type="index"
        label="#"
        width="60"
        align="center"
        fixed="left"
        :index="getRowIndex"
      />
      
      <!-- 基金代码 -->
      <el-table-column
        prop="fund_code"
        label="基金代码"
        width="120"
        sortable="custom"
        fixed="left"
      >
        <template #default="{ row }">
          <el-link
            type="primary"
            @click="handleViewFund(row)"
          >
            {{ row.fund_code }}
          </el-link>
        </template>
      </el-table-column>
      
      <!-- 基金名称 -->
      <el-table-column
        prop="fund_name"
        label="基金名称"
        min-width="180"
        sortable="custom"
        show-overflow-tooltip
      />
      
      <!-- 净值日期 -->
      <el-table-column
        prop="nav_date"
        label="净值日期"
        width="120"
        sortable="custom"
        align="center"
      >
        <template #default="{ row }">
          {{ formatDate(row.nav_date) }}
        </template>
      </el-table-column>
      
      <!-- 单位净值 -->
      <el-table-column
        prop="unit_nav"
        label="单位净值"
        width="120"
        sortable="custom"
        align="right"
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
        width="120"
        sortable="custom"
        align="right"
      >
        <template #default="{ row }">
          <span class="nav-value">
            {{ formatNumber(row.accum_nav, 4) }}
          </span>
        </template>
      </el-table-column>
      
      <!-- 日涨跌幅 -->
      <el-table-column
        prop="daily_return"
        label="日涨跌幅"
        width="120"
        sortable="custom"
        align="right"
      >
        <template #default="{ row }">
          <span
            v-if="row.daily_return !== null && row.daily_return !== undefined"
            :class="getReturnClass(row.daily_return)"
          >
            {{ formatPercent(row.daily_return, 2, true) }}
          </span>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>
      
      <!-- 数据状态 -->
      <el-table-column
        prop="status"
        label="状态"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="getStatusType(row.status)"
            size="small"
          >
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <!-- 创建时间 -->
      <el-table-column
        prop="created_at"
        label="创建时间"
        width="160"
        sortable="custom"
        align="center"
      >
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      
      <!-- 操作列 -->
      <el-table-column
        label="操作"
        width="120"
        align="center"
        fixed="right"
      >
        <template #default="{ row }">
          <el-space>
            <el-tooltip content="编辑">
              <el-button
                type="primary"
                size="small"
                circle
                @click="handleEdit(row)"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
            </el-tooltip>
            
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
          </el-space>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        :small="isMobile"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <!-- 批量操作工具条 -->
    <el-affix
      v-if="selectedRows.length"
      position="bottom"
      :offset="20"
    >
      <div class="batch-actions">
        <el-card shadow="always">
          <el-space>
            <span class="batch-info">
              已选择 {{ selectedRows.length }} 条记录
            </span>
            
            <el-button
              type="danger"
              size="small"
              @click="handleBatchDelete"
            >
              <el-icon><Delete /></el-icon>
              批量删除
            </el-button>
            
            <el-button
              type="info"
              size="small"
              @click="handleBatchExport"
            >
              <el-icon><Download /></el-icon>
              导出选中
            </el-button>
            
            <el-button
              size="small"
              @click="clearSelection"
            >
              <el-icon><Close /></el-icon>
              取消选择
            </el-button>
          </el-space>
        </el-card>
      </div>
    </el-affix>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { formatDate, formatNumber, formatPercent } from '@/utils'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    default: () => ({
      currentPage: 1,
      pageSize: 20,
      total: 0
    })
  }
})

const emit = defineEmits([
  'update:selection',
  'refresh',
  'sort-change',
  'size-change',
  'current-change',
  'edit',
  'delete'
])

const tableRef = ref()
const selectedRows = ref([])
const currentPage = ref(props.pagination.currentPage)
const pageSize = ref(props.pagination.pageSize)

// 是否移动端
const isMobile = computed(() => {
  return window.innerWidth < 768
})

// 格式化日期时间
const formatDateTime = (datetime) => {
  if (!datetime) return '--'
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取行号
const getRowIndex = (index) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

// 获取收益率样式
const getReturnClass = (value) => {
  if (value > 0) return 'text-success'
  if (value < 0) return 'text-danger'
  return 'text-muted'
}

// 获取状态类型
const getStatusType = (status) => {
  const statusMap = {
    normal: 'success',
    abnormal: 'danger',
    pending: 'warning'
  }
  return statusMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const statusMap = {
    normal: '正常',
    abnormal: '异常',
    pending: '待审核'
  }
  return statusMap[status] || '未知'
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
  emit('update:selection', selection)
}

// 处理排序变化
const handleSortChange = (sortInfo) => {
  emit('sort-change', sortInfo)
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  pageSize.value = size
  emit('size-change', size)
}

// 处理当前页变化
const handleCurrentChange = (page) => {
  currentPage.value = page
  emit('current-change', page)
}

// 查看基金详情
const handleViewFund = (row) => {
  // TODO: 跳转到基金详情页
  console.log('查看基金详情:', row.fund_code)
}

// 处理编辑
const handleEdit = (row) => {
  emit('edit', row)
}

// 处理删除
const handleDelete = (row) => {
  emit('delete', row)
}

// 批量删除
const handleBatchDelete = () => {
  emit('batch-delete', selectedRows.value)
}

// 批量导出
const handleBatchExport = () => {
  emit('batch-export', selectedRows.value)
}

// 清空选择
const clearSelection = () => {
  if (tableRef.value) {
    tableRef.value.clearSelection()
  }
}

// 刷新表格
const refresh = () => {
  emit('refresh')
}

// 暴露方法
defineExpose({
  clearSelection,
  refresh
})
</script>

<style scoped>
.nav-data-table {
  width: 100%;
}

.nav-value {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-weight: 500;
}

.text-success {
  color: #67c23a;
  font-weight: 500;
}

.text-danger {
  color: #f56c6c;
  font-weight: 500;
}

.text-muted {
  color: #909399;
}

.table-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.batch-actions {
  display: flex;
  justify-content: center;
  margin: 0 20px;
}

.batch-actions .el-card {
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.batch-info {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-data-table {
    overflow-x: auto;
  }
  
  .el-table {
    min-width: 800px;
  }
  
  .table-pagination {
    margin-top: 12px;
  }
  
  .batch-actions {
    margin: 0 10px;
  }
  
  .batch-actions .el-space {
    flex-wrap: wrap;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .batch-actions .el-card {
    border-radius: 12px;
  }
  
  .batch-info {
    font-size: 13px;
  }
}
</style>