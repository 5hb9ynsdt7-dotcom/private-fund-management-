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
        <div class="card-header">
          <span>档期规则列表</span>
          <div v-if="selectedRules.length > 0" class="batch-actions">
            <span class="selected-count">已选择 {{ selectedRules.length }} 项</span>
            <el-button
              type="success"
              size="small"
              @click="showSelectedInCalendar"
            >
              显示在日历
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="batchDeleteRules"
            >
              批量删除
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="scheduleRules"
        border
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="fund_code" label="基金代码" width="120" />
        <el-table-column prop="fund_name" label="基金名称" width="180" />
        <el-table-column prop="main_strategy" label="大类策略" width="150">
          <template #default="{ row }">
            <el-select
              v-model="row.main_strategy"
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
        <el-table-column prop="sub_strategy" label="细分策略" width="150">
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
        <el-table-column prop="subscription_rule" label="申购规则" min-width="180" />
        <el-table-column prop="redemption_rule" label="赎回规则" min-width="180" />
        <el-table-column prop="lock_period" label="锁定期" width="120" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <div class="action-buttons">
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
            </div>
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
        <el-form-item label="录入方式">
          <el-radio-group v-model="inputMode">
            <el-radio value="search">搜索现有产品</el-radio>
            <el-radio value="manual">手动新增产品</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="inputMode === 'search'" label="基金代码" required>
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

        <template v-if="inputMode === 'manual'">
          <el-form-item label="基金代码" required>
            <el-input
              v-model="ruleForm.fund_code"
              placeholder="例如：L01234"
            />
          </el-form-item>
          <el-form-item label="基金名称" required>
            <el-input
              v-model="ruleForm.fund_name"
              placeholder="例如：盛景私募证券投资基金"
            />
          </el-form-item>
        </template>

        <el-form-item label="申购规则">
          <el-input
            v-model="ruleForm.subscription_rule"
            type="textarea"
            :rows="3"
            placeholder="例如：每月15日和每月最后一个交易日"
          />
          <div class="rule-hint">
            支持：每月X日/号、每周X、第X个周X、每月最后一个交易日、每月最后一天<br>
            节假日处理：顺延、提前、不开放
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

    <!-- 申购日历 -->
    <el-card v-if="calendarData" class="calendar-card">
      <template #header>
        <div class="card-header">
          <span>{{ selectedMonthDisplay }} 申购开放日历</span>
          <div class="calendar-controls">
            <el-button
              v-if="selectedRules.length > 0"
              type="info"
              size="small"
              @click="loadCalendarData(false)"
            >
              显示全部
            </el-button>
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
            :key="'sub-' + index"
            :class="['calendar-day', { 'other-month': !day.isCurrentMonth }]"
          >
            <div class="day-number">{{ day.day }}</div>
            <div v-if="day.schedules?.subscriptions?.length > 0" class="day-schedules">
              <el-popover
                v-for="fund in day.schedules.subscriptions"
                :key="fund.fund_code"
                placement="top"
                :width="300"
                trigger="hover"
              >
                <template #reference>
                  <div class="fund-short-name">
                    {{ getFundShortName(fund.fund_name) }}
                  </div>
                </template>
                <div>
                  <strong>{{ fund.fund_code }}</strong><br>
                  {{ fund.fund_name }}<br>
                  策略：{{ fund.main_strategy }} / {{ fund.sub_strategy }}
                </div>
              </el-popover>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 赎回日历 -->
    <el-card v-if="calendarData" class="calendar-card">
      <template #header>
        <div class="card-header">
          <span>{{ selectedMonthDisplay }} 赎回开放日历</span>
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
            :key="'red-' + index"
            :class="['calendar-day', { 'other-month': !day.isCurrentMonth }]"
          >
            <div class="day-number">{{ day.day }}</div>
            <div v-if="day.schedules?.redemptions?.length > 0" class="day-schedules">
              <el-popover
                v-for="fund in day.schedules.redemptions"
                :key="fund.fund_code"
                placement="top"
                :width="300"
                trigger="hover"
              >
                <template #reference>
                  <div class="fund-short-name redemption">
                    {{ getFundShortName(fund.fund_name) }}
                  </div>
                </template>
                <div>
                  <strong>{{ fund.fund_code }}</strong><br>
                  {{ fund.fund_name }}<br>
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
const selectedRules = ref([])
const fundList = ref([])
const fundSearchLoading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('添加档期规则')
const datesDialogVisible = ref(false)
const calculatedDates = ref(null)
const selectedMonth = ref(null)
const calendarData = ref(null)
const inputMode = ref('search')

