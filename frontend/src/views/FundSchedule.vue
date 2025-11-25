<template>
  <div class="fund-schedule-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>产品档期管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加档期规则
          </el-button>
        </div>
      </template>

      <el-form :inline="true">
        <el-form-item label="选择月份">
          <el-date-picker
            v-model="selectedMonth"
            type="month"
            placeholder="选择月份"
            format="YYYY年MM月"
            value-format="YYYY-MM"
            @change="loadCalendarData"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 档期规则列表 -->
    <el-card class="rules-card">
      <template #header>
        <span>档期规则列表</span>
      </template>

      <el-table
        v-loading="loading"
        :data="scheduleRules"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column prop="fund_code" label="基金代码" width="120" />
        <el-table-column prop="fund_name" label="基金名称" width="180" />
        <el-table-column prop="main_strategy" label="大类策略" width="100" />
        <el-table-column prop="sub_strategy" label="细分策略" width="100" />
        <el-table-column prop="subscription_rule" label="申购规则" min-width="180" />
        <el-table-column prop="redemption_rule" label="赎回规则" min-width="180" />
        <el-table-column prop="lock_period" label="锁定期" width="120" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="calculateDates(scope.row)"
            >
              计算日期
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="editRule(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteRule(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑规则对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="ruleForm" label-width="100px">
        <el-form-item label="基金代码" required>
          <el-select
            v-model="ruleForm.fund_code"
            filterable
            remote
            reserve-keyword
            placeholder="输入基金代码或名称搜索"
            :remote-method="searchFunds"
            :loading="fundSearchLoading"
            style="width: 100%"
          >
            <el-option
              v-for="fund in fundList"
              :key="fund.fund_code"
              :label="`${fund.fund_code} - ${fund.fund_name}`"
              :value="fund.fund_code"
            />
          </el-select>
          <div class="search-hint">
            例如：输入"盛景"或"磐泽"搜索相关产品
          </div>
        </el-form-item>

        <el-form-item label="申购规则">
          <el-input
            v-model="ruleForm.subscription_rule"
            type="textarea"
            :rows="3"
            placeholder="例如：每月15日和每月最后一个交易日"
          />
          <div class="rule-hint">
            支持：每月X日、每月最后一个交易日、每月最后一天
          </div>
        </el-form-item>

        <el-form-item label="赎回规则">
          <el-input
            v-model="ruleForm.redemption_rule"
            type="textarea"
            :rows="3"
            placeholder="例如：每月最后一个交易日"
          />
        </el-form-item>

        <el-form-item label="锁定期">
          <el-input
            v-model="ruleForm.lock_period"
            placeholder="例如：3个月、6个月、1年"
          />
          <div class="rule-hint">
            描述投资锁定期限制，如：3个月、6个月、1年等
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 日期计算结果对话框 -->
    <el-dialog
      v-model="datesDialogVisible"
      title="档期日期计算结果"
      width="700px"
    >
      <div v-if="calculatedDates">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="基金代码">
            {{ calculatedDates.fund_code }}
          </el-descriptions-item>
          <el-descriptions-item label="计算月份">
            {{ calculatedDates.year }}年{{ calculatedDates.month }}月
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">申购开放日期</el-divider>
        <el-tag
          v-for="(date, index) in calculatedDates.subscription_dates"
          :key="'sub-' + index"
          type="success"
          size="large"
          style="margin: 5px"
        >
          {{ date.display }} ({{ date.rule_type }})
        </el-tag>
        <el-empty v-if="!calculatedDates.subscription_dates.length" description="无申购开放日" />

        <el-divider content-position="left">赎回开放日期</el-divider>
        <el-tag
          v-for="(date, index) in calculatedDates.redemption_dates"
          :key="'red-' + index"
          type="warning"
          size="large"
          style="margin: 5px"
        >
          {{ date.display }} ({{ date.rule_type }})
        </el-tag>
        <el-empty v-if="!calculatedDates.redemption_dates.length" description="无赎回开放日" />
      </div>

      <template #footer>
        <el-button @click="datesDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 月历视图 -->
    <el-card v-if="calendarData" class="calendar-card">
      <template #header>
        <div class="card-header">
          <span>{{ selectedMonthDisplay }} 产品档期月历</span>
          <el-button-group>
            <el-button @click="prevMonth">
              <el-icon><ArrowLeft /></el-icon>
              上月
            </el-button>
            <el-button @click="nextMonth">
              下月
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </el-button-group>
        </div>
      </template>

      <div class="calendar-grid">
        <div class="calendar-header">
          <div class="calendar-day-header">周日</div>
          <div class="calendar-day-header">周一</div>
          <div class="calendar-day-header">周二</div>
          <div class="calendar-day-header">周三</div>
          <div class="calendar-day-header">周四</div>
          <div class="calendar-day-header">周五</div>
          <div class="calendar-day-header">周六</div>
        </div>
        <div class="calendar-body">
          <div
            v-for="(day, index) in calendarDays"
            :key="index"
            :class="['calendar-day', { 'other-month': !day.isCurrentMonth }]"
          >
            <div class="day-number">{{ day.day }}</div>
            <div v-if="day.schedules" class="day-schedules">
              <el-popover
                v-if="day.schedules.subscriptions.length > 0"
                placement="top"
                :width="300"
                trigger="hover"
              >
                <template #reference>
                  <el-tag type="success" size="small" class="schedule-tag">
                    申购 ({{ day.schedules.subscriptions.length }})
                  </el-tag>
                </template>
                <div v-for="fund in day.schedules.subscriptions" :key="fund.fund_code">
                  <strong>{{ fund.fund_code }}</strong> - {{ fund.fund_name }}<br>
                  策略：{{ fund.main_strategy }} / {{ fund.sub_strategy }}
                </div>
              </el-popover>

              <el-popover
                v-if="day.schedules.redemptions.length > 0"
                placement="top"
                :width="300"
                trigger="hover"
              >
                <template #reference>
                  <el-tag type="warning" size="small" class="schedule-tag">
                    赎回 ({{ day.schedules.redemptions.length }})
                  </el-tag>
                </template>
                <div v-for="fund in day.schedules.redemptions" :key="fund.fund_code">
                  <strong>{{ fund.fund_code }}</strong> - {{ fund.fund_name }}<br>
                  策略：{{ fund.main_strategy }} / {{ fund.sub_strategy }}
                </div>
              </el-popover>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const loading = ref(false)
