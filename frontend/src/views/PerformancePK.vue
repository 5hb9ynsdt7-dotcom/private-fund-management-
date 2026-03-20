<template>
  <div class="performance-pk">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2>业绩PK</h2>
        <p>对比不同产品/组合的历史表现，一眼看出谁更稳、谁更赚、谁回撤控制更好</p>
      </div>
      <div style="display: flex; gap: 12px;">
        <el-button size="large" @click="downloadAsImage" :disabled="!comparisonResult">
          <el-icon><Download /></el-icon>
          下载图片
        </el-button>
        <el-button size="large" @click="showHistoryDrawer = true">
          <el-icon><Clock /></el-icon>
          查看历史PK
        </el-button>
      </div>
    </div>

    <!-- 筛选区 -->
    <el-card class="filter-section">
      <el-row :gutter="16">
        <!-- 对象选择 -->
        <el-col :span="8">
          <div class="filter-label">
            选择产品/组合
            <el-tooltip content="最多选择10个对象进行对比，支持单品和组合混合对比">
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <el-select
            v-model="selectedObjects"
            multiple
            filterable
            placeholder="搜索并选择产品或组合"
            style="width: 100%"
            @change="handleObjectChange"
            :loading="loadingProducts"
          >
            <el-option-group label="保存的组合">
              <el-option
                v-for="item in portfolioObjects"
                :key="item.id"
                :label="item.name"
                :value="item.id"
                :disabled="selectedObjects.length >= 10 && !selectedObjects.includes(item.id)"
              >
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>{{ item.name }}</span>
                  <el-tag
                    size="small"
                    :type="item.type === 'backtest' ? 'success' : 'warning'"
                    style="margin-left: 4px;"
                  >
                    {{ item.category }}
                  </el-tag>
                </div>
              </el-option>
            </el-option-group>
            <el-option-group label="产品">
              <el-option
                v-for="item in productObjects"
                :key="item.id"
                :label="item.name"
                :value="item.id"
                :disabled="selectedObjects.length >= 10 && !selectedObjects.includes(item.id)"
              >
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span>{{ item.name }}</span>
                  <span style="color: #8492a6; font-size: 12px;">
                    {{ item.code }}
                    <el-tag v-if="item.type === 'public'" size="small" type="info" style="margin-left: 4px;">公募</el-tag>
                  </span>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </el-col>

        <!-- 时间区间选择 -->
        <el-col :span="8">
          <div class="filter-label">时间区间</div>
          <el-space>
            <el-select v-model="timeRange" @change="handleTimeRangeChange" style="width: 150px;">
              <el-option label="近1个月" value="1m" />
              <el-option label="近3个月" value="3m" />
              <el-option label="近6个月" value="6m" />
              <el-option label="近1年" value="1y" />
              <el-option label="近3年" value="3y" />
              <el-option label="成立以来" value="all" />
              <el-option label="自定义" value="custom" />
            </el-select>
            <el-date-picker
              v-if="timeRange === 'custom'"
              v-model="customStartDate"
              type="date"
              placeholder="期初日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 48%; margin-right: 4%"
              @change="onCustomDateChange"
            />
            <el-date-picker
              v-if="timeRange === 'custom'"
              v-model="customEndDate"
              type="date"
              placeholder="期末日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 48%"
              @change="onCustomDateChange"
            />
          </el-space>
        </el-col>

        <!-- 基准选择 -->
        <el-col :span="8">
          <div class="filter-label">
            对标基准
            <el-tooltip content="选择对比的基准指数">
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
          <el-select v-model="selectedBenchmark" placeholder="选择基准指数" style="width: 100%;">
            <el-option label="无" value="" />
            <el-option label="沪深300" value="000300" />
            <el-option label="中证500" value="000905" />
            <el-option label="中证1000" value="000852" />
            <el-option label="上证指数" value="000001" />
            <el-option label="创业板指" value="399006" />
            <el-option label="恒生指数" value="HSI" />
            <el-option label="货币基金收益" value="MONEY_FUND" />
          </el-select>
        </el-col>
      </el-row>

      <el-row style="margin-top: 20px;">
        <el-col :span="24">
          <div class="filter-label">数据对齐方式</div>
          <el-radio-group v-model="alignMode">
            <el-radio value="common">按共同区间对齐（推荐）</el-radio>
            <el-radio value="separate">按各自成立以来分别展示</el-radio>
          </el-radio-group>
        </el-col>
      </el-row>
    </el-card>

    <!-- 已选对象列表区 -->
    <el-card class="selected-objects-section" v-if="selectedObjectsList.length > 0">
      <div class="section-title">已选对比对象（{{ selectedObjectsList.length }}/10）</div>
      <div class="objects-tags">
        <el-tag
          v-for="(obj, index) in selectedObjectsList"
          :key="obj.id"
          closable
          @close="handleRemoveObject(obj.id)"
          size="large"
          class="object-tag"
          :type="index % 4 === 0 ? 'primary' : index % 4 === 1 ? 'success' : index % 4 === 2 ? 'warning' : 'danger'"
        >
          <div class="tag-content">
            <div class="tag-name">
              {{ obj.name }}
              <el-tag v-if="obj.type === 'public'" size="small" type="info" style="margin-left: 6px;">公募</el-tag>
            </div>
            <div class="tag-meta">{{ obj.code }} | {{ obj.category || '未分类' }}</div>
          </div>
        </el-tag>
      </div>
    </el-card>

    <!-- 对比按钮 -->
    <div class="action-section" v-if="selectedObjectsList.length >= 2">
      <el-button type="primary" size="large" @click="handleCompare" :loading="comparing">
        <el-icon><TrendCharts /></el-icon>
        开始对比分析
      </el-button>
    </div>

    <!-- 空状态提示 -->
    <el-empty
      v-if="!comparisonResult && selectedObjectsList.length < 2"
      description="请至少选择2个对象进行对比"
      :image-size="200"
    />

    <!-- 对比结果区域 -->
    <div v-if="comparisonResult" class="comparison-result">
      <!-- 截图专用头部（仅在截图时显示） -->
      <div ref="screenshotHeader" class="screenshot-header" style="display: none; padding: 24px; background: #fff; text-align: center; border-bottom: 2px solid #409EFF;">
        <h1 style="margin: 0 0 12px 0; font-size: 28px; color: #303133;">{{ downloadTitle || '业绩对比分析' }}</h1>
        <p style="margin: 0; font-size: 16px; color: #909399;">生成日期：{{ formatDownloadDate() }}</p>
      </div>

      <!-- 截图容器 -->
      <div ref="screenshotContent">
        <!-- 操作按钮栏 -->
        <div style="margin-bottom: 20px; text-align: right;" class="action-buttons">
          <el-button type="success" @click="showSaveDialog = true">
            <el-icon><FolderAdd /></el-icon>
            保存此PK
          </el-button>
        </div>

      <!-- 图表区 -->
      <el-card class="chart-section">
        <template #header>
          <div class="chart-header">
            <span>收益对比图</span>
            <el-radio-group v-model="chartType" size="small">
              <el-radio-button value="return">累计收益</el-radio-button>
              <el-radio-button value="drawdown">回撤曲线</el-radio-button>
              <el-radio-button value="nav">净值曲线</el-radio-button>
            </el-radio-group>
          </div>
        </template>
        <div ref="chartRef" style="width: 100%; height: 500px;"></div>
      </el-card>

      <!-- 指标卡片区 -->
      <!-- 1. 收益类指标卡片 -->
      <el-card class="metrics-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span class="card-title">收益类指标</span>
            <div class="card-subtitle">对比区间：{{ getCompareRangeText() }}</div>
          </div>
        </template>
        <el-table
          :data="metricsTableData"
          border
          stripe
          class="performance-table"
          style="width: 100%"
        >
          <el-table-column prop="name" label="对象名称" align="left" fixed width="234" />
          <el-table-column prop="periodReturn" label="区间收益" align="center">
            <template #default="scope">
              <span v-if="scope.row.periodReturn !== null" :style="{ color: scope.row.periodReturn >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.periodReturn >= 0 ? '+' : '' }}{{ scope.row.periodReturn }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="return1m" label="近1月" align="center">
            <template #default="scope">
              <span v-if="scope.row.return1m !== null" :style="{ color: scope.row.return1m >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.return1m >= 0 ? '+' : '' }}{{ scope.row.return1m.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="return3m" label="近3月" align="center">
            <template #default="scope">
              <span v-if="scope.row.return3m !== null" :style="{ color: scope.row.return3m >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.return3m >= 0 ? '+' : '' }}{{ scope.row.return3m.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="return1y" label="近1年" align="center">
            <template #default="scope">
              <span v-if="scope.row.return1y !== null" :style="{ color: scope.row.return1y >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.return1y >= 0 ? '+' : '' }}{{ scope.row.return1y.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="return3y" label="近3年" align="center">
            <template #default="scope">
              <span v-if="scope.row.return3y !== null" :style="{ color: scope.row.return3y >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.return3y >= 0 ? '+' : '' }}{{ scope.row.return3y.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="return5y" label="近5年" align="center">
            <template #default="scope">
              <span v-if="scope.row.return5y !== null" :style="{ color: scope.row.return5y >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.return5y >= 0 ? '+' : '' }}{{ scope.row.return5y.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="ytdReturn" label="今年以来" align="center">
            <template #default="scope">
              <span v-if="scope.row.ytdReturn !== null" :style="{ color: scope.row.ytdReturn >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.ytdReturn >= 0 ? '+' : '' }}{{ scope.row.ytdReturn.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 2. 风险收益指标卡片 -->
      <el-card class="metrics-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span class="card-title">风险收益指标（成立以来）</span>
          </div>
        </template>
        <el-table
          :data="metricsTableData"
          border
          stripe
          class="performance-table"
          style="width: 100%"
        >
          <el-table-column prop="name" label="对象名称" align="left" fixed width="234">
            <template #default="scope">
              <span>{{ scope.row.name }}</span>
              <span v-if="scope.row.inceptionYears !== null && scope.row.inceptionYears !== undefined" style="color: #909399; font-size: 12px;">（{{ scope.row.inceptionYears }}年）</span>
            </template>
          </el-table-column>
          <el-table-column prop="annualReturn" label="年化收益" align="center">
            <template #default="scope">
              <span v-if="scope.row.annualReturn !== null" :style="{ color: scope.row.annualReturn >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.annualReturn >= 0 ? '+' : '' }}{{ scope.row.annualReturn.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="volatility" label="年化波动率" align="center">
            <template #default="scope">
              <span v-if="scope.row.volatility !== null">{{ scope.row.volatility.toFixed(2) }}%</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="maxDrawdown" label="最大回撤" align="center">
            <template #default="scope">
              <span v-if="scope.row.maxDrawdown !== null" style="color: #67C23A;">
                -{{ scope.row.maxDrawdown.toFixed(2) }}%
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="recoveryDays" label="最大回撤修复" align="center">
            <template #default="scope">
              <span v-if="scope.row.recoveryDays !== null && scope.row.recoveryDays !== -1">{{ scope.row.recoveryDays }}天</span>
              <span v-else-if="scope.row.recoveryDays === -1">未修复</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="latestHighDate" label="最近创新高时间" align="center">
            <template #default="scope">
              <span v-if="scope.row.latestHighDate">{{ scope.row.latestHighDate }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="sharpe" label="夏普比率" align="center">
            <template #default="scope">
              <span v-if="scope.row.sharpe !== null">{{ scope.row.sharpe.toFixed(2) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="calmar" label="卡玛比率" align="center">
            <template #default="scope">
              <span v-if="scope.row.calmar !== null">{{ scope.row.calmar.toFixed(2) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 3. 月度收益卡片 -->
      <!-- 年份选择器 -->
      <el-card v-if="availableYears.length > 0" class="metrics-card page-monthly-card" style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span class="card-title">月度收益</span>
            <el-select
              v-model="selectedYears"
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="选择年份（可多选）"
              style="width: 300px;"
              @change="handleYearChange"
              class="year-selector"
            >
              <el-option
                v-for="year in availableYears"
                :key="year"
                :label="`${year}年`"
                :value="year"
              />
            </el-select>
          </div>
        </template>

        <!-- 如果没有选择任何年份 -->
        <div v-if="selectedYears.length === 0" style="padding: 40px; text-align: center; color: #909399;">
          请选择年份查看月度收益数据
        </div>

        <!-- 展示选中年份的数据 -->
        <div v-for="(year, index) in selectedYears" :key="year">
          <div v-if="index > 0" style="margin-top: 20px; border-top: 2px solid #e4e7ed; padding-top: 20px;"></div>
          <div style="margin-bottom: 12px; font-weight: 600; font-size: 16px; color: #303133;">{{ year }}年</div>
          <el-table
            :data="getMonthlyDataByYear(year)"
            border
            stripe
            class="performance-table"
            style="width: 100%"
          >
            <el-table-column prop="name" label="对象名称" align="left" fixed width="234" />
            <el-table-column prop="year_return" label="全年" align="center" class-name="year-return-column">
              <template #default="scope">
                <span v-if="scope.row.year_return !== null" :style="{ color: scope.row.year_return >= 0 ? '#F56C6C' : '#67C23A' }">
                  {{ scope.row.year_return >= 0 ? '+' : '' }}{{ scope.row.year_return.toFixed(1) }}%
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column
              v-for="month in 12"
              :key="`m${month}`"
              :prop="`m${month}`"
              :label="`${month}月`"
              align="center"
            >
              <template #default="scope">
                <span v-if="scope.row[`m${month}`] !== null" :style="{ color: scope.row[`m${month}`] >= 0 ? '#F56C6C' : '#67C23A' }">
                  {{ scope.row[`m${month}`] >= 0 ? '+' : '' }}{{ scope.row[`m${month}`].toFixed(1) }}%
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="win_rate" label="月胜率" align="center" class-name="win-rate-column">
              <template #default="scope">
                <span v-if="scope.row.win_rate !== null">{{ scope.row.win_rate.toFixed(1) }}%</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>

      <!-- 截图专用：选中年份的月度收益 -->
      <div ref="allMonthlyData" style="display: none;">
        <div v-for="year in selectedYears" :key="year" style="margin-top: 20px;">
          <el-card class="metrics-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">月度收益 - {{ year }}年</span>
              </div>
            </template>
            <el-table
              :data="getMonthlyDataByYear(year)"
              border
              stripe
              class="performance-table"
              style="width: 100%"
            >
              <el-table-column prop="name" label="对象名称" align="left" fixed width="234" />
              <el-table-column prop="year_return" label="全年" align="center" class-name="year-return-column">
                <template #default="scope">
                  <span v-if="scope.row.year_return !== null" :style="{ color: scope.row.year_return >= 0 ? '#F56C6C' : '#67C23A' }">
                    {{ scope.row.year_return >= 0 ? '+' : '' }}{{ scope.row.year_return.toFixed(1) }}%
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column
                v-for="month in 12"
                :key="`m${month}`"
                :prop="`m${month}`"
                :label="`${month}月`"
                align="center"
              >
                <template #default="scope">
                  <span v-if="scope.row[`m${month}`] !== null" :style="{ color: scope.row[`m${month}`] >= 0 ? '#F56C6C' : '#67C23A' }">
                    {{ scope.row[`m${month}`] >= 0 ? '+' : '' }}{{ scope.row[`m${month}`].toFixed(1) }}%
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="win_rate" label="月胜率" align="center" class-name="win-rate-column">
                <template #default="scope">
                  <span v-if="scope.row.win_rate !== null">{{ scope.row.win_rate.toFixed(1) }}%</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </div>
      </div><!-- 截图容器结束 -->
    </div>

    <!-- 保存PK对话框 -->
    <el-dialog
      v-model="showSaveDialog"
      title="保存业绩PK"
      width="500px"
    >
      <el-form :model="saveForm" label-width="100px">
        <el-form-item label="PK标题" required>
          <el-input
            v-model="saveForm.title"
            placeholder="请输入PK标题，例如：2025年Q1产品对比"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSavePK" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 历史PK记录抽屉 -->
    <el-drawer
      v-model="showHistoryDrawer"
      title="历史PK记录"
      size="600px"
      direction="rtl"
    >
      <div v-loading="loadingHistory">
        <el-empty v-if="pkRecords.length === 0" description="暂无历史记录" />
        <div v-else>
          <el-card
            v-for="record in pkRecords"
            :key="record.id"
            class="history-card"
            shadow="hover"
            style="margin-bottom: 12px; cursor: pointer;"
            @click="handleLoadPK(record.id)"
          >
            <div class="history-item">
              <div class="history-title">{{ record.title }}</div>
              <div class="history-meta">
                <span>{{ record.compare_type === 'product' ? '产品对比' : '组合对比' }}</span>
                <span>{{ record.time_range }}</span>
                <span v-if="record.benchmark">基准: {{ record.benchmark }}</span>
              </div>
              <div class="history-time">{{ formatDate(record.created_at) }}</div>
              <el-button
                type="danger"
                size="small"
                text
                @click.stop="handleDeletePK(record.id)"
                style="position: absolute; top: 12px; right: 12px;"
              >
                删除
              </el-button>
            </div>
          </el-card>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'
import html2canvas from 'html2canvas'

// 对比类型（保留用于兼容，但不再显示切换按钮）
const compareType = ref('product')
const selectedObjects = ref([])
const timeRange = ref('1y')
const customTimeRange = ref([])
const customStartDate = ref(null)
const customEndDate = ref(null)
const selectedBenchmark = ref('')
const alignMode = ref('common')

// 可选对象列表 - 分别存储产品和组合
const productObjects = ref([])
const portfolioObjects = ref([])
const availableObjects = computed(() => [...portfolioObjects.value, ...productObjects.value])
const loadingProducts = ref(false)

// 图表类型
const chartType = ref('return')

// 对比进行中
const comparing = ref(false)

// 对比结果
const comparisonResult = ref(null)

// 图表实例
const chartRef = ref(null)
let chartInstance = null

// 已选对象列表（带详细信息）
const selectedObjectsList = computed(() => {
  if (!availableObjects.value.length) return []

  return selectedObjects.value.map(id => {
    return availableObjects.value.find(obj => obj.id === id)
  }).filter(Boolean)
})

// 指标表格数据
const metricsTableData = ref([])

// 月度收益数据
const selectedYears = ref([])
const availableYears = ref([])

// 保存PK相关
const showSaveDialog = ref(false)
const saving = ref(false)
const saveForm = ref({ title: '' })

// 历史PK记录相关
const showHistoryDrawer = ref(false)
const loadingHistory = ref(false)
const pkRecords = ref([])

// 下载图片相关
const screenshotHeader = ref(null)
const screenshotContent = ref(null)
const downloadTitle = ref('')
const allMonthlyData = ref(null)

// 获取指定年份的月度数据
const getMonthlyDataByYear = (year) => {
  if (!comparisonResult.value || !metricsTableData.value.length) return []

  return metricsTableData.value.map(item => {
    const monthlyData = item.monthlyReturns?.[year] || {}
    return {
      name: item.name,
      ...monthlyData
    }
  })
}

// 加载可用对象 - 同时加载产品和组合
const loadAvailableObjects = async () => {
  loadingProducts.value = true
  try {
    // 调用新的统一接口获取所有可对比对象
    const response = await axios.get('http://localhost:8003/api/performance/objects')

    const data = response.data.data || {}

    // 处理产品列表
    productObjects.value = data.products || []

    // 处理组合列表（包括回测组合和实盘组合）
    const portfolios = data.portfolios || []
    portfolioObjects.value = portfolios.map(item => ({
      id: `${item.type}_${item.id}`,  // backtest_1 或 live_2
      name: item.name,
      code: item.id.toString(),
      category: item.category,  // '回测组合' 或 '实盘组合'
      type: item.type,  // 'backtest' 或 'live'
      portfolio_id: item.id
    }))
  } catch (error) {
    console.error('加载对象列表失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loadingProducts.value = false
  }
}

// 对象选择变化
const handleObjectChange = (value) => {
  if (value.length > 10) {
    ElMessage.warning('最多只能选择10个对象')
    selectedObjects.value = value.slice(0, 10)
  }
}

// 时间区间变化
const handleTimeRangeChange = () => {
  if (timeRange.value !== 'custom') {
    customTimeRange.value = []
    customStartDate.value = null
    customEndDate.value = null
  }
}

// 自定义日期变化时同步到customTimeRange
const onCustomDateChange = () => {
  if (customStartDate.value && customEndDate.value) {
    customTimeRange.value = [customStartDate.value, customEndDate.value]
  } else {
    customTimeRange.value = []
  }
}

// 移除对象
const handleRemoveObject = (id) => {
  selectedObjects.value = selectedObjects.value.filter(objId => objId !== id)
}

// 执行对比
const handleCompare = async () => {
  if (selectedObjectsList.value.length < 2) {
    ElMessage.warning('请至少选择2个对象进行对比')
    return
  }

  comparing.value = true

  try {
    // 准备对比对象数据
    const compareObjects = selectedObjectsList.value.map(obj => {
      // 对于组合类型（backtest 或 live），提取真实的 portfolio_id
      if (obj.type === 'backtest' || obj.type === 'live') {
        // 从 id 中提取数字部分（去掉 backtest_ 或 live_ 前缀）
        const portfolioId = obj.id.replace(`${obj.type}_`, '')
        return {
          id: portfolioId,
          type: obj.type  // 'backtest' 或 'live'
        }
      } else if (obj.type === 'portfolio') {
        // 兼容旧的 portfolio 类型
        const portfolioId = obj.id.replace('portfolio_', '')
        return {
          id: portfolioId,
          type: 'portfolio'
        }
      } else {
        // 产品类型直接使用 id
        return {
          id: obj.id,
          type: obj.type
        }
      }
    })

    console.log('发送对比请求:', compareObjects)

    // 调用后端API进行对比分析
    const response = await axios.post('http://localhost:8003/api/performance/compare', {
      objects: compareObjects,
      time_range: timeRange.value,
      custom_range: customTimeRange.value.length ? customTimeRange.value : null,
      benchmark: selectedBenchmark.value || null,
      align_mode: alignMode.value
    })

    comparisonResult.value = response.data
    metricsTableData.value = response.data.metrics

    // 提取所有可用的年份（确保唯一性和排序）
    const yearsSet = new Set()
    response.data.metrics.forEach(item => {
      if (item.monthlyReturns) {
        Object.keys(item.monthlyReturns).forEach(year => {
          yearsSet.add(parseInt(year))
        })
      }
    })
    // 按从新到旧排序（2025 → 2024）
    availableYears.value = Array.from(yearsSet).sort((a, b) => b - a)

    // 默认选择最新的2个年份（确保唯一性）
    if (availableYears.value.length > 0) {
      const defaultYears = availableYears.value.slice(0, Math.min(2, availableYears.value.length))
      selectedYears.value = [...new Set(defaultYears)]
    }

    // 等待DOM更新后绘制图表
    await nextTick()
    drawChart()

    ElMessage.success('对比分析完成')
  } catch (error) {
    console.error('对比分析失败:', error)
    ElMessage.error(error.response?.data?.detail || '对比分析失败，请重试')
  } finally {
    comparing.value = false
  }
}

// 获取对比区间文本
const getCompareRangeText = () => {
  if (!comparisonResult.value || !comparisonResult.value.dates) return '-'

  const dates = comparisonResult.value.dates
  if (dates.length === 0) return '-'

  const startDate = dates[0]
  const endDate = dates[dates.length - 1]

  return `${startDate} 至 ${endDate}`
}

// 格式化下载日期
const formatDownloadDate = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const day = now.getDate()
  return `${year}年${month}月${day}日`
}

// 下载为图片
const downloadAsImage = async () => {
  if (!comparisonResult.value) return

  try {
    ElMessage.info('正在生成图片，请稍候...')

    // 设置下载标题
    if (!downloadTitle.value) {
      const objectNames = metricsTableData.value.map(item => item.name).join(' vs ')
      downloadTitle.value = objectNames || '业绩对比分析'
    }

    // 1. 获取ECharts图表的图片
    let chartImageUrl = null
    if (chartInstance) {
      chartImageUrl = chartInstance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
      })
    }

    // 2. 显示截图头部
    if (screenshotHeader.value) {
      screenshotHeader.value.style.display = 'block'
    }

    // 3. 显示所有年份的月度收益数据
    if (allMonthlyData.value) {
      allMonthlyData.value.style.display = 'block'
    }

    await nextTick()

    // 4. 获取网页端父容器的实际渲染宽度
    const actualContainerWidth = screenshotContent.value.offsetWidth
    console.log('网页端父容器实际宽度:', actualContainerWidth)

    // 5. 创建临时容器（继承网页端父容器宽度）
    const tempContainer = document.createElement('div')
    tempContainer.style.background = '#f5f7fa'
    tempContainer.style.padding = '0'
    tempContainer.style.position = 'absolute'
    tempContainer.style.left = '-9999px'
    tempContainer.style.top = '0'
    tempContainer.style.width = `${actualContainerWidth}px`
    tempContainer.style.boxSizing = 'border-box'
    document.body.appendChild(tempContainer)

    // 6. 克隆头部
    const headerClone = screenshotHeader.value.cloneNode(true)
    headerClone.style.display = 'block'
    headerClone.style.width = '100%'
    headerClone.style.boxSizing = 'border-box'
    tempContainer.appendChild(headerClone)

    // 7. 克隆内容
    const contentClone = screenshotContent.value.cloneNode(true)
    contentClone.style.width = '100%'
    contentClone.style.boxSizing = 'border-box'
    tempContainer.appendChild(contentClone)

    // 8. 替换图表为图片
    if (chartImageUrl) {
      // 查找图表容器 - 通过ref属性或者父元素有chart-section类
      const chartSections = tempContainer.querySelectorAll('.chart-section')
      for (const section of chartSections) {
        const chartDiv = section.querySelector('[style*="height: 500px"]')
        if (chartDiv) {
          chartDiv.innerHTML = ''
          const img = document.createElement('img')
          img.src = chartImageUrl
          img.style.width = '100%'
          img.style.height = '500px'
          img.style.objectFit = 'contain'
          img.style.display = 'block'
          chartDiv.appendChild(img)
        }
      }
    }

    // 9. 隐藏操作按钮和年份选择器
    const actionButtons = tempContainer.querySelectorAll('.action-buttons')
    actionButtons.forEach(btn => {
      btn.style.display = 'none'
    })

    const yearSelectors = tempContainer.querySelectorAll('.year-selector')
    yearSelectors.forEach(selector => {
      selector.style.display = 'none'
    })

    // 隐藏页面显示的月度收益卡片（避免重复）
    const pageMonthlyCards = tempContainer.querySelectorAll('.page-monthly-card')
    pageMonthlyCards.forEach(card => {
      card.style.display = 'none'
    })

    // 10. 强制所有元素100%撑满父容器，禁止重新计算布局
    // 禁止auto/shrink/fit-content等自适应行为
    const allCards = tempContainer.querySelectorAll('.el-card')
    allCards.forEach(card => {
      card.style.width = '100%'
      card.style.maxWidth = 'none'
      card.style.minWidth = '0'
      card.style.boxSizing = 'border-box'
      card.style.margin = '0'
      card.style.flex = 'none'
    })

    const allTables = tempContainer.querySelectorAll('.el-table')
    allTables.forEach(table => {
      table.style.width = '100%'
      table.style.maxWidth = 'none'
      table.style.minWidth = '0'
      table.style.boxSizing = 'border-box'
      table.style.tableLayout = 'fixed'  // 强制fixed布局，禁止html2canvas重算列宽
      // 明确设置字体和行高，避免clone DOM后样式继承问题
      table.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
      table.style.fontSize = '16px'  // 导出图片时字体设置为16px
      table.style.lineHeight = '1.5'
    })

    const allTableWrappers = tempContainer.querySelectorAll('.el-table__wrapper')
    allTableWrappers.forEach(wrapper => {
      wrapper.style.width = '100%'
      wrapper.style.maxWidth = 'none'
      wrapper.style.overflow = 'visible'
    })

    // 强制处理所有表格的body和header，确保100%宽度和统一的盒模型
    const allTableBodies = tempContainer.querySelectorAll('.el-table__body')
    allTableBodies.forEach(body => {
      body.style.width = '100%'
    })

    const allTableHeaders = tempContainer.querySelectorAll('.el-table__header')
    allTableHeaders.forEach(header => {
      header.style.width = '100%'
    })

    // 强制thead和tbody使用统一的display，避免html2canvas盒模型不一致
    const allTheads = tempContainer.querySelectorAll('thead')
    allTheads.forEach(thead => {
      thead.style.display = 'table-header-group'
      thead.style.width = '100%'
    })

    const allTbodies = tempContainer.querySelectorAll('tbody')
    allTbodies.forEach(tbody => {
      tbody.style.display = 'table-row-group'
      tbody.style.width = '100%'
    })

    // 移除所有固定列的fixed-column类，避免宽度限制
    const fixedColumns = tempContainer.querySelectorAll('.el-table-fixed-column, .el-table__fixed, .el-table__fixed-right')
    fixedColumns.forEach(col => {
      col.classList.remove('el-table-fixed-column')
      col.classList.remove('el-table__fixed')
      col.classList.remove('el-table__fixed-right')
      col.style.position = 'static'
    })

    // 强制处理所有表格的列宽，使用明确的百分比/像素值，避免html2canvas重算
    const allTableColGroups = tempContainer.querySelectorAll('colgroup')
    allTableColGroups.forEach(colgroup => {
      const cols = colgroup.querySelectorAll('col')
      if (cols.length > 0) {
        // 计算总列数和宽度分配策略
        const totalCols = cols.length
        // 对象名称列: 20%, 其他列均分剩余80%
        const firstColWidth = '20%'
        const otherColWidth = `${80 / (totalCols - 1)}%`

        cols.forEach((col, index) => {
          col.removeAttribute('width')
          if (index === 0) {
            // 第一列（对象名称）：明确设置20%宽度
            col.style.width = firstColWidth
            col.style.minWidth = '0'
            col.style.maxWidth = 'none'
          } else {
            // 其他列：均分剩余80%
            col.style.width = otherColWidth
            col.style.minWidth = '0'
            col.style.maxWidth = 'none'
          }
        })
      }
    })

    // 强制所有表格行使用table-row display
    const allTableRows = tempContainer.querySelectorAll('tr')
    allTableRows.forEach(row => {
      row.style.display = 'table-row'
      row.style.width = '100%'
    })

    // 针对性处理表格单元格：强制不换行、统一字体行高
    const allTableCells = tempContainer.querySelectorAll('.el-table th, .el-table td')
    allTableCells.forEach((cell) => {
      // 判断是否为第一列（对象名称列）
      const cellIndex = Array.from(cell.parentElement.children).indexOf(cell)

      // 统一设置：禁止换行、明确字体和行高
      cell.style.whiteSpace = 'nowrap'
      cell.style.overflow = 'hidden'
      cell.style.textOverflow = 'ellipsis'
      cell.style.boxSizing = 'border-box'
      cell.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
      cell.style.fontSize = '16px'  // 导出图片时字体设置为16px
      cell.style.lineHeight = '1.5'
      cell.style.verticalAlign = 'middle'
      cell.style.display = 'table-cell'  // 强制使用table-cell display

      if (cellIndex === 0) {
        // 对象名称列：相对更多的padding
        cell.style.padding = '12px 8px'
      } else {
        // 数值列：紧凑padding
        cell.style.padding = '12px 4px'
        cell.style.textAlign = 'center'
      }
    })

    // 强制所有table标签100%宽度和fixed布局（Element UI内部可能生成多个table标签）
    const allInnerTables = tempContainer.querySelectorAll('table')
    allInnerTables.forEach(table => {
      table.style.width = '100%'
      table.style.tableLayout = 'fixed'  // 强制fixed布局，与外层.el-table一致
      table.style.minWidth = '100%'
      table.style.maxWidth = '100%'
      table.style.borderCollapse = 'collapse'  // 确保边框合并
      table.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
      table.style.fontSize = '16px'  // 导出图片时字体设置为16px
      table.style.lineHeight = '1.5'
    })

    // 强制所有卡片主体100%宽度
    const allCardBodies = tempContainer.querySelectorAll('.el-card__body')
    allCardBodies.forEach(body => {
      body.style.width = '100%'
      body.style.boxSizing = 'border-box'
    })

    // 显示截图专用的月度收益数据（它在contentClone中被克隆过来了）
    // 找到克隆内容中的隐藏月度收益数据并显示
    const clonedMonthlyData = contentClone.querySelector('[style*="display: none"]')
    if (clonedMonthlyData) {
      clonedMonthlyData.style.display = 'block'
    }

    // 等待DOM更新
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 800))

    // 验证临时容器最终宽度（调试用）
    console.log('=================== 导出调试信息 ===================')
    console.log('网页端父容器实际宽度:', actualContainerWidth)
    console.log('临时容器最终宽度:', tempContainer.offsetWidth)
    console.log('临时容器样式宽度:', tempContainer.style.width)

    // 调试表格宽度和列宽分配
    const debugTables = tempContainer.querySelectorAll('table')
    debugTables.forEach((table, index) => {
      console.log(`\n表格${index + 1} 信息:`)
      console.log('  整体宽度:', table.offsetWidth, '样式:', table.style.width)
      console.log('  布局模式:', table.style.tableLayout)

      // 调试colgroup列宽设置
      const colgroup = table.querySelector('colgroup')
      if (colgroup) {
        const cols = colgroup.querySelectorAll('col')
        console.log('  列数:', cols.length)
        cols.forEach((col, i) => {
          console.log(`    列${i + 1} width样式:`, col.style.width)
        })
      }

      // 调试表头行单元格宽度
      const theadRow = table.querySelector('thead tr')
      if (theadRow) {
        const thCells = theadRow.querySelectorAll('th')
        const thWidths = Array.from(thCells).map((cell, i) => ({
          列: i + 1,
          实际宽度: cell.offsetWidth,
          样式宽度: cell.style.width,
          文本: cell.textContent.trim().substring(0, 15)
        }))
        console.log('  表头单元格宽度:', thWidths)
      }

      // 调试第一个内容行单元格宽度
      const tbodyRow = table.querySelector('tbody tr')
      if (tbodyRow) {
        const tdCells = tbodyRow.querySelectorAll('td')
        const tdWidths = Array.from(tdCells).map((cell, i) => ({
          列: i + 1,
          实际宽度: cell.offsetWidth,
          样式宽度: cell.style.width,
          文本: cell.textContent.trim().substring(0, 15)
        }))
        console.log('  内容单元格宽度:', tdWidths)
      }
    })
    console.log('==================================================\n')

    // 10. 使用html2canvas截图（使用网页端父容器实际宽度）
    const canvas = await html2canvas(tempContainer, {
      backgroundColor: '#f5f7fa',
      scale: 2,
      useCORS: true,
      logging: false,
      width: actualContainerWidth,
      windowWidth: actualContainerWidth
    })

    // 11. 移除临时容器
    document.body.removeChild(tempContainer)

    // 12. 隐藏截图头部和所有年份数据
    if (screenshotHeader.value) {
      screenshotHeader.value.style.display = 'none'
    }
    if (allMonthlyData.value) {
      allMonthlyData.value.style.display = 'none'
    }

    // 13. 转换为图片并下载
    const link = document.createElement('a')
    const timestamp = new Date().getTime()
    link.download = `业绩对比_${timestamp}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()

    ElMessage.success('图片下载成功')
  } catch (error) {
    console.error('下载图片失败:', error)
    ElMessage.error('下载图片失败，请稍后重试')

    // 确保隐藏截图头部和所有年份数据
    if (screenshotHeader.value) {
      screenshotHeader.value.style.display = 'none'
    }
    if (allMonthlyData.value) {
      allMonthlyData.value.style.display = 'none'
    }
  }
}

// 年份变化处理
const handleYearChange = () => {
  // 年份变化时，月度表格数据会自动更新
}

// 绘制图表
const drawChart = () => {
  if (!chartRef.value || !comparisonResult.value) return

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#00D084', '#F78989', '#58D5FF', '#C77EB5', '#4ECDC4']

  // 根据图表类型选择对应的数据字段
  let dataField, chartTitle, yAxisFormatter

  if (chartType.value === 'return') {
    dataField = 'return_data'
    chartTitle = '累计收益率对比'
    yAxisFormatter = '{value}%'
  } else if (chartType.value === 'drawdown') {
    dataField = 'drawdown_data'
    chartTitle = '回撤曲线对比'
    yAxisFormatter = '{value}%'
  } else { // nav
    dataField = 'nav_data'
    chartTitle = '净值曲线对比'
    yAxisFormatter = '{value}'
  }

  const series = comparisonResult.value.chart_data.map((item, index) => ({
    name: item.name,
    type: 'line',
    data: item[dataField],
    smooth: true,
    symbol: 'none',
    connectNulls: true,  // 连接空值点
    lineStyle: {
      width: item.is_benchmark ? 2 : 3,
      type: item.is_benchmark ? 'dashed' : 'solid'
    },
    itemStyle: {
      color: colors[index % colors.length]
    }
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      valueFormatter: (value) => {
        // 处理null/undefined值
        if (value === null || value === undefined) {
          return '-'
        }
        if (chartType.value === 'nav') {
          return value.toFixed(4)
        } else {
          return value.toFixed(2) + '%'
        }
      }
    },
    legend: {
      data: comparisonResult.value.chart_data.map(item => item.name),
      bottom: 10,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      top: '3%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: comparisonResult.value.dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: yAxisFormatter
      }
    },
    series: series
  }

  chartInstance.setOption(option, true)  // 使用notMerge选项
}

// 监听图表类型变化
watch(chartType, () => {
  if (comparisonResult.value && chartInstance) {
    nextTick(() => {
      drawChart()
    })
  }
})

// 页面加载时获取产品列表
onMounted(() => {
  loadAvailableObjects()

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})

// 窗口大小调整
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 保存PK记录
const handleSavePK = async () => {
  if (!saveForm.value.title || !saveForm.value.title.trim()) {
    ElMessage.warning('请输入PK标题')
    return
  }

  saving.value = true
  try {
    await axios.post('http://localhost:8003/api/performance/pk/save', {
      title: saveForm.value.title.trim(),
      compare_type: compareType.value,
      objects: selectedObjectsList.value.map(obj => ({
        id: obj.id,
        type: obj.type
      })),
      time_range: timeRange.value,
      custom_range: customTimeRange.value.length ? customTimeRange.value : null,
      benchmark: selectedBenchmark.value,
      align_mode: alignMode.value
    })

    ElMessage.success('PK记录保存成功')
    showSaveDialog.value = false
    saveForm.value.title = ''
  } catch (error) {
    console.error('保存PK记录失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存PK记录失败')
  } finally {
    saving.value = false
  }
}

// 加载历史PK记录列表
const loadPKRecords = async () => {
  loadingHistory.value = true
  try {
    const response = await axios.get('http://localhost:8003/api/performance/pk/list', {
      params: { page: 1, page_size: 50 }
    })
    pkRecords.value = response.data.data || []
  } catch (error) {
    console.error('加载历史记录失败:', error)
    ElMessage.error('加载历史记录失败')
  } finally {
    loadingHistory.value = false
  }
}

// 加载指定的PK记录
const handleLoadPK = async (pkId) => {
  try {
    const response = await axios.get(`http://localhost:8003/api/performance/pk/${pkId}`)
    const record = response.data.data

    // 恢复对比配置
    compareType.value = record.compare_type
    timeRange.value = record.time_range
    customTimeRange.value = record.custom_range || []
    // 恢复自定义日期的独立字段
    if (record.custom_range && record.custom_range.length === 2) {
      customStartDate.value = record.custom_range[0]
      customEndDate.value = record.custom_range[1]
    } else {
      customStartDate.value = null
      customEndDate.value = null
    }
    selectedBenchmark.value = record.benchmark
    alignMode.value = record.align_mode || 'common'

    // 加载对应的对象列表
    await loadAvailableObjects()

    // 恢复选中的对象
    selectedObjects.value = record.objects.map(obj => obj.id)

    // 关闭抽屉
    showHistoryDrawer.value = false

    // 自动执行对比
    ElMessage.success('已加载历史PK配置')
    await nextTick()
    handleCompare()
  } catch (error) {
    console.error('加载PK记录失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载PK记录失败')
  }
}

// 删除PK记录
const handleDeletePK = async (pkId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条PK记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await axios.delete(`http://localhost:8003/api/performance/pk/${pkId}`)
    ElMessage.success('删除成功')

    // 重新加载列表
    loadPKRecords()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除PK记录失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除PK记录失败')
    }
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 监听抽屉打开，加载历史记录
watch(showHistoryDrawer, (newVal) => {
  if (newVal) {
    loadPKRecords()
  }
})
</script>

<style scoped>
.performance-pk {
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.page-header p {
  color: #909399;
  font-size: 14px;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.type-hint {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}

.selected-objects-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.objects-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.object-tag {
  padding: 12px 16px;
  height: auto;
}

.tag-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tag-name {
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.tag-meta {
  font-size: 12px;
  opacity: 0.8;
}

.action-section {
  text-align: center;
  margin: 32px 0;
}

.chart-header,
.metrics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-subtitle {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.metrics-card {
  margin-bottom: 20px;
}

.performance-table {
  font-size: 13px;
}

.performance-table :deep(.el-table__header th) {
  background-color: #f5f7fa;
  font-weight: 600;
  text-align: center;
}

.performance-table :deep(.el-table__body td) {
  text-align: center;
}

.performance-table :deep(.el-table__body td:first-child) {
  text-align: left;
  font-weight: 500;
}

/* 全年列背景色 - 表头和所有内容行 */
.performance-table :deep(.el-table__header .year-return-column),
.performance-table :deep(.el-table__body .year-return-column) {
  background-color: #fef9e7 !important;
}

/* 月胜率列字体颜色 - 蓝色 */
.performance-table :deep(.el-table__body .win-rate-column) {
  color: #409EFF !important;
}

.metrics-table {
  font-size: 13px;
}

.metrics-table :deep(.el-table__header th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

/* 历史记录样式 */
.history-card {
  position: relative;
}

.history-item {
  padding: 12px 0;
}

.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.history-meta {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.history-meta span {
  margin-right: 12px;
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
}

.history-time {
  font-size: 12px;
  color: #909399;
}

/* 响应式 */
@media (max-width: 768px) {
  .el-col {
    margin-bottom: 16px;
  }
}
</style>