const ruleForm = ref({
  fund_code: '',
  fund_name: '',
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
  inputMode.value = 'search'
  ruleForm.value = {
    fund_code: '',
    fund_name: '',
    subscription_rule: '',
    redemption_rule: '',
    lock_period: ''
  }
  dialogVisible.value = true
}

function editRule(row) {
  dialogTitle.value = '编辑档期规则'
  inputMode.value = 'manual'
  ruleForm.value = {
    fund_code: row.fund_code,
    fund_name: row.fund_name || '',
    subscription_rule: row.subscription_rule || '',
    redemption_rule: row.redemption_rule || '',
    lock_period: row.lock_period || ''
  }
  dialogVisible.value = true
}

async function saveRule() {
  if (!ruleForm.value.fund_code) {
    ElMessage.warning('请输入基金代码')
    return
  }

  if (inputMode.value === 'manual' && !ruleForm.value.fund_name) {
    ElMessage.warning('请输入基金名称')
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
  inputMode.value = 'search'
  ruleForm.value = {
    fund_code: '',
    fund_name: '',
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

function handleSelectionChange(selection) {
  selectedRules.value = selection
}

async function batchDeleteRules() {
  if (selectedRules.value.length === 0) {
    ElMessage.warning('请先选择要删除的规则')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRules.value.length} 条档期规则吗？`,
      '确认批量删除',
      {
        type: 'warning'
      }
    )

    const deletePromises = selectedRules.value.map(rule =>
      axios.delete(`${API_BASE}/api/fund-schedules/rules/${rule.fund_code}`)
    )

    await Promise.all(deletePromises)
    ElMessage.success(`成功删除 ${selectedRules.value.length} 条规则`)
    selectedRules.value = []
    loadScheduleRules()
    loadCalendarData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

function showSelectedInCalendar() {
  if (selectedRules.value.length === 0) {
    ElMessage.warning('请先选择要显示的规则')
    return
  }

  loadCalendarData(true)
  ElMessage.success(`已在日历中显示选中的 ${selectedRules.value.length} 个产品`)
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

async function loadCalendarData(onlySelected = false) {
  if (!selectedMonth.value || scheduleRules.value.length === 0) {
    calendarData.value = null
    return
  }

  const [year, month] = selectedMonth.value.split('-')

  // 如果onlySelected为true且有选中的规则，只显示选中的；否则显示所有
  let fundCodes
  if (onlySelected && selectedRules.value.length > 0) {
    fundCodes = selectedRules.value.map(r => r.fund_code)
  } else {
    fundCodes = scheduleRules.value.map(r => r.fund_code)
  }

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

// 处理策略变更
async function handleStrategyChange(row) {
  // 检查是否有必要字段
  if (!row.main_strategy && !row.sub_strategy) {
    return // 两个都为空，不保存
  }

  if (!row.main_strategy) {
    ElMessage.warning('请选择大类策略')
    return
  }

  try {
    // 先查询策略表中是否已存在该产品的策略
    const existingStrategyResponse = await axios.get(`${API_BASE}/api/strategy/${row.fund_code}`)
    const existingStrategy = existingStrategyResponse.data

    // 检查是否有冲突（同一产品策略信息不同）
    if (existingStrategy &&
        (existingStrategy.main_strategy !== row.main_strategy ||
         existingStrategy.sub_strategy !== row.sub_strategy)) {
      // 弹窗确认
      try {
        await ElMessageBox.confirm(
          `产品 ${row.fund_code} 的策略信息在策略表中已存在且不同：\n\n` +
          `现有策略：${existingStrategy.main_strategy} - ${existingStrategy.sub_strategy || '--'}\n` +
          `新策略：${row.main_strategy} - ${row.sub_strategy || '--'}\n\n` +
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
        row.main_strategy = existingStrategy.main_strategy
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
      main_strategy: row.main_strategy,
      sub_strategy: row.sub_strategy || '',
      is_qd: false
    })

    ElMessage.success(`产品 ${row.fund_code} 策略信息已保存`)

    // 保存成功后，从后端重新获取该产品的策略数据以确认保存成功
    try {
      const savedStrategyResponse = await axios.get(`${API_BASE}/api/strategy/${row.fund_code}`)
      const savedStrategy = savedStrategyResponse.data

      // 更新本地表格数据，确保显示的是数据库中的实际值
      row.main_strategy = savedStrategy.main_strategy
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

function getFundShortName(fullName) {
  if (!fullName) return ''

  let shortName = fullName

  // 去掉"龙舟-"前缀
  shortName = shortName.replace(/^龙舟-/, '')

  // 去掉"私募证券投资基金"及其后面的所有内容
  // 匹配"私募证券投资基金"后面可能跟着的：A1号、Z1号、I期、C类等
  shortName = shortName.replace(/私募证券投资基金.*$/, '')

  // 去掉尾部可能残留的数字+期（如果没被上面匹配到）
  shortName = shortName.replace(/[一二三四五六七八九十]期$/, '')
  shortName = shortName.replace(/\d+期$/, '')

  // 去掉尾部的"-"或空格
  shortName = shortName.replace(/[-\s]+$/, '')

  return shortName.trim()
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

.batch-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.selected-count {
  color: #409EFF;
  font-weight: bold;
  margin-right: 10px;
}

.calendar-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  white-space: nowrap;
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

.fund-short-name {
  background-color: #e88a8a;
  color: white;
  font-size: 12px;
  padding: 4px 8px;
  margin: 2px 0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
  word-break: break-all;
  line-height: 1.4;
}

.fund-short-name:hover {
  background-color: #d97777;
  transform: scale(1.05);
}

.fund-short-name.redemption {
  background-color: #e6a23c;
}

.fund-short-name.redemption:hover {
  background-color: #cf9236;
}
</style>
