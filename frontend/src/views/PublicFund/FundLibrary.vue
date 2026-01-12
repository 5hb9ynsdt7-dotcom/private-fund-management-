<template>
  <div class="fund-library-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">公募基金库</h2>
      <div class="header-actions">
        <el-button type="success" @click="handleRefreshAllNav" :loading="refreshingAll">
          <el-icon><Refresh /></el-icon>
          批量刷新净值
        </el-button>
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加基金
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选栏 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" :inline="true">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="基金代码或名称"
            clearable
            style="width: 200px"
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 基金列表表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="fundList"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="fund_code" label="基金代码" width="120" fixed />
        <el-table-column prop="fund_name" label="基金名称" min-width="300" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '运行中' : '已清盘' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="success" link size="small" @click="handleRefreshNav(row)" :loading="row._refreshing">
              刷新净值
            </el-button>
            <el-button type="primary" link size="small" @click="goToDetail(row.fund_code)">
              查看
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 添加基金对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加基金"
      width="600px"
      @close="resetAddForm"
    >
      <el-tabs v-model="addMethod">
        <el-tab-pane label="自动抓取" name="auto">
          <el-form :model="autoForm" label-width="100px">
            <el-form-item label="基金代码">
              <el-input
                v-model="autoForm.fund_code"
                placeholder="请输入6位数字基金代码"
                maxlength="6"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="fetching" @click="handleAutoFetch">
                自动抓取
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="手动录入" name="manual">
          <el-form :model="manualForm" label-width="100px">
            <el-form-item label="基金代码" required>
              <el-input v-model="manualForm.fund_code" placeholder="6位数字" maxlength="6" />
            </el-form-item>
            <el-form-item label="基金名称" required>
              <el-input v-model="manualForm.fund_name" placeholder="请输入基金名称" />
            </el-form-item>
            <el-form-item label="基金类型">
              <el-select v-model="manualForm.fund_type" placeholder="请选择">
                <el-option label="股票型" value="股票型" />
                <el-option label="债券型" value="债券型" />
                <el-option label="混合型" value="混合型" />
                <el-option label="货币型" value="货币型" />
                <el-option label="QDII" value="QDII" />
              </el-select>
            </el-form-item>
            <el-form-item label="基金公司">
              <el-input v-model="manualForm.fund_company" placeholder="请输入基金公司" />
            </el-form-item>
            <el-form-item label="基金经理">
              <el-input v-model="manualForm.fund_manager" placeholder="请输入基金经理" />
            </el-form-item>
            <el-form-item label="成立日期">
              <el-date-picker
                v-model="manualForm.establish_date"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="handleManualCreate">
                创建基金
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import publicFundAPI from '@/api/publicFund'

const router = useRouter()

// 搜索表单
const searchForm = reactive({
  keyword: ''
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 基金列表
const fundList = ref([])
const loading = ref(false)
const refreshingAll = ref(false)

// 添加基金对话框
const showAddDialog = ref(false)
const addMethod = ref('auto')
const fetching = ref(false)
const submitting = ref(false)

const autoForm = reactive({
  fund_code: ''
})

const manualForm = reactive({
  fund_code: '',
  fund_name: '',
  fund_type: '',
  fund_company: '',
  fund_manager: '',
  establish_date: ''
})

// 加载基金列表
const loadFundList = async () => {
  loading.value = true
  try {
    const params = {
      keyword: searchForm.keyword || undefined,
      page: pagination.page,
      page_size: pagination.page_size
    }

    const response = await publicFundAPI.getFundList(params)
    fundList.value = response.data.map(fund => ({
      ...fund,
      _refreshing: false  // 为每个基金添加刷新状态
    }))
    pagination.total = response.total
  } catch (error) {
    ElMessage.error('加载基金列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadFundList()
}

// 重置
const handleReset = () => {
  searchForm.keyword = ''
  handleSearch()
}

// 刷新净值
const handleRefreshNav = async (row) => {
  row._refreshing = true
  try {
    const response = await publicFundAPI.refreshNav(row.fund_code)
    if (response.success) {
      ElMessage.success(response.message)
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('刷新失败：' + (error.message || '未知错误'))
  } finally {
    row._refreshing = false
  }
}

// 批量刷新所有净值
const handleRefreshAllNav = async () => {
  ElMessageBox.confirm(
    '确定要刷新所有基金的净值吗？这可能需要一些时间。',
    '批量刷新确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
    .then(async () => {
      refreshingAll.value = true
      try {
        const response = await publicFundAPI.refreshAllNav()
        if (response.success) {
          const data = response.data || {}
          const successCount = data.success_count || 0
          const failedCount = data.failed_count || 0

          if (failedCount > 0) {
            ElMessage.warning(`${response.message}`)
          } else {
            ElMessage.success(`批量刷新成功！共刷新 ${successCount} 个基金净值`)
          }

          // 刷新列表
          await loadFundList()
        } else {
          ElMessage.error(response.message || '批量刷新失败')
        }
      } catch (error) {
        ElMessage.error('批量刷新失败：' + (error.message || '未知错误'))
      } finally {
        refreshingAll.value = false
      }
    })
    .catch(() => {})
}

// 分页变化
const handleSizeChange = (size) => {
  pagination.page_size = size
  loadFundList()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadFundList()
}

// 自动抓取
const handleAutoFetch = async () => {
  if (!autoForm.fund_code || autoForm.fund_code.length !== 6) {
    ElMessage.warning('请输入6位数字基金代码')
    return
  }

  fetching.value = true
  try {
    const response = await publicFundAPI.fetchFund(autoForm.fund_code)
    if (response.success) {
      ElMessage.success(response.message)
      showAddDialog.value = false
      loadFundList()
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    ElMessage.error('自动抓取失败：' + error.message)
  } finally {
    fetching.value = false
  }
}

// 手动创建
const handleManualCreate = async () => {
  if (!manualForm.fund_code || !manualForm.fund_name) {
    ElMessage.warning('请填写基金代码和名称')
    return
  }

  submitting.value = true
  try {
    await publicFundAPI.createFund(manualForm)
    ElMessage.success('创建成功')
    showAddDialog.value = false
    loadFundList()
  } catch (error) {
    ElMessage.error('创建失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

// 重置添加表单
const resetAddForm = () => {
  autoForm.fund_code = ''
  manualForm.fund_code = ''
  manualForm.fund_name = ''
  manualForm.fund_type = ''
  manualForm.fund_company = ''
  manualForm.fund_manager = ''
  manualForm.establish_date = ''
}

// 删除基金
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除基金 ${row.fund_name}？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await publicFundAPI.deleteFund(row.fund_code)
        ElMessage.success('删除成功')
        loadFundList()
      } catch (error) {
        ElMessage.error('删除失败：' + error.message)
      }
    })
    .catch(() => {})
}

// 跳转详情页
const goToDetail = (fundCode) => {
  router.push({
    name: 'PublicFundDetail',
    params: { fundCode }
  })
}

onMounted(() => {
  loadFundList()
})
</script>

<style scoped>
.fund-library-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: #333;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
