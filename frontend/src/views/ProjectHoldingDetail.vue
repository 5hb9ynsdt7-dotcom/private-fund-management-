<template>
  <div class="project-holding-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item @click="$router.push('/project-holding')">
          项目持仓分析
        </el-breadcrumb-item>
        <el-breadcrumb-item>{{ projectName }}</el-breadcrumb-item>
      </el-breadcrumb>
      <h2>{{ projectName }}</h2>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载项目数据中...</span>
    </div>

    <div v-else>
      <!-- 选项卡 -->
      <el-tabs v-model="activeTab" class="main-tabs">
        <!-- 资产类别Tab -->
        <el-tab-pane label="资产类别" name="asset">
          <div class="tab-content">
            <!-- 新增按钮 -->
            <div class="action-bar">
              <el-button type="primary" @click="handleNewAsset">
                <el-icon><Plus /></el-icon>
                新增资产配置
              </el-button>
            </div>

            <!-- 资产配置列表 -->
            <el-card shadow="hover" class="data-card">
              <template #header>
                <span>资产配置记录</span>
              </template>
              
              <el-table 
                :data="assetRecords" 
                stripe
                style="width: 100%; min-width: 1200px"
                :header-cell-style="{ backgroundColor: '#f5f7fa' }"
              >
                <el-table-column prop="month" label="月份" width="140">
                  <template #default="scope">
                    {{ formatMonth(scope.row.month) }}
                  </template>
                </el-table-column>
                <el-table-column prop="a_share_ratio" label="A股比例" width="120" align="right">
                  <template #default="scope">
                    {{ formatPercentage(scope.row.a_share_ratio) }}
                  </template>
                </el-table-column>
                <el-table-column prop="h_share_ratio" label="H股比例" width="120" align="right">
                  <template #default="scope">
                    {{ formatPercentage(scope.row.h_share_ratio) }}
                  </template>
                </el-table-column>
                <el-table-column prop="us_share_ratio" label="美股比例" width="120" align="right">
                  <template #default="scope">
                    {{ formatPercentage(scope.row.us_share_ratio) }}
                  </template>
                </el-table-column>
                <el-table-column prop="other_market_ratio" label="其他市场比例" width="130" align="right">
                  <template #default="scope">
                    {{ formatPercentage(scope.row.other_market_ratio) }}
                  </template>
                </el-table-column>
                <el-table-column prop="stock_total_ratio" label="股票总仓位" width="140" align="right">
                  <template #default="scope">
                    <el-tag type="success" size="small">
                      {{ formatPercentage(scope.row.stock_total_ratio) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="global_bond_ratio" label="全球债券比例" width="130" align="right">
                  <template #default="scope">
                    {{ formatPercentage(scope.row.global_bond_ratio) }}
                  </template>
                </el-table-column>
                <el-table-column prop="convertible_bond_ratio" label="可转债比例" width="130" align="right">
                  <template #default="scope">
                    {{ formatPercentage(scope.row.convertible_bond_ratio) }}
                  </template>
                </el-table-column>
                <el-table-column prop="other_ratio" label="其他比例" width="120" align="right">
                  <template #default="scope">
                    {{ formatPercentage(scope.row.other_ratio) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="140" align="center">
                  <template #default="scope">
                    <div class="action-buttons">
                      <el-button
                        size="small"
                        type="primary"
                        @click="editAssetRecord(scope.row)"
                      >
                        编辑
                      </el-button>
                      <el-button
                        size="small"
                        type="danger"
                        @click="deleteAssetRecord(scope.row.id)"
                      >
                        删除
                      </el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 空状态 -->
              <div v-if="assetRecords.length === 0" class="empty-state">
                <el-empty description="暂无资产配置记录">
                  <el-button type="primary" @click="showAssetForm = true">
                    新增资产配置
                  </el-button>
                </el-empty>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 行业分类Tab -->
        <el-tab-pane label="行业分类" name="industry">
          <div class="tab-content">
            <!-- 新增按钮 -->
            <div class="action-bar">
              <el-button type="primary" @click="handleNewIndustry">
                <el-icon><Plus /></el-icon>
                新增行业配置
              </el-button>
            </div>

            <!-- 行业配置列表 -->
            <el-card shadow="hover" class="data-card">
              <template #header>
                <span>行业配置记录</span>
              </template>
              
              <el-table 
                :data="industryRecords" 
                stripe
                style="width: 100%"
                :header-cell-style="{ backgroundColor: '#f5f7fa' }"
              >
                <el-table-column prop="month" label="月份" width="120">
                  <template #default="scope">
                    {{ formatMonth(scope.row.month) }}
                  </template>
                </el-table-column>
                <el-table-column prop="ratio_type" label="计算方式" width="140">
                  <template #default="scope">
                    <el-tag 
                      :type="scope.row.ratio_type === 'based_on_stock' ? 'warning' : 'info'"
                      size="small"
                    >
                      {{ scope.row.ratio_type === 'based_on_stock' ? '基于股票仓位' : '基于总仓位' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="行业分布" min-width="300">
                  <template #default="scope">
                    <div class="industry-list">
                      <template v-for="i in 5" :key="i">
                        <div 
                          v-if="scope.row[`industry${i}`]" 
                          class="industry-item"
                        >
                          <span class="industry-name">{{ scope.row[`industry${i}`] }}</span>
                          <el-tag size="small" class="industry-ratio">
                            {{ formatPercentage(scope.row[`industry${i}_ratio`]) }}
                          </el-tag>
                          <el-tag 
                            v-if="scope.row.actual_ratios && scope.row.actual_ratios[scope.row[`industry${i}`]]"
                            type="success" 
                            size="small" 
                            class="actual-ratio"
                          >
                            实际: {{ formatPercentage(scope.row.actual_ratios[scope.row[`industry${i}`]]) }}
                          </el-tag>
                        </div>
                      </template>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="140" align="center">
                  <template #default="scope">
                    <div class="action-buttons">
                      <el-button
                        size="small"
                        type="primary"
                        @click="editIndustryRecord(scope.row)"
                      >
                        编辑
                      </el-button>
                      <el-button
                        size="small"
                        type="danger"
                        @click="deleteIndustryRecord(scope.row.id)"
                      >
                        删除
                      </el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 空状态 -->
              <div v-if="industryRecords.length === 0" class="empty-state">
                <el-empty description="暂无行业配置记录">
                  <el-button type="primary" @click="showIndustryForm = true">
                    新增行业配置
                  </el-button>
                </el-empty>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 资产配置表单对话框 -->
    <AssetConfigDialog
      v-model="showAssetForm"
      :project-name="projectName"
      :edit-data="currentAssetRecord"
      @success="handleAssetSuccess"
    />

    <!-- 行业配置表单对话框 -->
    <IndustryConfigDialog
      v-model="showIndustryForm"
      :project-name="projectName"
      :edit-data="currentIndustryRecord"
      @success="handleIndustrySuccess"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Plus } from '@element-plus/icons-vue'
import projectHoldingAPI from '@/api/project-holding'
import AssetConfigDialog from '@/components/AssetConfigDialog.vue'
import IndustryConfigDialog from '@/components/IndustryConfigDialog.vue'

// 路由参数
const route = useRoute()
const projectName = computed(() => route.params.projectName)

// 响应式数据
const loading = ref(false)
const activeTab = ref('asset')
const assetRecords = ref([])
const industryRecords = ref([])
const showAssetForm = ref(false)
const showIndustryForm = ref(false)
const currentAssetRecord = ref(null)
const currentIndustryRecord = ref(null)

// 获取项目详情数据
const fetchProjectDetail = async () => {
  loading.value = true
  try {
    const response = await projectHoldingAPI.getProjectDetail(projectName.value)
    if (response) {
      assetRecords.value = response.asset_records || []
      industryRecords.value = response.industry_records || []
    }
  } catch (error) {
    console.error('获取项目详情失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取项目详情失败')
  } finally {
    loading.value = false
  }
}

// 新增资产记录
const handleNewAsset = () => {
  // 获取最新的资产记录作为默认值
  if (assetRecords.value && assetRecords.value.length > 0) {
    // 数据从后端按月份降序返回，第一条就是最新的
    const latestRecord = assetRecords.value[0]
    
    // 计算下一个月份
    const latestMonth = new Date(latestRecord.month)
    const nextMonth = new Date(latestMonth.getFullYear(), latestMonth.getMonth() + 1, 1)
    const nextMonthString = nextMonth.toISOString().split('T')[0]
    
    // 复制数据并设置为下一个月份
    currentAssetRecord.value = {
      ...latestRecord,
      month: nextMonthString,
      id: undefined // 移除ID，因为这是新记录
    }
  } else {
    currentAssetRecord.value = null
  }
  
  showAssetForm.value = true
}

// 编辑资产记录
const editAssetRecord = (record) => {
  currentAssetRecord.value = { ...record }
  showAssetForm.value = true
}

// 新增行业记录
const handleNewIndustry = () => {
  // 获取最新的行业记录作为默认值
  if (industryRecords.value && industryRecords.value.length > 0) {
    // 数据从后端按月份降序返回，第一条就是最新的
    const latestRecord = industryRecords.value[0]
    
    // 计算下一个月份
    const latestMonth = new Date(latestRecord.month)
    const nextMonth = new Date(latestMonth.getFullYear(), latestMonth.getMonth() + 1, 1)
    const nextMonthString = nextMonth.toISOString().split('T')[0]
    
    // 复制数据并设置为下一个月份
    currentIndustryRecord.value = {
      ...latestRecord,
      month: nextMonthString,
      id: undefined, // 移除ID，因为这是新记录
      actual_ratios: undefined // 移除计算出的实际比例
    }
  } else {
    currentIndustryRecord.value = null
  }
  
  showIndustryForm.value = true
}

// 编辑行业记录
const editIndustryRecord = (record) => {
  currentIndustryRecord.value = { ...record }
  showIndustryForm.value = true
}

// 删除资产记录
const deleteAssetRecord = async (recordId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条资产配置记录吗？',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await projectHoldingAPI.deleteAssetRecord(recordId)
    ElMessage.success('删除成功')
    await fetchProjectDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 删除行业记录
const deleteIndustryRecord = async (recordId) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条行业配置记录吗？',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await projectHoldingAPI.deleteIndustryRecord(recordId)
    ElMessage.success('删除成功')
    await fetchProjectDetail()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 处理资产表单成功
const handleAssetSuccess = () => {
  console.log('资产表单提交成功')
  // 确保状态完全重置
  showAssetForm.value = false
  currentAssetRecord.value = null
  // 刷新数据
  fetchProjectDetail()
}

// 处理行业表单成功
const handleIndustrySuccess = () => {
  console.log('行业表单提交成功')
  // 确保状态完全重置
  showIndustryForm.value = false
  currentIndustryRecord.value = null
  // 刷新数据
  fetchProjectDetail()
}

// 格式化月份
const formatMonth = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${String(date.getMonth() + 1).padStart(2, '0')}月`
}

// 格式化百分比
const formatPercentage = (value) => {
  if (value === null || value === undefined) return '-'
  return `${parseFloat(value).toFixed(2)}%`
}

// 组件挂载时获取数据
onMounted(() => {
  fetchProjectDetail()
})
</script>

<style scoped>
.project-holding-detail {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
}

.page-header .el-breadcrumb {
  margin-bottom: 12px;
}

.page-header .el-breadcrumb-item {
  cursor: pointer;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.loading-container .el-icon {
  margin-right: 8px;
  font-size: 20px;
}

.main-tabs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.tab-content {
  padding: 0 24px 24px 24px;
}

.action-bar {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-start;
}

.data-card {
  border-radius: 8px;
  overflow-x: auto;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.industry-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.industry-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.industry-name {
  min-width: 80px;
  font-weight: 500;
  color: #303133;
}

.industry-ratio {
  background-color: #e1f3ff;
  color: #409eff;
}

.actual-ratio {
  background-color: #f0f9ff;
  color: #67c23a;
}

:deep(.el-tabs__header) {
  margin: 0;
  padding: 0 24px;
  background-color: #fff;
  border-radius: 8px 8px 0 0;
}

:deep(.el-tabs__nav-wrap) {
  padding: 12px 0;
}

:deep(.el-tabs__content) {
  padding: 0;
}

:deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-card__header) {
  background-color: #fafbfc;
  border-bottom: 1px solid #ebeef5;
  font-weight: 600;
  color: #303133;
}

.action-buttons {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}
</style>