const scheduleRules = ref([])
const fundList = ref([])
const fundSearchLoading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('添加档期规则')
const datesDialogVisible = ref(false)
const calculatedDates = ref(null)
const selectedMonth = ref(null)
const calendarData = ref(null)

const ruleForm = ref({
  fund_code: '',
  subscription_rule: '',
  redemption_rule: '',
  lock_period: ''
})

// 初始化当前月份
const now = new Date()
selectedMonth.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

const selectedMonthDisplay = computed(() => {
  if (!selectedMonth.value) return ''
  const [year, month] = selectedMonth.value.split('-')
  return `${year}年${month}月`
})

onMounted(() => {
  loadScheduleRules()
  loadCalendarData()
})

async function searchFunds(query) {
  if (!query || query.trim().length < 1) {
    fundList.value = []
    return
  }

  fundSearchLoading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/nav/funds`, {
      params: { search: query }
    })
    if (response.data.success) {
      fundList.value = response.data.data.funds || []
    }
  } catch (error) {
    console.error('搜索基金失败:', error)
    ElMessage.error('搜索基金失败')
  } finally {
    fundSearchLoading.value = false
  }
}

async function loadScheduleRules() {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/fund-schedules/rules`)
    if (response.data.success) {
      scheduleRules.value = response.data.data
    }
  } catch (error) {
    ElMessage.error('加载档期规则失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function showAddDialog() {
  dialogTitle.value = '添加档期规则'
  ruleForm.value = {
    fund_code: '',
    subscription_rule: '',
    redemption_rule: '',
    lock_period: ''
  }
  dialogVisible.value = true
}

function editRule(row) {
  dialogTitle.value = '编辑档期规则'
  ruleForm.value = {
    fund_code: row.fund_code,
    subscription_rule: row.subscription_rule || '',
    redemption_rule: row.redemption_rule || '',
    lock_period: row.lock_period || ''
  }
  dialogVisible.value = true
}

async function saveRule() {
  if (!ruleForm.value.fund_code) {
    ElMessage.warning('请选择基金')
    return
  }

  try {
    const response = await axios.post(`${API_BASE}/api/fund-schedules/rules`, ruleForm.value)
    if (response.data.success) {
      ElMessage.success(response.data.message)
      dialogVisible.value = false
      loadScheduleRules()
      loadCalendarData()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

function resetForm() {
  ruleForm.value = {
    fund_code: '',
    subscription_rule: '',
    redemption_rule: '',
    lock_period: ''
  }
}

async function deleteRule(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除基金 ${row.fund_code} 的档期规则吗？`,
      '确认删除',
      {
        type: 'warning'
      }
    )

    const response = await axios.delete(`${API_BASE}/api/fund-schedules/rules/${row.fund_code}`)
    if (response.data.success) {
      ElMessage.success('删除成功')
      loadScheduleRules()
      loadCalendarData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function calculateDates(row) {
  if (!selectedMonth.value) {
    ElMessage.warning('请先选择月份')
    return
  }

  const [year, month] = selectedMonth.value.split('-')

  try {
    const response = await axios.post(`${API_BASE}/api/fund-schedules/calculate`, {
      fund_code: row.fund_code,
      year: parseInt(year),
      month: parseInt(month)
    })

    if (response.data.success) {
      calculatedDates.value = {
        ...response.data.data,
        fund_code: row.fund_code
      }
      datesDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('计算日期失败')
    console.error(error)
  }
}

async function loadCalendarData() {
  if (!selectedMonth.value || scheduleRules.value.length === 0) {
    calendarData.value = null
    return
  }

  const [year, month] = selectedMonth.value.split('-')
  const fundCodes = scheduleRules.value.map(r => r.fund_code)

  try {
    const response = await axios.post(`${API_BASE}/api/fund-schedules/calendar`, {
      fund_codes: fundCodes,
      year: parseInt(year),
      month: parseInt(month)
    })

    if (response.data.success) {
      calendarData.value = response.data.data
    }
  } catch (error) {
    console.error('加载月历数据失败:', error)
  }
}

const calendarDays = computed(() => {
  if (!selectedMonth.value) return []

  const [year, month] = selectedMonth.value.split('-')
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const daysInMonth = lastDay.getDate()
  const firstDayWeek = firstDay.getDay()

  const days = []

  // 上个月的日期填充
  const prevMonthDays = new Date(year, month - 1, 0).getDate()
  for (let i = firstDayWeek - 1; i >= 0; i--) {
    days.push({
      day: prevMonthDays - i,
      isCurrentMonth: false
    })
  }

  // 当前月的日期
  for (let i = 1; i <= daysInMonth; i++) {
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    days.push({
      day: i,
      isCurrentMonth: true,
      date: dateStr,
      schedules: calendarData.value?.calendar_days?.[dateStr] || null
    })
  }

  // 下个月的日期填充
  const remainingDays = 42 - days.length
  for (let i = 1; i <= remainingDays; i++) {
    days.push({
      day: i,
      isCurrentMonth: false
    })
  }

  return days
})

function prevMonth() {
  const [year, month] = selectedMonth.value.split('-')
  const date = new Date(year, month - 2, 1)
  selectedMonth.value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
  loadCalendarData()
}

function nextMonth() {
  const [year, month] = selectedMonth.value.split('-')
  const date = new Date(year, month, 1)
  selectedMonth.value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
  loadCalendarData()
}
</script>

<style scoped>
.fund-schedule-container {
  padding: 20px;
}

.header-card,
.rules-card,
.calendar-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rule-hint,
.search-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.calendar-grid {
  width: 100%;
}

.calendar-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background-color: #f0f0f0;
  border: 1px solid #e0e0e0;
}

.calendar-day-header {
  background-color: #409EFF;
  color: white;
  text-align: center;
  padding: 10px;
  font-weight: bold;
}

.calendar-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background-color: #f0f0f0;
  border: 1px solid #e0e0e0;
  border-top: none;
}

.calendar-day {
  background-color: white;
  min-height: 100px;
  padding: 8px;
  position: relative;
}

.calendar-day.other-month {
  background-color: #fafafa;
  color: #c0c0c0;
}

.day-number {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 5px;
}

.day-schedules {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.schedule-tag {
  font-size: 11px;
  padding: 2px 6px;
  cursor: pointer;
}
</style>
