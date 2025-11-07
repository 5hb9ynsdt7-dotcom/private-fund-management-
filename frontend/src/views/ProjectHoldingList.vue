<template>
  <div class="project-holding-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>项目持仓分析</h2>
      <p>管理和分析不同项目的持仓数据</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>加载项目列表中...</span>
    </div>

    <!-- 项目列表表格 -->
    <el-card v-else shadow="hover" class="table-card">
      <template #header>
        <div class="card-header">
          <span>项目列表</span>
          <el-tag type="info">共 {{ projects.length }} 个项目</el-tag>
        </div>
      </template>

      <el-table 
        :data="sortedProjects" 
        stripe
        style="width: 100%"
        :header-cell-style="{ backgroundColor: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column 
          label="序号" 
          width="80"
          align="center"
        >
          <template #default="scope">
            {{ scope.$index + 1 }}
          </template>
        </el-table-column>

        <el-table-column 
          prop="project_name" 
          label="项目名称" 
          min-width="200"
        >
          <template #default="scope">
            <div class="project-name-cell">
              <el-button 
                type="primary" 
                link 
                @click="navigateToDetail(scope.row.project_name)"
                class="project-name-link"
              >
                {{ scope.row.project_name }}
              </el-button>
              <el-tag 
                v-if="scope.row.latest_data_month" 
                type="success" 
                size="small"
                class="data-month-tag"
              >
                {{ scope.row.latest_data_month }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column 
          prop="main_strategy" 
          label="主策略" 
          width="120"
          align="center"
        >
          <template #default="scope">
            <el-tag :type="getStrategyTagType(scope.row.main_strategy)" size="small">
              {{ scope.row.main_strategy }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column 
          prop="sub_strategy" 
          label="子策略" 
          width="120"
          align="center"
        >
          <template #default="scope">
            <el-tag type="info" size="small">
              {{ scope.row.sub_strategy }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column 
          prop="latest_industries" 
          label="最新行业分类" 
          min-width="200"
          align="left"
        >
          <template #default="scope">
            <div v-if="scope.row.latest_industries && scope.row.latest_industries.length > 0" class="industries-container">
              <el-tag 
                v-for="industry in scope.row.latest_industries" 
                :key="industry"
                size="small"
                type="info"
                class="industry-tag"
              >
                {{ industry }}
              </el-tag>
            </div>
            <el-text v-else type="info">无数据</el-text>
          </template>
        </el-table-column>
        
        <el-table-column 
          label="操作" 
          width="150"
          align="center"
        >
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="navigateToDetail(scope.row.project_name)"
            >
              详情
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteProject(scope.row.project_name)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-if="projects.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无项目数据">
          <el-text type="info">
            请先上传净值数据并配置项目策略信息
          </el-text>
        </el-empty>
      </div>
    </el-card>

    <!-- 帮助信息 -->
    <el-alert
      title="使用说明"
      type="info"
      :closable="false"
      class="help-alert"
    >
      <ul class="help-list">
        <li>项目列表显示所有已上传净值数据的项目</li>
        <li>点击项目名称可进入该项目的持仓分析详情页面</li>
        <li>在详情页面可以录入和管理资产类别、行业分类数据</li>
        <li>系统支持按月录入数据，并自动计算相关比例</li>
      </ul>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import projectHoldingAPI from '@/api/project-holding'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const projects = ref([])

// 获取项目列表
const fetchProjectList = async () => {
  loading.value = true
  try {
    const response = await projectHoldingAPI.getProjectList()
    if (response && response.projects) {
      projects.value = response.projects
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取项目列表失败')
  } finally {
    loading.value = false
  }
}

// 导航到项目详情页
const navigateToDetail = (projectName) => {
  router.push({
    name: 'ProjectHoldingDetail',
    params: { projectName }
  })
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 多级排序逻辑
const sortedProjects = computed(() => {
  return [...projects.value].sort((a, b) => {
    // 第一级：按大类策略排序
    const mainStrategyOrder = getMainStrategyOrder(a.main_strategy, b.main_strategy)
    if (mainStrategyOrder !== 0) return mainStrategyOrder
    
    // 第二级：成长策略内部按子策略排序
    if (a.main_strategy === '成长策略' || a.main_strategy === '成长配置') {
      const subStrategyOrder = getSubStrategyOrder(a.sub_strategy, b.sub_strategy)
      if (subStrategyOrder !== 0) return subStrategyOrder
      
      // 第三级：主观多头内部按持仓市值从大到小排序
      if (a.sub_strategy === '主观多头' && b.sub_strategy === '主观多头') {
        return (b.total_market_value || 0) - (a.total_market_value || 0)
      }
    }
    
    // 默认按项目名称排序
    return a.project_name.localeCompare(b.project_name)
  })
})

// 大类策略排序顺序
const getMainStrategyOrder = (a, b) => {
  const order = {
    '成长策略': 1,
    '成长配置': 1,
    '稳健策略': 2,
    '固收策略': 2,
    '尾部对冲': 3
  }
  return (order[a] || 999) - (order[b] || 999)
}

// 子策略排序顺序（成长策略内部）
const getSubStrategyOrder = (a, b) => {
  const order = {
    '主观多头': 1,
    '股票多空': 2,
    '股债混合': 3,
    '量化多头': 4
  }
  return (order[a] || 999) - (order[b] || 999)
}

// 获取策略标签类型
const getStrategyTagType = (strategy) => {
  if (strategy === '成长策略' || strategy === '成长配置') return 'success'
  if (strategy === '稳健策略' || strategy === '固收策略') return 'warning'
  if (strategy === '尾部对冲') return 'danger'
  return 'info'
}

// 格式化市值
const formatMarketValue = (value) => {
  if (!value || value === 0) return '-'
  if (value >= 100000000) { // 1亿
    return `${(value / 100000000).toFixed(1)}亿`
  } else if (value >= 10000) { // 1万
    return `${(value / 10000).toFixed(0)}万`
  }
  return value.toLocaleString()
}

// 删除项目
const deleteProject = async (projectName) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目"${projectName}"吗？这将删除所有相关的配置记录。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await projectHoldingAPI.deleteProject(projectName)
    ElMessage.success('项目删除成功')
    await fetchProjectList() // 重新获取列表
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除项目失败')
    }
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchProjectList()
})
</script>

<style scoped>
.project-holding-list {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
  text-align: left;
}

.page-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
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

.table-card {
  margin-bottom: 24px;
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #303133;
}

.project-name-link {
  font-weight: 600;
  font-size: 15px;
}

.project-name-link:hover {
  text-decoration: underline;
}

.empty-state {
  padding: 40px 0;
}

.help-alert {
  border-radius: 8px;
}

.help-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.help-list li {
  margin: 4px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

:deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-table__header) {
  border-radius: 6px 6px 0 0;
}

:deep(.el-table .el-button--text) {
  padding: 0;
}

.project-name-cell {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
}

.data-month-tag {
  font-size: 11px;
  background-color: #f0f9ff;
  border-color: #67c23a;
  color: #67c23a;
}

:deep(.el-tag) {
  border-radius: 4px;
}

.industries-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.industry-tag {
  margin: 1px 0;
  background-color: #f0f2f5;
  border-color: #d9d9d9;
  color: #595959;
}
</style>