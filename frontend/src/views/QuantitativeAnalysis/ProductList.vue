<template>
  <div class="product-list-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="success" @click="handleFetchProducts">
        <el-icon><Refresh /></el-icon>
        刷新产品列表
      </el-button>

      <el-button type="primary" @click="handleSaveConfigs">
        <el-icon><Check /></el-icon>
        保存当前配置
      </el-button>

      <el-button type="danger" @click="handleDeleteSelected" :disabled="selectedProducts.length === 0">
        <el-icon><Delete /></el-icon>
        删除选中 ({{ selectedProducts.length }})
      </el-button>

      <el-button type="warning" @click="handleBatchConfig">
        <el-icon><Setting /></el-icon>
        批量配置
      </el-button>

      <div class="toolbar-right">
        <el-text type="info" style="margin-right: 20px">
          共 {{ filteredProducts.length }} 个量化多头产品
        </el-text>

        <el-input
          v-model="searchText"
          placeholder="搜索产品名称"
          clearable
          style="width: 240px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 产品列表表格 -->
    <el-table
      :data="filteredProducts"
      v-loading="loading"
      height="calc(100vh - 320px)"
      stripe
      class="product-table-equal-width"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" fixed />
      <el-table-column prop="productName" label="产品名称" min-width="200" fixed>
        <template #default="{ row }">
          <el-link type="primary" @click="handleViewProduct(row)">
            {{ row.displayName }}
            <span v-if="row.dividendCount > 0" class="dividend-badge">
              (分红{{ row.dividendCount }}次)
            </span>
          </el-link>
        </template>
      </el-table-column>

      <el-table-column prop="trackingIndex" label="跟踪指数" align="center">
        <template #default="{ row }">
          <el-select
            v-model="row.trackingIndex"
            placeholder="选择指数"
            @change="handleIndexChange(row)"
            size="small"
          >
            <el-option label="中证500" value="000905.SH" />
            <el-option label="沪深300" value="000300.SH" />
            <el-option label="中证800" value="000906.SH" />
            <el-option label="中证A500" value="000510.SH" />
            <el-option label="中证1000" value="000852.SH" />
            <el-option label="中证2000" value="932000.CSI" />
            <el-option label="上证指数" value="000001.SH" />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column prop="productType" label="产品类型" align="center">
        <template #default="{ row }">
          <el-select
            v-model="row.productType"
            placeholder="选择类型"
            @change="handleTypeChange(row)"
            size="small"
          >
            <el-option label="300指增" value="300指增" />
            <el-option label="500指增" value="500指增" />
            <el-option label="A500指增" value="A500指增" />
            <el-option label="1000指增" value="1000指增" />
            <el-option label="量化选股" value="量化选股" />
          </el-select>
        </template>
      </el-table-column>

      <el-table-column prop="latestNav" label="最新净值" align="center">
        <template #default="{ row }">
          <span class="nav-value">{{ formatNumber(row.latestNav, 4) }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="latestDate" label="净值日期" align="center">
        <template #default="{ row }">
          <span class="date-cell">{{ row.latestDate }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button
            type="primary"
            size="small"
            link
            @click="handleAnalyze(row)"
          >
            分析
          </el-button>

          <el-button
            type="success"
            size="small"
            link
            @click="handleViewChart(row)"
          >
            图表
          </el-button>

          <el-button
            type="warning"
            size="small"
            link
            @click="handleEditConfig(row)"
          >
            配置
          </el-button>

          <el-button
            type="danger"
            size="small"
            link
            @click="handleDividendEntry(row)"
          >
            分红录入
          </el-button>
        </template>
      </el-table-column>
    </el-table>


    <!-- 批量配置对话框 -->
    <el-dialog v-model="batchConfigDialogVisible" title="批量配置" width="500px">
      <el-form :model="batchConfigForm" label-width="100px">
        <el-form-item label="产品类型">
          <el-checkbox-group v-model="batchConfigForm.productTypes">
            <el-checkbox label="300指增" />
            <el-checkbox label="500指增" />
            <el-checkbox label="A500指增" />
            <el-checkbox label="1000指增" />
            <el-checkbox label="量化选股" />
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="跟踪指数">
          <el-select v-model="batchConfigForm.trackingIndex" placeholder="选择指数">
            <el-option label="中证500" value="000905.SH" />
            <el-option label="沪深300" value="000300.SH" />
            <el-option label="中证800" value="000906.SH" />
            <el-option label="中证A500" value="000510.SH" />
            <el-option label="中证1000" value="000852.SH" />
            <el-option label="中证2000" value="932000.CSI" />
            <el-option label="上证指数" value="000001.SH" />
          </el-select>
        </el-form-item>

        <el-form-item label="产品类型">
          <el-select v-model="batchConfigForm.productType" placeholder="选择类型">
            <el-option label="300指增" value="300指增" />
            <el-option label="500指增" value="500指增" />
            <el-option label="A500指增" value="A500指增" />
            <el-option label="1000指增" value="1000指增" />
            <el-option label="量化选股" value="量化选股" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="batchConfigDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchConfigSave">确定</el-button>
      </template>
    </el-dialog>

    <!-- 分红录入对话框 -->
    <el-dialog v-model="dividendDialogVisible" title="分红录入" width="500px">
      <el-form :model="dividendForm" :rules="dividendRules" ref="dividendFormRef" label-width="140px">
        <el-form-item label="产品名称">
          <el-text>{{ currentProduct?.displayName }}</el-text>
        </el-form-item>

        <el-form-item label="基准日" prop="exDividendDate">
          <el-date-picker
            v-model="dividendForm.exDividendDate"
            type="date"
            placeholder="选择除息日（基准日）"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="除权前净值" prop="preDividendNav">
          <el-input-number
            v-model="dividendForm.preDividendNav"
            :precision="4"
            :step="0.0001"
            :min="0"
            placeholder="请输入除权前净值"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="分红方案" prop="dividendPerShare">
          <el-input-number
            v-model="dividendForm.dividendPerShare"
            :precision="4"
            :step="0.0001"
            :min="0"
            placeholder="请输入每份分红金额"
            style="width: 100%"
          />
          <el-text type="info" size="small">单位：元/份产品份额</el-text>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dividendDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleDividendSubmit" :loading="dividendSubmitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000'

// 数据
const products = ref([])
const loading = ref(false)
const searchText = ref('')
const batchConfigDialogVisible = ref(false)
const selectedProducts = ref([])

// 批量配置表单
const batchConfigForm = ref({
  productTypes: [],
  trackingIndex: '',
  productType: ''
})

// 分红录入相关
const dividendDialogVisible = ref(false)
const dividendSubmitting = ref(false)
const currentProduct = ref(null)
const dividendFormRef = ref(null)
const dividendForm = ref({
  exDividendDate: '',
  preDividendNav: null,
  dividendPerShare: null
})

const dividendRules = {
  exDividendDate: [
    { required: true, message: '请选择基准日', trigger: 'change' }
  ],
  preDividendNav: [
    { required: true, message: '请输入除权前净值', trigger: 'blur' },
    { type: 'number', min: 0.0001, message: '除权前净值必须大于0', trigger: 'blur' }
  ],
  dividendPerShare: [
    { required: true, message: '请输入分红方案', trigger: 'blur' },
    { type: 'number', min: 0.0001, message: '分红金额必须大于0', trigger: 'blur' }
  ]
}

// 产品类型排序优先级
const productTypeOrder = {
  '300指增': 1,
  '500指增': 2,
  'A500指增': 3,
  '1000指增': 4,
  '量化选股': 5,
  '其他': 6
}

// 计算属性：筛选后的产品列表（按产品类型排序）
const filteredProducts = computed(() => {
  let result = products.value

  // 搜索筛选
  if (searchText.value) {
    result = result.filter(product =>
      product.displayName.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }

  // 按产品类型排序
  result = [...result].sort((a, b) => {
    const orderA = productTypeOrder[a.productType] || 999
    const orderB = productTypeOrder[b.productType] || 999
    return orderA - orderB
  })

  return result
})

// 格式化数字
const formatNumber = (value, decimals = 2) => {
  if (!value && value !== 0) return '--'
  return Number(value).toFixed(decimals)
}

// 获取产品列表
const handleFetchProducts = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/quantitative/products`)

    // 后端已经筛选了量化多头产品，直接使用
    products.value = response.data

    // 从localStorage加载已保存的配置
    loadSavedConfigs()

    ElMessage.success(`成功加载 ${products.value.length} 个量化多头产品`)
  } catch (error) {
    ElMessage.error('获取产品列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 从localStorage加载已保存的配置
const loadSavedConfigs = () => {
  try {
    const savedConfigs = localStorage.getItem('quantProductConfigs')
    if (savedConfigs) {
      const configs = JSON.parse(savedConfigs)

      // 应用已保存的配置到产品列表
      products.value.forEach(product => {
        const savedConfig = configs[product.fundCode]
        if (savedConfig) {
          product.trackingIndex = savedConfig.trackingIndex || product.trackingIndex
          product.productType = savedConfig.productType || product.productType
        }
      })

      console.log('已加载保存的配置')
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 保存当前配置到localStorage
const handleSaveConfigs = () => {
  try {
    const configs = {}
    products.value.forEach(product => {
      configs[product.fundCode] = {
        trackingIndex: product.trackingIndex,
        productType: product.productType
      }
    })

    localStorage.setItem('quantProductConfigs', JSON.stringify(configs))
    ElMessage.success('配置已保存到本地')
  } catch (error) {
    ElMessage.error('保存配置失败：' + error.message)
  }
}

// 选择变更处理
const handleSelectionChange = (selection) => {
  selectedProducts.value = selection
}

// 删除选中的产品
const handleDeleteSelected = () => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请先选择要删除的产品')
    return
  }

  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedProducts.value.length} 个产品吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // 获取要删除的产品代码
    const selectedCodes = selectedProducts.value.map(p => p.fundCode)

    // 从列表中移除选中的产品
    products.value = products.value.filter(
      product => !selectedCodes.includes(product.fundCode)
    )

    // 同时从localStorage中删除这些产品的配置
    try {
      const savedConfigs = localStorage.getItem('quantProductConfigs')
      if (savedConfigs) {
        const configs = JSON.parse(savedConfigs)
        selectedCodes.forEach(code => {
          delete configs[code]
        })
        localStorage.setItem('quantProductConfigs', JSON.stringify(configs))
      }
    } catch (error) {
      console.error('删除配置失败:', error)
    }

    selectedProducts.value = []
    ElMessage.success('已删除选中的产品')
  }).catch(() => {
    // 用户取消删除
  })
}


// 批量配置
const handleBatchConfig = () => {
  batchConfigDialogVisible.value = true
}

// 保存批量配置
const handleBatchConfigSave = () => {
  // 应用批量配置到选中的产品
  products.value.forEach(product => {
    if (batchConfigForm.value.productTypes.includes(product.productType)) {
      if (batchConfigForm.value.trackingIndex) {
        product.trackingIndex = batchConfigForm.value.trackingIndex
      }
      if (batchConfigForm.value.productType) {
        product.productType = batchConfigForm.value.productType
      }
    }
  })

  ElMessage.success('批量配置已应用')
  batchConfigDialogVisible.value = false

  // 保存配置到后端
  saveProductConfigs()
}

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑由computed属性自动处理
}

// 查看产品详情
const handleViewProduct = (row) => {
  localStorage.setItem('selectedQuantProduct', row.fundCode)
  localStorage.setItem('selectedQuantProductName', row.displayName)
  router.push(`/quantitative-analysis/single-product/${row.fundCode}`)
}

// 分析产品
const handleAnalyze = (row) => {
  localStorage.setItem('selectedQuantProduct', row.fundCode)
  localStorage.setItem('selectedQuantProductName', row.displayName)
  router.push(`/quantitative-analysis/single-product/${row.fundCode}`)
}

// 查看图表
const handleViewChart = (row) => {
  localStorage.setItem('selectedQuantProduct', row.fundCode)
  localStorage.setItem('selectedQuantProductName', row.displayName)
  router.push(`/quantitative-analysis/single-product/${row.fundCode}`)
}

// 编辑配置
const handleEditConfig = (row) => {
  ElMessageBox.confirm(
    `配置产品：${row.displayName}`,
    '编辑配置',
    {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      type: 'info',
    }
  ).then(() => {
    saveProductConfig(row)
  })
}

// 分红录入
const handleDividendEntry = (row) => {
  currentProduct.value = row
  dividendForm.value = {
    exDividendDate: '',
    preDividendNav: null,
    dividendPerShare: null
  }
  dividendDialogVisible.value = true
}

// 提交分红数据
const handleDividendSubmit = async () => {
  if (!dividendFormRef.value) return

  try {
    await dividendFormRef.value.validate()
  } catch (error) {
    return
  }

  dividendSubmitting.value = true

  try {
    const response = await axios.post(
      `${API_BASE}/api/dividend/create`,
      null,
      {
        params: {
          fund_code: currentProduct.value.fundCode,
          ex_dividend_date: dividendForm.value.exDividendDate,
          pre_dividend_nav: dividendForm.value.preDividendNav,
          dividend_per_share: dividendForm.value.dividendPerShare
        }
      }
    )

    if (response.data.success) {
      ElMessage.success('分红记录创建成功')
      dividendDialogVisible.value = false
    } else {
      ElMessage.error(response.data.message || '创建失败')
    }
  } catch (error) {
    console.error('创建分红记录失败:', error)
    ElMessage.error(error.response?.data?.detail || '创建失败，请重试')
  } finally {
    dividendSubmitting.value = false
  }
}

// 指数变更
const handleIndexChange = (row) => {
  // 保存到localStorage
  saveConfigToLocalStorage(row)
}

// 类型变更
const handleTypeChange = (row) => {
  // 保存到localStorage
  saveConfigToLocalStorage(row)
}

// 保存单个产品配置到localStorage
const saveConfigToLocalStorage = (product) => {
  try {
    const savedConfigs = localStorage.getItem('quantProductConfigs')
    const configs = savedConfigs ? JSON.parse(savedConfigs) : {}

    configs[product.fundCode] = {
      trackingIndex: product.trackingIndex,
      productType: product.productType
    }

    localStorage.setItem('quantProductConfigs', JSON.stringify(configs))
  } catch (error) {
    console.error('保存配置失败:', error)
  }
}

// 保存单个产品配置
const saveProductConfig = async (product) => {
  try {
    await axios.post(`${API_BASE}/api/quantitative/product-config`, {
      fundCode: product.fundCode,
      productName: product.productName,
      trackingIndex: product.trackingIndex,
      productType: product.productType
    })
    ElMessage.success('配置已保存')
  } catch (error) {
    ElMessage.error('保存配置失败：' + error.message)
  }
}

// 保存所有产品配置
const saveProductConfigs = async () => {
  try {
    await axios.post(`${API_BASE}/api/quantitative/product-configs`, {
      products: products.value.map(p => ({
        fundCode: p.fundCode,
        productName: p.productName,
        trackingIndex: p.trackingIndex,
        productType: p.productType
      }))
    })
  } catch (error) {
    console.error('保存配置失败：', error)
  }
}

// 初始化
onMounted(() => {
  handleFetchProducts()
})
</script>

<style scoped>
.product-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-value {
  font-family: 'Inter', 'SF Pro Display', monospace;
  font-weight: 500;
  color: #303133;
}

.date-cell {
  font-family: 'Inter', 'SF Pro Display', monospace;
  color: #606266;
}

.upload-demo {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

:deep(.el-icon--upload) {
  font-size: 48px;
  color: #909399;
  margin-bottom: 16px;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

/* 产品列表表格：强制等宽列布局 */
.product-table-equal-width {
  width: 100% !important;
}

.product-table-equal-width :deep(table) {
  table-layout: fixed !important;
  width: 100% !important;
}

.product-table-equal-width :deep(.el-table__header table),
.product-table-equal-width :deep(.el-table__body table) {
  table-layout: fixed !important;
  width: 100% !important;
}

.product-table-equal-width :deep(.el-table__cell) {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

/* 分红次数样式 */
.dividend-badge {
  color: #F56C6C;
  font-size: 12px;
  margin-left: 4px;
  font-weight: 500;
}
</style>