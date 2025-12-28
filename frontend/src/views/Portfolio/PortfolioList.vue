<template>
  <div class="portfolio-list">
    <div class="page-header">
      <h2>实盘组合</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建组合
      </el-button>
    </div>

    <div v-loading="loading" class="portfolio-cards">
      <el-empty v-if="portfolios.length === 0 && !loading" description="暂无组合，点击右上角新建组合" />

      <div v-for="portfolio in portfolios" :key="portfolio.id" class="portfolio-card">
        <div class="card-content" @click="goToDetail(portfolio.id)">
          <div class="card-header">
            <h3>{{ portfolio.portfolio_name }}</h3>
            <el-tag :type="portfolio.is_active ? 'success' : 'info'" size="small">
              {{ portfolio.is_active ? '激活' : '未激活' }}
            </el-tag>
          </div>

          <div class="card-stats">
            <div class="stat-item">
              <div class="stat-label">累计收益率</div>
              <div class="stat-value" :class="getReturnClass(portfolio.total_return_rate)">
                {{ formatPercent(portfolio.total_return_rate) }}
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-label">当前市值</div>
              <div class="stat-value">{{ formatMoney(portfolio.current_value) }}</div>
            </div>

            <div class="stat-item">
              <div class="stat-label">持仓数量</div>
              <div class="stat-value">{{ portfolio.position_count || 0 }}</div>
            </div>
          </div>

          <div class="card-footer">
            <span>最近更新：{{ formatDate(portfolio.updated_at) }}</span>
          </div>
        </div>

        <div class="card-actions">
          <el-button type="danger" size="small" @click.stop="handleDelete(portfolio)">
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建组合对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建组合" width="500px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="组合名称" required>
          <el-input v-model="createForm.portfolio_name" placeholder="请输入组合名称" />
        </el-form-item>

        <el-form-item label="组合描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="可选，描述组合的投资策略或目标"
          />
        </el-form-item>

        <el-alert
          title="提示：总投入金额将根据您的买入交易自动累加"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        />
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import portfolioAPI from '@/api/portfolio'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const portfolios = ref([])

const showCreateDialog = ref(false)
const createForm = ref({
  portfolio_name: '',
  description: ''
})

// 加载组合列表
const loadPortfolios = async () => {
  loading.value = true
  try {
    const response = await portfolioAPI.getPortfolioList()
    portfolios.value = response.data
  } catch (error) {
    console.error('加载组合列表失败:', error)
    ElMessage.error('加载组合列表失败')
  } finally {
    loading.value = false
  }
}

// 创建组合
const handleCreate = async () => {
  if (!createForm.value.portfolio_name) {
    ElMessage.warning('请输入组合名称')
    return
  }

  creating.value = true
  try {
    await portfolioAPI.createPortfolio(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false

    // 重置表单
    createForm.value = {
      portfolio_name: '',
      description: ''
    }

    // 重新加载列表
    await loadPortfolios()
  } catch (error) {
    console.error('创建组合失败:', error)
    ElMessage.error('创建组合失败')
  } finally {
    creating.value = false
  }
}

// 进入详情页
const goToDetail = (portfolioId) => {
  router.push(`/portfolio/${portfolioId}`)
}

// 删除组合
const handleDelete = async (portfolio) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除组合"${portfolio.portfolio_name}"吗？删除后将无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await portfolioAPI.deletePortfolio(portfolio.id)
    ElMessage.success('删除成功')
    await loadPortfolios()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除组合失败:', error)
      ElMessage.error('删除组合失败')
    }
  }
}

// 格式化函数
const formatMoney = (value) => {
  if (value == null) return '--'
  return '¥' + parseFloat(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const formatPercent = (value) => {
  if (value == null) return '--'
  const num = parseFloat(value)
  return (num >= 0 ? '+' : '') + num.toFixed(2) + '%'
}

const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getReturnClass = (value) => {
  if (value == null) return ''
  return parseFloat(value) >= 0 ? 'profit' : 'loss'
}

onMounted(() => {
  loadPortfolios()
})
</script>

<style scoped>
.portfolio-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
}

.portfolio-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.portfolio-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  overflow: hidden;
}

.card-content {
  padding: 20px;
  cursor: pointer;
}

.card-content:hover {
  background-color: #f9f9f9;
}

.portfolio-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-actions {
  padding: 10px 20px;
  border-top: 1px solid #f0f0f0;
  background-color: #fafafa;
  text-align: right;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.card-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.stat-value.profit {
  color: #f56c6c;
}

.stat-value.loss {
  color: #67c23a;
}

.card-footer {
  font-size: 12px;
  color: #909399;
  text-align: right;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
</style>
