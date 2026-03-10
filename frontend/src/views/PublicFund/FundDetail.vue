<template>
  <div class="fund-detail-container">
    <!-- 返回按钮 -->
    <div class="back-button">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回基金库
      </el-button>
    </div>

    <!-- 基金信息卡片 -->
    <FundInfoCard v-if="fundInfo.fund_code" :fund-info="fundInfo">
      <template #actions>
        <el-button size="small" @click="showUploadDialog = true">上传净值</el-button>
        <el-button size="small" type="primary" @click="showAnalysisDialog = true">
          分析
        </el-button>
      </template>
    </FundInfoCard>

    <!-- 核心指标卡片 -->
    <el-card v-if="indicators" class="indicators-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>核心指标</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
          />
        </div>
      </template>
      <div class="indicators-grid">
        <IndicatorCard
          label="年化收益"
          :value="indicators.annual_return"
          unit="%"
          :colorize="true"
        />
        <IndicatorCard
          label="波动率"
          :value="indicators.volatility"
          unit="%"
          :colorize="false"
        />
        <IndicatorCard
          label="最大回撤"
          :value="indicators.max_drawdown"
          unit="%"
          :colorize="true"
        />
        <IndicatorCard
          label="夏普比率"
          :value="indicators.sharpe_ratio"
          unit=""
          :colorize="true"
          :precision="3"
        />
      </div>
    </el-card>

    <!-- 净值走势图 -->
    <el-card v-if="navList.length > 0" class="chart-card" shadow="hover">
      <NavChart :nav-data="navList" height="450px" />
    </el-card>

    <!-- 历史净值数据表格 -->
    <el-card class="nav-table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>历史净值数据</span>
          <el-button size="small" @click="refreshNavList">刷新</el-button>
        </div>
      </template>
      <el-table
        v-loading="navLoading"
        :data="navList"
        border
        stripe
        max-height="400"
      >
        <el-table-column prop="nav_date" label="日期" width="120" fixed />
        <el-table-column prop="unit_nav" label="单位净值" width="120" align="right" />
        <el-table-column prop="accum_nav" label="累计净值" width="120" align="right" />
        <el-table-column label="日涨跌幅" width="120" align="right">
          <template #default="{ row }">
            <span
              v-if="row.daily_return"
              :style="{ color: row.daily_return > 0 ? '#f5222d' : '#52c41a' }"
            >
              {{ row.daily_return > 0 ? '+' : '' }}{{ row.daily_return }}%
            </span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="data_source" label="数据来源" width="100" />
      </el-table>
    </el-card>

    <!-- 上传净值对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传净值数据" width="500px">
      <el-upload
        class="upload-demo"
        drag
        :action="uploadAction"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        accept=".xlsx,.xls"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 xlsx/xls 文件，文件需包含：基金代码、净值日期、单位净值、累计净值
          </div>
        </template>
      </el-upload>
    </el-dialog>

    <!-- 分析对话框 -->
    <el-dialog v-model="showAnalysisDialog" title="基金分析" width="600px">
      <el-form :model="analysisForm" label-width="100px">
        <el-form-item label="分析区间">
          <el-date-picker
            v-model="analysisDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="保存结果">
          <el-switch v-model="analysisForm.save_result" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="analyzing" @click="handleAnalyze">
            开始分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, UploadFilled } from '@element-plus/icons-vue'
import FundInfoCard from '@/components/PublicFund/FundInfoCard.vue'
import NavChart from '@/components/PublicFund/NavChart.vue'
import IndicatorCard from '@/components/PublicFund/IndicatorCard.vue'
import publicFundAPI from '@/api/publicFund'

const route = useRoute()
const router = useRouter()

const fundCode = computed(() => route.params.fundCode)

// 基金信息
const fundInfo = ref({})

// 净值列表
const navList = ref([])
const navLoading = ref(false)

// 核心指标
const indicators = ref(null)
const dateRange = ref([])

// 对话框
const showUploadDialog = ref(false)
const showAnalysisDialog = ref(false)
const analyzing = ref(false)

// 分析表单
const analysisForm = reactive({
  save_result: true
})
const analysisDateRange = ref([])

// 上传配置
const uploadAction = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8003'}/api/public-fund/nav/upload`
})
const uploadHeaders = computed(() => {
  return {
    // 如果需要token，在这里添加
  }
})

// 加载基金信息
const loadFundInfo = async () => {
  try {
    const response = await publicFundAPI.getFundDetail(fundCode.value)
    fundInfo.value = response
  } catch (error) {
    ElMessage.error('加载基金信息失败：' + error.message)
  }
}

// 加载净值数据
const loadNavList = async () => {
  navLoading.value = true
  try {
    const params = {
      sort: 'desc'
    }

    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const response = await publicFundAPI.getNavList(fundCode.value, params)
    navList.value = response.data.sort((a, b) => a.nav_date.localeCompare(b.nav_date))
  } catch (error) {
    ElMessage.error('加载净值数据失败：' + error.message)
  } finally {
    navLoading.value = false
  }
}

// 日期范围变化
const handleDateRangeChange = async () => {
  await loadNavList()
  await loadIndicators()
}

// 加载指标
const loadIndicators = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    return
  }

  try {
    const response = await publicFundAPI.analyzeSingleFund({
      fund_code: fundCode.value,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      save_result: false
    })
    indicators.value = response.indicators
  } catch (error) {
    ElMessage.error('加载指标失败：' + error.message)
  }
}

// 刷新净值列表
const refreshNavList = () => {
  loadNavList()
}

// 上传前校验
const beforeUpload = (file) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
    file.type === 'application/vnd.ms-excel'

  if (!isExcel) {
    ElMessage.error('只能上传 Excel 文件！')
    return false
  }

  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB！')
    return false
  }

  return true
}

// 上传成功
const handleUploadSuccess = (response) => {
  ElMessage.success(`上传成功：成功 ${response.success_count} 条，失败 ${response.failed_count} 条`)
  showUploadDialog.value = false
  loadNavList()
}

// 上传失败
const handleUploadError = (error) => {
  ElMessage.error('上传失败：' + error.message)
}

// 执行分析
const handleAnalyze = async () => {
  if (!analysisDateRange.value || analysisDateRange.value.length !== 2) {
    ElMessage.warning('请选择分析区间')
    return
  }

  analyzing.value = true
  try {
    const response = await publicFundAPI.analyzeSingleFund({
      fund_code: fundCode.value,
      start_date: analysisDateRange.value[0],
      end_date: analysisDateRange.value[1],
      save_result: analysisForm.save_result
    })

    ElMessage.success('分析完成')
    showAnalysisDialog.value = false

    // 更新显示的指标
    dateRange.value = analysisDateRange.value
    indicators.value = response.indicators
    await loadNavList()
  } catch (error) {
    ElMessage.error('分析失败：' + error.message)
  } finally {
    analyzing.value = false
  }
}

// 返回
const goBack = () => {
  router.push({ name: 'PublicFundLibrary' })
}

onMounted(async () => {
  await loadFundInfo()

  // 设置默认日期范围（近一年）
  const endDate = new Date()
  const startDate = new Date()
  startDate.setFullYear(startDate.getFullYear() - 1)

  dateRange.value = [
    startDate.toISOString().split('T')[0],
    endDate.toISOString().split('T')[0]
  ]
  analysisDateRange.value = [...dateRange.value]

  await loadNavList()
  await loadIndicators()
})
</script>

<style scoped>
.fund-detail-container {
  padding: 20px;
}

.back-button {
  margin-bottom: 20px;
}

.indicators-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.nav-table-card {
  margin-bottom: 20px;
}
</style>
