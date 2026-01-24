<template>
  <div class="stage-performance">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>阶段涨幅分析</h2>
      <p class="page-description">产品近期表现分析与涨跌幅统计</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-section">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="产品总数"
            :value="statistics.totalProducts"
            suffix="个"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><Grid /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="上涨产品"
            :value="statistics.risingProducts"
            suffix="个"
          >
            <template #prefix>
              <el-icon style="color: #f56c6c"><Top /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="下跌产品"
            :value="statistics.fallingProducts"
            suffix="个"
          >
            <template #prefix>
              <el-icon style="color: #67c23a"><Bottom /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic
            title="平均涨幅"
            :value="statistics.avgReturn"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon :style="`color: ${statistics.avgReturn >= 0 ? '#f56c6c' : '#67c23a'}`">
                <TrendCharts />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 筛选控制 -->
    <el-card class="filter-section">
      <el-row :gutter="16" align="middle">
        <el-col :span="12">
          <el-date-picker
            v-model="startDate"
            type="date"
            placeholder="期初日期"
            style="width: 48%; margin-right: 4%"
            format="MM/DD"
            value-format="YYYY-MM-DD"
            @change="onStartDateChange"
            clearable
          />
          <el-date-picker
            v-model="endDate"
            type="date"
            placeholder="期末日期"
            style="width: 48%"
            format="MM/DD"
            value-format="YYYY-MM-DD"
            @change="onEndDateChange"
            clearable
          />
        </el-col>
        <el-col :span="12">
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
          <el-button
            v-if="selectedProducts.length > 0"
            type="danger"
            @click="hideSelectedProducts"
          >
            隐藏选中 ({{ selectedProducts.length }})
          </el-button>
          <el-button
            v-if="selectedProducts.length > 0"
            type="success"
            @click="downloadSelectedData"
          >
            <el-icon><Download /></el-icon>
            下载图片 ({{ selectedProducts.length }})
          </el-button>
          <el-button @click="showAllProducts" size="default">显示全部</el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 产品列表表格 -->
    <el-card class="table-section">
      <template #header>
        <div class="table-header">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span>产品列表</span>
            <el-tag v-if="currentLoadedList" type="success" closable @close="clearLoadedList">
              当前清单：{{ currentLoadedList.name }}
            </el-tag>
          </div>
          <div class="table-actions">
            <el-dropdown @command="handleListCommand" style="margin-right: 8px;">
              <el-button size="small" type="primary">
                <el-icon><Collection /></el-icon>
                清单管理
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="save">
                    <el-icon><DocumentAdd /></el-icon>
                    保存当前清单
                  </el-dropdown-item>
                  <el-dropdown-item command="manage" divided>
                    <el-icon><Setting /></el-icon>
                    管理清单
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button @click="handleListCommand('load')" size="small" type="success" style="margin-right: 8px;">
              <el-icon><FolderOpened /></el-icon>
              已保存清单
            </el-button>
            <el-button @click="refreshData" size="small">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        v-loading="tableLoading"
        :data="displayData"
        style="width: 100%"
        stripe
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column 
          type="selection" 
          width="55" 
          fixed="left"
        />
        
        <el-table-column
          prop="fund_code"
          label="产品代码"
          width="120"
          fixed="left"
          align="center"
        />
        
        <el-table-column
          prop="short_name"
          label="产品简称"
          min-width="200"
          show-overflow-tooltip
        />
        
        <el-table-column
          prop="major_strategy"
          label="大类策略"
          width="150"
          align="center"
        >
          <template #default="{ row }">
            <el-select
              v-model="row.major_strategy"
              placeholder="选择大类策略"
              size="small"
              style="width: 130px"
              @change="() => handleStrategyChange(row)"
            >
              <el-option label="成长配置" value="成长配置" />
              <el-option label="底仓配置" value="底仓配置" />
              <el-option label="尾部对冲" value="尾部对冲" />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column
          prop="sub_strategy"
          label="细分策略"
          width="150"
          align="center"
        >
          <template #default="{ row }">
            <el-input
              v-model="row.sub_strategy"
              placeholder="输入细分策略"
              size="small"
              style="width: 130px"
              @blur="() => handleStrategyChange(row)"
              @keyup.enter="() => handleStrategyChange(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column
          prop="latest_nav_date"
          label="最新净值日期"
          width="130"
          align="center"
        >
          <template #default="{ row }">
            <span class="date-cell">{{ formatDate(row.latest_nav_date) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="latest_nav"
          label="最新净值"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <span class="nav-value">{{ formatNav(row.latest_nav) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="weekly_return"
          :label="`${selectedPeriodDisplay}涨跌幅`"
          width="160"
          align="center"
          sortable
        >
          <template #default="{ row }">
            <span :class="getReturnClass(row.weekly_return)">
              {{ formatPercent(row.weekly_return) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="ytd_return"
          label="今年以来涨跌幅"
          width="150"
          align="center"
          sortable
        >
          <template #default="{ row }">
            <span :class="getReturnClass(row.ytd_return)">
              {{ formatPercent(row.ytd_return) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="previous_nav_date"
          label="对比日期"
          width="130"
          align="center"
        >
          <template #default="{ row }">
            <span class="date-cell">{{ formatDate(row.previous_nav_date) }}</span>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="previous_nav"
          label="对比净值"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <span class="nav-value">{{ formatNav(row.previous_nav) }}</span>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 保存清单对话框 -->
    <el-dialog
      v-model="saveListDialogVisible"
      title="保存产品清单"
      width="500px"
    >
      <el-form :model="saveListForm" label-width="100px">
        <el-form-item label="清单名称" required>
          <el-input
            v-model="saveListForm.name"
            placeholder="请输入清单名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="清单描述">
          <el-input
            v-model="saveListForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入清单描述（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="产品数量">
          <el-tag type="info">{{ selectedProducts.length }} 个产品</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveListDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProductList" :loading="saveListLoading">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 加载清单对话框 -->
    <el-dialog
      v-model="loadListDialogVisible"
      title="加载产品清单"
      width="900px"
    >
      <el-table
        v-loading="loadListLoading"
        :data="productLists"
        style="width: 100%"
        row-key="id"
        :expand-row-keys="expandedListIds"
        @expand-change="handleListExpand"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div style="padding: 20px;">
              <el-table :data="row.items" border style="width: 100%">
                <el-table-column prop="fund_code" label="产品代码" width="120" align="center" />
                <el-table-column prop="short_name" label="产品简称" min-width="200" show-overflow-tooltip />
                <el-table-column label="最新净值日期" width="150" align="center">
                  <template #default="{ row: item }">
                    <span :style="{ color: getNavDateColor(item.latest_nav_date) }">
                      {{ formatDate(item.latest_nav_date) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>
              <div style="margin-top: 16px; text-align: right;">
                <el-button type="primary" @click="handleLoadList(row)">
                  加载此清单
                </el-button>
                <el-button @click="handleEditList(row)">
                  编辑清单
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="清单名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="产品数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.items?.length || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="loadListDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 管理清单对话框 -->
    <el-dialog
      v-model="manageListDialogVisible"
      title="管理产品清单"
      width="700px"
    >
      <el-table
        v-loading="loadListLoading"
        :data="productLists"
        style="width: 100%"
      >
        <el-table-column prop="name" label="清单名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="产品数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small">{{ row.items?.length || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="deleteProductList(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="manageListDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 编辑清单对话框 -->
    <el-dialog
      v-model="editListDialogVisible"
      title="编辑产品清单"
      width="900px"
    >
      <el-form :model="editListForm" label-width="100px">
        <el-form-item label="清单名称">
          <el-input v-model="editListForm.name" placeholder="请输入清单名称" />
        </el-form-item>
        <el-form-item label="清单描述">
          <el-input
            v-model="editListForm.description"
            type="textarea"
            :rows="2"
            placeholder="请输入清单描述（可选）"
          />
        </el-form-item>
      </el-form>

      <el-divider content-position="left">清单产品</el-divider>

      <el-transfer
        v-model="editListForm.selectedFundCodes"
        :data="allFundsForTransfer"
        :titles="['可选产品', '已选产品']"
        :button-texts="['移除', '添加']"
        :props="{
          key: 'value',
          label: 'label'
        }"
        filterable
        filter-placeholder="搜索产品"
        style="text-align: left; display: inline-block"
      />

      <template #footer>
        <el-button @click="editListDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="updateProductList" :loading="saveListLoading">
          保存修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { stagePerformanceAPI } from '@/api/stage-performance'
import html2canvas from 'html2canvas'
import axios from 'axios'

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000'

// 响应式数据
const tableLoading = ref(false)
const tableData = ref([])
const hiddenProducts = ref(new Set()) // 存储被隐藏的产品代码
const selectedProducts = ref([])

// 清单管理相关数据
const saveListDialogVisible = ref(false)
const loadListDialogVisible = ref(false)
const manageListDialogVisible = ref(false)
const editListDialogVisible = ref(false)
const saveListLoading = ref(false)
const loadListLoading = ref(false)
const productLists = ref([])
const expandedListIds = ref([])
const currentLoadedList = ref(null) // 当前加载的清单
const saveListForm = reactive({
  name: '',
  description: ''
})
const editListForm = reactive({
  id: null,
  name: '',
  description: '',
  selectedFundCodes: []
})

// 统计数据
const statistics = reactive({
  totalProducts: 0,
  risingProducts: 0,
  fallingProducts: 0,
  avgReturn: 0
})

// 日期范围选择
const dateRange = ref([])
const startDate = ref(null)
const endDate = ref(null)
const selectedPeriodDisplay = ref('近一周')

// 日期快捷选项
const dateShortcuts = [
  {
    text: '近一周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '近两周',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 14)
      return [start, end]
    }
  },
  {
    text: '近一个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    }
  },
  {
    text: '近三个月',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 90)
      return [start, end]
    }
  }
]

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

// 计算显示数据（排除隐藏的产品）
const displayData = computed(() => {
  let filtered = tableData.value.filter(item => !hiddenProducts.value.has(item.fund_code))

  // 如果有加载的清单，只显示清单中的产品
  if (currentLoadedList.value) {
    const listFundCodes = new Set(currentLoadedList.value.items.map(item => item.fund_code))
    filtered = filtered.filter(item => listFundCodes.has(item.fund_code))
  }

  // 三级排序逻辑
  filtered.sort((a, b) => {
    // 第一级：大类策略排序
    const strategyOrder = ['成长配置', '底仓配置', '尾部对冲']
    const strategyA = strategyOrder.indexOf(a.major_strategy)
    const strategyB = strategyOrder.indexOf(b.major_strategy)

    if (strategyA !== strategyB) {
      return (strategyA === -1 ? 999 : strategyA) - (strategyB === -1 ? 999 : strategyB)
    }

    // 第二级：细分策略排序
    let subStrategyOrder = []
    if (a.major_strategy === '成长配置') {
      subStrategyOrder = ['主观多头', '量化多头', '股票多头', '股票多空']
    } else if (a.major_strategy === '尾部对冲') {
      subStrategyOrder = ['宏观策略', 'CTA策略']
    }

    if (subStrategyOrder.length > 0) {
      const subStrategyA = subStrategyOrder.indexOf(a.sub_strategy)
      const subStrategyB = subStrategyOrder.indexOf(b.sub_strategy)

      if (subStrategyA !== subStrategyB) {
        return (subStrategyA === -1 ? 999 : subStrategyA) - (subStrategyB === -1 ? 999 : subStrategyB)
      }
    }

    // 第三级：涨跌幅降序排序
    const returnA = parseFloat(a.weekly_return) || 0
    const returnB = parseFloat(b.weekly_return) || 0
    return returnB - returnA
  })

  // 更新分页信息
  pagination.total = filtered.length

  // 分页处理
  const start = (pagination.page - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filtered.slice(start, end)
})

// Transfer组件数据源
const allFundsForTransfer = computed(() => {
  return tableData.value.map(fund => ({
    value: fund.fund_code,
    label: `${fund.fund_code} - ${fund.short_name || fund.fund_name}`
  }))
})

// 加载数据
const loadData = async () => {
  tableLoading.value = true
  try {
    let response

    if (dateRange.value && dateRange.value.length === 2) {
      // 使用自定义时间范围
      const params = {
        start_date: dateRange.value[0],
        end_date: dateRange.value[1]
      }

      response = await stagePerformanceAPI.getPeriodPerformance(params)
      
      // 处理自定义期间返回的数据格式
      if (response.success && response.data && response.data.products) {
        const mappedData = response.data.products.map(item => ({
          fund_code: item.fund_code,
          fund_name: item.fund_name,
          short_name: item.short_name,
          major_strategy: item.major_strategy,
          sub_strategy: item.sub_strategy,
          latest_nav_date: item.end_nav_date,
          latest_nav: item.end_nav,
          previous_nav_date: item.start_nav_date,
          previous_nav: item.start_nav,
          weekly_return: item.period_return,
          ytd_return: item.ytd_return // 使用后端计算的今年以来收益
        }))
        
        response.data = mappedData
        
        // 计算统计信息
        const totalProducts = mappedData.length
        const risingProducts = mappedData.filter(item => item.weekly_return > 0).length
        const fallingProducts = mappedData.filter(item => item.weekly_return < 0).length
        const validReturns = mappedData.map(item => item.weekly_return).filter(r => r !== null)
        const avgReturn = validReturns.length > 0 ? validReturns.reduce((a, b) => a + b, 0) / validReturns.length : 0
        
        response.statistics = {
          total_products: totalProducts,
          rising_products: risingProducts,
          falling_products: fallingProducts,
          avg_return: avgReturn
        }
      }
    } else {
      // 使用默认近一周数据
      const params = {
        days_limit: 7
      }

      response = await stagePerformanceAPI.getWeeklyPerformance(params)
    }
    
    if (response.success) {
      tableData.value = response.data || []
      
      // 更新统计数据（使用后端返回的统计信息）
      if (response.statistics) {
        Object.assign(statistics, {
          totalProducts: response.statistics.total_products || 0,
          risingProducts: response.statistics.rising_products || 0,
          fallingProducts: response.statistics.falling_products || 0,
          avgReturn: response.statistics.avg_return || 0
        })
      } else {
        updateStatistics()
      }
    } else {
      throw new Error(response.message || '获取数据失败')
    }
    
  } catch (error) {
    console.error('加载数据失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || '网络错误'
    ElMessage.error(`加载数据失败: ${errorMsg}`)
    tableData.value = []
    
    // 重置统计数据
    Object.assign(statistics, {
      totalProducts: 0,
      risingProducts: 0,
      fallingProducts: 0,
      avgReturn: 0
    })
  } finally {
    tableLoading.value = false
  }
}

// 更新统计数据
const updateStatistics = () => {
  const data = displayData.value
  if (data.length === 0) {
    Object.assign(statistics, {
      totalProducts: 0,
      risingProducts: 0,
      fallingProducts: 0,
      avgReturn: 0
    })
    return
  }
  
  const risingCount = data.filter(item => (parseFloat(item.weekly_return) || 0) > 0).length
  const fallingCount = data.filter(item => (parseFloat(item.weekly_return) || 0) < 0).length
  const totalReturn = data.reduce((sum, item) => sum + (parseFloat(item.weekly_return) || 0), 0)
  
  Object.assign(statistics, {
    totalProducts: data.length,
    risingProducts: risingCount,
    fallingProducts: fallingCount,
    avgReturn: data.length > 0 ? totalReturn / data.length : 0
  })
}

// 选择处理
const handleSelectionChange = (selection) => {
  selectedProducts.value = selection
}

// 隐藏选中的产品
const hideSelectedProducts = () => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请先选择要隐藏的产品')
    return
  }
  
  selectedProducts.value.forEach(product => {
    hiddenProducts.value.add(product.fund_code)
  })
  
  selectedProducts.value = []
  updateStatistics()
  ElMessage.success(`已隐藏 ${selectedProducts.value.length} 个产品`)
}

// 显示全部产品
const showAllProducts = () => {
  hiddenProducts.value.clear()
  updateStatistics()
  ElMessage.success('已恢复显示所有产品')
}

// 下载选中产品数据图片
const downloadSelectedData = async () => {
  if (selectedProducts.value.length === 0) {
    ElMessage.warning('请先选择要下载的产品')
    return
  }
  
  try {
    ElMessage.info('正在生成图片，请稍候...')
    
    // 创建包含选中产品数据的HTML容器
    const downloadContainer = document.createElement('div')
    downloadContainer.style.cssText = `
      position: absolute;
      top: -9999px;
      left: -9999px;
      width: 1200px;
      background: white;
      padding: 20px;
      font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
    `
    
    // 生成简化表格HTML（删除标题、统计卡片和部分列）
    const tableHtml = `
      <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
          <tr style="background-color: #f5f7fa;">
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: left;">产品代码</th>
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: left;">产品名称</th>
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: center;">大类策略</th>
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: center;">细分策略</th>
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: center;">最新净值日期</th>
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: center;">最新净值</th>
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: center;">${selectedPeriodDisplay.value}涨跌幅</th>
            <th style="border: 1px solid #dcdfe6; padding: 12px 8px; text-align: center;">今年以来涨跌幅</th>
          </tr>
        </thead>
        <tbody>
          ${selectedProducts.value.map(product => {
            const weeklyReturn = parseFloat(product.weekly_return) || 0
            const weeklyReturnColor = weeklyReturn > 0 ? '#f56c6c' : weeklyReturn < 0 ? '#67c23a' : '#909399'
            const weeklyReturnText = weeklyReturn ? `${weeklyReturn > 0 ? '+' : ''}${weeklyReturn.toFixed(2)}%` : '--'
            
            const ytdReturn = parseFloat(product.ytd_return) || 0
            const ytdReturnColor = ytdReturn > 0 ? '#f56c6c' : ytdReturn < 0 ? '#67c23a' : '#909399'
            const ytdReturnText = ytdReturn ? `${ytdReturn > 0 ? '+' : ''}${ytdReturn.toFixed(2)}%` : '--'
            
            return `
              <tr>
                <td style="border: 1px solid #dcdfe6; padding: 8px; font-family: 'Inter', monospace;">${product.fund_code || '--'}</td>
                <td style="border: 1px solid #dcdfe6; padding: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px;">${product.short_name || '--'}</td>
                <td style="border: 1px solid #dcdfe6; padding: 8px; text-align: center;">${product.major_strategy || '--'}</td>
                <td style="border: 1px solid #dcdfe6; padding: 8px; text-align: center;">${product.sub_strategy || '--'}</td>
                <td style="border: 1px solid #dcdfe6; padding: 8px; text-align: center; font-family: 'Inter', monospace;">${product.latest_nav_date || '--'}</td>
                <td style="border: 1px solid #dcdfe6; padding: 8px; text-align: center; font-family: 'Inter', monospace;">${product.latest_nav ? parseFloat(product.latest_nav).toFixed(4) : '--'}</td>
                <td style="border: 1px solid #dcdfe6; padding: 8px; text-align: center; font-family: 'Inter', monospace; color: ${weeklyReturnColor}; font-weight: bold;">${weeklyReturnText}</td>
                <td style="border: 1px solid #dcdfe6; padding: 8px; text-align: center; font-family: 'Inter', monospace; color: ${ytdReturnColor}; font-weight: bold;">${ytdReturnText}</td>
              </tr>
            `
          }).join('')}
        </tbody>
      </table>
    `
    
    downloadContainer.innerHTML = tableHtml
    document.body.appendChild(downloadContainer)
    
    // 使用html2canvas生成图片
    const canvas = await html2canvas(downloadContainer, {
      backgroundColor: '#ffffff',
      scale: 2, // 提高清晰度
      useCORS: true,
      allowTaint: true,
      width: 1200,
      height: downloadContainer.scrollHeight
    })
    
    // 清理临时容器
    document.body.removeChild(downloadContainer)
    
    // 下载图片
    const link = document.createElement('a')
    link.download = `阶段涨幅分析_${selectedProducts.value.length}个产品.png`
    link.href = canvas.toDataURL('image/png', 1.0)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`已成功下载 ${selectedProducts.value.length} 个产品的阶段涨幅图片`)
    
  } catch (error) {
    console.error('生成图片失败:', error)
    ElMessage.error('生成图片失败，请重试')
  }
}

// 日期范围变化处理
const onDateRangeChange = (dates) => {
  if (dates && dates.length === 2) {
    const startDateObj = new Date(dates[0])
    const endDateObj = new Date(dates[1])

    // 格式化显示日期（MM/DD格式）
    const formatDate = (date) => {
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      return `${month}${day}`
    }

    selectedPeriodDisplay.value = `${formatDate(startDateObj)}-${formatDate(endDateObj)}`
  } else {
    selectedPeriodDisplay.value = '近一周'
  }

  // 重新加载数据
  loadData()
}

// 期初日期变化处理
const onStartDateChange = (date) => {
  if (date && endDate.value) {
    dateRange.value = [date, endDate.value]
    onDateRangeChange(dateRange.value)
  }
}

// 期末日期变化处理
const onEndDateChange = (date) => {
  if (startDate.value && date) {
    dateRange.value = [startDate.value, date]
    onDateRangeChange(dateRange.value)
  }
}

// 搜索处理
const resetSearch = () => {
  dateRange.value = []
  startDate.value = null
  endDate.value = null
  selectedPeriodDisplay.value = '近一周'
  pagination.page = 1
  updateStatistics()
  loadData()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
}

const handleCurrentChange = (page) => {
  pagination.page = page
}

// 刷新数据
const refreshData = () => {
  loadData()
}

// 格式化函数
const formatDate = (date) => {
  if (!date) return '--'
  return new Date(date).toLocaleDateString('zh-CN')
}

const formatNav = (nav) => {
  if (nav == null || nav === '') return '--'
  return parseFloat(nav).toFixed(4)
}

const formatPercent = (percent) => {
  if (percent == null || percent === '') return '--'
  const value = parseFloat(percent)
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

// 根据净值日期返回颜色
const getNavDateColor = (navDate) => {
  if (!navDate) return '#999'

  const today = new Date()
  const nav = new Date(navDate)
  const diffDays = Math.floor((today - nav) / (1000 * 60 * 60 * 24))

  if (diffDays <= 3) return '#67c23a' // 绿色：3天内
  if (diffDays <= 7) return '#e6a23c' // 橙色：7天内
  return '#f56c6c' // 红色：超过7天
}

// 样式类
const getReturnClass = (value) => {
  if (value == null || value === '') return ''
  const num = parseFloat(value)
  if (num > 0) return 'return-positive'
  if (num < 0) return 'return-negative'
  return 'return-neutral'
}

// 处理策略变更
const handleStrategyChange = async (row) => {
  // 检查是否有必要字段
  if (!row.major_strategy && !row.sub_strategy) {
    return // 两个都为空，不保存
  }

  if (!row.major_strategy) {
    ElMessage.warning('请选择大类策略')
    return
  }

  try {
    // 先查询策略表中是否已存在该产品的策略
    const existingStrategyResponse = await axios.get(`${API_BASE}/api/strategy/${row.fund_code}`)

    const existingStrategy = existingStrategyResponse.data

    // 检查是否有冲突（同一产品策略信息不同）
    if (existingStrategy &&
        (existingStrategy.main_strategy !== row.major_strategy ||
         existingStrategy.sub_strategy !== row.sub_strategy)) {
      // 弹窗确认
      try {
        await ElMessageBox.confirm(
          `产品 ${row.fund_code} 的策略信息在策略表中已存在且不同：\n\n` +
          `现有策略：${existingStrategy.main_strategy} - ${existingStrategy.sub_strategy || '--'}\n` +
          `新策略：${row.major_strategy} - ${row.sub_strategy || '--'}\n\n` +
          `是否要更新为新的策略信息？`,
          '策略冲突确认',
          {
            confirmButtonText: '更新',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
      } catch {
        // 用户取消，恢复原值
        row.major_strategy = existingStrategy.main_strategy
        row.sub_strategy = existingStrategy.sub_strategy
        return
      }
    }
  } catch (error) {
    // 如果是404，说明策略不存在，继续保存
    if (error.response?.status !== 404) {
      console.error('查询策略失败:', error)
      // 非404错误，可能是网络问题，询问是否继续
      try {
        await ElMessageBox.confirm(
          '无法查询现有策略信息，是否继续保存？',
          '提示',
          {
            confirmButtonText: '继续保存',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
      } catch {
        return // 用户取消
      }
    }
  }

  // 保存策略信息
  try {
    await axios.post(`${API_BASE}/api/strategy/`, {
      fund_code: row.fund_code,
      main_strategy: row.major_strategy,
      sub_strategy: row.sub_strategy || '',
      is_qd: false
    })

    ElMessage.success(`产品 ${row.fund_code} 策略信息已保存`)

    // 保存成功后，从后端重新获取该产品的策略数据以确认保存成功
    try {
      const savedStrategyResponse = await axios.get(`${API_BASE}/api/strategy/${row.fund_code}`)
      const savedStrategy = savedStrategyResponse.data

      // 更新本地表格数据，确保显示的是数据库中的实际值
      row.major_strategy = savedStrategy.main_strategy
      row.sub_strategy = savedStrategy.sub_strategy
    } catch (fetchError) {
      console.warn('获取已保存的策略数据失败:', fetchError)
      // 即使获取失败，保存已经成功，不影响用户操作
    }
  } catch (error) {
    console.error('保存策略失败:', error)
    ElMessage.error(`保存失败: ${error.response?.data?.detail || error.message}`)
  }
}

const getStrategyTagType = (strategy) => {
  const typeMap = {
    '成长配置': 'danger',
    '底仓配置': 'success',
    '尾部对冲': 'warning'
  }
  return typeMap[strategy] || ''
}

// 清单管理 - 处理下拉菜单命令
const handleListCommand = (command) => {
  if (command === 'save') {
    if (selectedProducts.value.length === 0) {
      ElMessage.warning('请先选择要保存的产品')
      return
    }
    saveListForm.name = ''
    saveListForm.description = ''
    saveListDialogVisible.value = true
  } else if (command === 'load') {
    loadProductLists()
    loadListDialogVisible.value = true
  } else if (command === 'manage') {
    loadProductLists()
    manageListDialogVisible.value = true
  }
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载所有产品清单
const loadProductLists = async () => {
  try {
    loadListLoading.value = true
    const response = await axios.get(`${API_BASE}/api/product-lists/`)
    productLists.value = response.data
  } catch (error) {
    console.error('加载产品清单失败:', error)
    ElMessage.error('加载产品清单失败')
  } finally {
    loadListLoading.value = false
  }
}

// 处理清单展开/收起
const handleListExpand = (row, expandedRows) => {
  expandedListIds.value = expandedRows.map(r => r.id)
}

// 保存产品清单
const saveProductList = async () => {
  if (!saveListForm.name.trim()) {
    ElMessage.warning('请输入清单名称')
    return
  }

  try {
    saveListLoading.value = true
    const fundCodes = selectedProducts.value.map(p => p.fund_code)

    await axios.post(`${API_BASE}/api/product-lists/`, {
      name: saveListForm.name,
      description: saveListForm.description,
      fund_codes: fundCodes
    })

    ElMessage.success('清单保存成功')
    saveListDialogVisible.value = false
  } catch (error) {
    console.error('保存清单失败:', error)
    ElMessage.error('保存清单失败')
  } finally {
    saveListLoading.value = false
  }
}

// 加载清单（点击行时触发）
const handleLoadList = async (row) => {
  try {
    // 保存当前加载的清单
    currentLoadedList.value = row

    // 根据清单中的基金代码筛选表格数据
    const fundCodes = new Set(row.items.map(item => item.fund_code))

    // 清空当前选择
    selectedProducts.value = []

    // 筛选出清单中的产品
    const listProducts = tableData.value.filter(product => fundCodes.has(product.fund_code))

    // 设置为选中状态
    selectedProducts.value = listProducts

    // 重置分页到第一页
    pagination.page = 1

    ElMessage.success(`已加载清单"${row.name}"，共 ${listProducts.length} 个产品`)
    loadListDialogVisible.value = false
  } catch (error) {
    console.error('加载清单失败:', error)
    ElMessage.error('加载清单失败')
  }
}

// 清除当前加载的清单
const clearLoadedList = () => {
  currentLoadedList.value = null
  selectedProducts.value = []
  pagination.page = 1
  ElMessage.info('已清除清单过滤')
}

// 编辑清单
const handleEditList = (row) => {
  editListForm.id = row.id
  editListForm.name = row.name
  editListForm.description = row.description || ''
  editListForm.selectedFundCodes = row.items.map(item => item.fund_code)

  loadListDialogVisible.value = false
  editListDialogVisible.value = true
}

// 更新清单
const updateProductList = async () => {
  if (!editListForm.name.trim()) {
    ElMessage.warning('请输入清单名称')
    return
  }

  try {
    saveListLoading.value = true

    await axios.put(`${API_BASE}/api/product-lists/${editListForm.id}`, {
      name: editListForm.name,
      description: editListForm.description,
      fund_codes: editListForm.selectedFundCodes
    })

    ElMessage.success('清单更新成功')
    editListDialogVisible.value = false

    // 重新加载清单列表
    await loadProductLists()
  } catch (error) {
    console.error('更新清单失败:', error)
    ElMessage.error('更新清单失败')
  } finally {
    saveListLoading.value = false
  }
}

// 删除清单
const deleteProductList = async (listId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个清单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await axios.delete(`${API_BASE}/api/product-lists/${listId}`)
    ElMessage.success('清单删除成功')

    // 重新加载清单列表
    await loadProductLists()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除清单失败:', error)
      ElMessage.error('删除清单失败')
    }
  }
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.stage-performance {
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

.filter-section {
  margin-bottom: 24px;
}

.table-section {
  margin-bottom: 24px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

/* 涨跌幅颜色 */
.return-positive {
  color: #f56c6c;
  font-weight: 600;
}

.return-negative {
  color: #67c23a;
  font-weight: 600;
}

.return-neutral {
  color: #909399;
  font-weight: 500;
}

/* 数字字体 */
.nav-value,
.date-cell {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-section .el-col {
    margin-bottom: 16px;
  }
  
  .filter-section .el-col {
    margin-bottom: 12px;
  }
}

@media (max-width: 768px) {
  .stage-performance {
    padding: 16px;
  }
  
  .page-header h2 {
    font-size: 20px;
  }
  
  .stats-section .el-col {
    margin-bottom: 12px;
  }
  
  .filter-section .el-row {
    flex-direction: column;
  }
  
  .filter-section .el-col {
    margin-bottom: 12px;
    width: 100%;
  }
  
  .table-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}
</style>