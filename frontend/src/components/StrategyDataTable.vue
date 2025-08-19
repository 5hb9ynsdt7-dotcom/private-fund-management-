<template>
  <div class="strategy-data-table">
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
      @row-dblclick="handleRowDoubleClick"
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
        min-width="200"
        sortable="custom"
        show-overflow-tooltip
      />
      
      <!-- 大类策略 -->
      <el-table-column
        prop="main_strategy"
        label="大类策略"
        width="120"
        sortable="custom"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :color="getStrategyColor(row.main_strategy)"
            style="border: none; color: white;"
            size="small"
          >
            {{ row.main_strategy }}
          </el-tag>
        </template>
      </el-table-column>
      
      <!-- 细分策略 -->
      <el-table-column
        prop="sub_strategy"
        label="细分策略"
        width="140"
        sortable="custom"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.sub_strategy"
            type="info"
            size="small"
          >
            {{ row.sub_strategy }}
          </el-tag>
          <span v-else class="text-muted">--</span>
        </template>
      </el-table-column>
      
      <!-- 是否QD -->
      <el-table-column
        prop="is_qd"
        label="是否QD"
        width="80"
        sortable="custom"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.is_qd ? 'success' : 'info'"
            size="small"
          >
            {{ row.is_qd ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      
      <!-- 操作列 -->
      <el-table-column
        label="操作"
        width="140"
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
            
            <el-tooltip content="复制">
              <el-button
                type="success"
                size="small"
                circle
                @click="handleCopy(row)"
              >
                <el-icon><CopyDocument /></el-icon>
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
              type="success"
              size="small"
              @click="handleBatchEdit"
            >
              <el-icon><Edit /></el-icon>
              批量编辑
            </el-button>
            
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
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { strategyAPI } from '@/api/strategy'

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
  'delete',
  'row-dblclick'
])

const tableRef = ref()
const selectedRows = ref([])
const currentPage = ref(props.pagination.currentPage)
const pageSize = ref(props.pagination.pageSize)

// 是否移动端
const isMobile = computed(() => {
  return window.innerWidth < 768
})

// 策略颜色映射
const strategyColorMap = {
  '成长策略': '#36A2EB',
  '稳健策略': '#4BC0C0', 
  '尾部对冲': '#FFCE56',
  // 兼容旧数据
  '成长配置': '#36A2EB',
  '底仓配置': '#4BC0C0',
  'growth': '#36A2EB',
  'fixed_income': '#4BC0C0', 
  'macro': '#FFCE56',
  'other': '#FF6384'
}



// 获取行号
const getRowIndex = (index) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

// 获取策略颜色
const getStrategyColor = (strategy) => {
  return strategyColorMap[strategy] || '#909399'
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

// 处理行双击
const handleRowDoubleClick = (row) => {
  emit('row-dblclick', row)
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

// 处理QD状态变化
const handleQdStatusChange = async (row, newValue) => {
  // 添加loading状态
  row.qdLoading = true
  
  try {
    await strategyAPI.updateQdStatus(row.fund_code, newValue)
    row.is_qd = newValue
    ElMessage.success(`QD状态${newValue ? '开启' : '关闭'}成功`)
    emit('refresh')
  } catch (error) {
    console.error('更新QD状态失败:', error)
    ElMessage.error('更新QD状态失败')
  } finally {
    row.qdLoading = false
  }
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

// 处理复制
const handleCopy = (row) => {
  // TODO: 实现复制策略配置
  console.log('复制策略:', row)
  ElMessage.success('策略配置已复制')
}

// 处理删除
const handleDelete = (row) => {
  emit('delete', row)
}

// 批量编辑
const handleBatchEdit = () => {
  emit('batch-edit', selectedRows.value)
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
.strategy-data-table {
  width: 100%;
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

.el-table .el-table__row:hover {
  background-color: #f5f7fa;
}

/* QD开关样式 */
.el-switch {
  --el-switch-on-color: #67c23a;
  --el-switch-off-color: #dcdfe6;
}

/* 风险等级样式 */
.el-rate {
  --el-rate-icon-size: 14px;
  --el-rate-icon-margin: 2px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .strategy-data-table {
    overflow-x: auto;
  }
  
  .el-table {
    min-width: 1000px;
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