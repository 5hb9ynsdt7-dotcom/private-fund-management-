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
              type="warning"
              size="small"
              @click="batchSetDefaultFee"
            >
              批量设置默认费用
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="showOrderGuide"
            >
              添加订单指引
            </el-button>
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
        <el-table-column prop="fund_code" label="基金代码" width="84" />
        <el-table-column prop="fund_name" label="基金简称" width="240">
          <template #default="{ row }">
            {{ getFundShortName(row.fund_name) }}
          </template>
        </el-table-column>
        <el-table-column prop="main_strategy" label="大类策略" width="120" align="center" />
        <el-table-column prop="sub_strategy" label="细分策略" width="120" align="center" />
        <el-table-column prop="subscription_rule" label="申购规则" min-width="252" />
        <el-table-column prop="redemption_rule" label="赎回规则" min-width="180" />
        <el-table-column prop="lock_period" label="锁定期" width="120" />
        <el-table-column label="费用" width="144" align="center">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="editFeeStructure(scope.row)"
            >
              {{ getFeeStructureSummary(scope.row.fee_structure) }}
            </el-button>
          </template>
        </el-table-column>
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
          <el-form-item label="大类策略">
            <el-select
              v-model="ruleForm.main_strategy"
              placeholder="选择大类策略"
              style="width: 100%"
            >
              <el-option label="成长配置" value="成长配置" />
              <el-option label="底仓配置" value="底仓配置" />
              <el-option label="尾部对冲" value="尾部对冲" />
            </el-select>
          </el-form-item>
          <el-form-item label="细分策略">
            <el-input
              v-model="ruleForm.sub_strategy"
              placeholder="例如：主观多头、量化多头等"
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

    <!-- 费用结构编辑对话框 -->
    <el-dialog
      v-model="feeDialogVisible"
      title="编辑费用结构"
      width="700px"
    >
      <div style="margin-bottom: 20px">
        <strong>产品：</strong>{{ feeStructureForm.fund_code }} - {{ feeStructureForm.fund_name }}
      </div>

      <el-table :data="feeStructureForm.fee_tiers" border style="width: 100%">
        <el-table-column label="费用类型" width="120">
          <template #default="{ row }">
            <el-select v-model="row.fee_type" size="small">
              <el-option label="申购费" value="申购费" />
              <el-option label="认购费" value="认购费" />
              <el-option label="赎回费" value="赎回费" />
              <el-option label="管理费" value="管理费" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="最小金额（万元）" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.amount_min"
              :min="0"
              :precision="2"
              size="small"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="最大金额（万元）" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.amount_max"
              :min="0"
              :precision="2"
              size="small"
              placeholder="无上限"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="费率（%）" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.rate"
              :min="0"
              :max="100"
              :precision="2"
              size="small"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ $index }">
            <el-button
              type="danger"
              size="small"
              @click="removeFeeTier($index)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 10px">
        <el-button type="primary" size="small" @click="addFeeTier">
          添加档位
        </el-button>
      </div>

      <div style="margin-top: 20px; padding: 10px; background-color: #f5f7fa; border-radius: 4px">
        <div style="font-weight: 600; margin-bottom: 8px">费用预览：</div>
        <div v-for="(tier, index) in feeStructureForm.fee_tiers" :key="index" style="margin-bottom: 4px">
          <span style="color: #606266">
            {{ tier.fee_type }}：
            {{ formatAmount(tier.amount_min) }} ≤ M
            <span v-if="tier.amount_max !== null && tier.amount_max !== ''">
              &lt; {{ formatAmount(tier.amount_max) }}
            </span>
            <span v-else>（无上限）</span>
            → {{ tier.rate }}%
          </span>
        </div>
        <div v-if="feeStructureForm.fee_tiers.length === 0" style="color: #909399">
          暂无费用档位
        </div>
      </div>

      <template #footer>
        <el-button @click="feeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFeeStructure">保存</el-button>
      </template>
    </el-dialog>

    <!-- 订单指引对话框 -->
    <el-dialog
      v-model="orderGuideDialogVisible"
      title="订单指引"
      width="1200px"
      @close="resetOrderGuide"
    >
      <div style="margin-bottom: 15px">
        <el-input
          v-model="orderGuideTitle"
          placeholder="输入标题，如：XX总的订单指引"
          style="width: 400px"
        />
      </div>

      <div ref="orderGuideExportRef" style="background: white; padding: 20px;">
        <div style="margin-bottom: 15px; text-align: center;">
          <h2 style="margin: 0; font-size: 20px; font-weight: bold;">{{ orderGuideTitle }}</h2>
        </div>

        <el-table :data="orderGuideItems" border style="width: 100%;" max-height="500" show-summary :summary-method="getOrderGuideSummary">
          <el-table-column label="产品简称" min-width="180" prop="fund_short_name" fixed />
          <el-table-column label="买入金额（万元）" min-width="140">
            <template #default="{ row }">
              <!-- 导出模式：显示纯文本 -->
              <span v-if="isExportMode">{{ row.purchase_amount.toFixed(2) }}</span>
              <!-- 交互模式：显示输入框 -->
              <el-input-number
                v-else
                v-model="row.purchase_amount"
                :min="0"
                :precision="2"
                size="small"
                style="width: 100%"
                @change="calculateFee(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="前端费用（万元）" min-width="130">
            <template #default="{ row }">
              <span>{{ row.frontend_fee.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="合计打款（万元）" min-width="130">
            <template #default="{ row }">
              <span>{{ row.total_payment.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="档期" min-width="140">
            <template #default="{ row }">
              <!-- 导出模式：显示纯文本 -->
              <span v-if="isExportMode">{{ row.schedule_date }}</span>
              <!-- 交互模式：显示下拉框 -->
              <el-select
                v-else
                v-model="row.schedule_date"
                size="small"
                style="width: 100%"
                @change="updateDatesOnScheduleChange(row)"
              >
                <el-option
                  v-for="(date, index) in row.available_schedules"
                  :key="index"
                  :label="date"
                  :value="date"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="余额+支付截止日" min-width="130">
            <template #default="{ row }">
              <span>{{ row.balance_operation_date }}</span>
            </template>
          </el-table-column>
          <el-table-column label="转账支付截止日" min-width="130">
            <template #default="{ row }">
              <span>{{ row.latest_payment_date }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 余额+支付提醒 -->
        <div style="margin-top: 30px; padding: 15px 20px; background-color: #fff3e0; border-radius: 6px; border: 2px solid #ff9800; border-left: 6px solid #ff9800;">
          <div style="display: flex; align-items: center; color: #e65100;">
            <span style="font-size: 18px; margin-right: 8px;">⚠️</span>
            <span style="font-weight: bold; font-size: 15px;">余额+支付提醒：</span>
            <span style="margin-left: 8px; font-size: 14px;">需要于余额+打款截止日当天的14:55前完成操作</span>
          </div>
        </div>

        <!-- 转账指引 -->
        <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 6px; border: 1px solid #e9ecef;">
          <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; border-bottom: 2px solid #409EFF; padding-bottom: 8px;">
            转账指引
          </div>
          <div style="line-height: 2; color: #606266;">
            <div style="display: flex; margin-bottom: 8px;">
              <span style="min-width: 150px; font-weight: 500; color: #303133;">收款户名：</span>
              <span>诺亚正行基金销售有限公司私募基金募集结算专户</span>
            </div>
            <div style="display: flex; margin-bottom: 8px;">
              <span style="min-width: 150px; font-weight: 500; color: #303133;">收款账号：</span>
              <span style="font-family: monospace; font-size: 15px; font-weight: 500;">627121167</span>
            </div>
            <div style="display: flex; margin-bottom: 8px;">
              <span style="min-width: 150px; font-weight: 500; color: #303133;">开户行：</span>
              <span>中国民生银行股份有限公司上海滨江支行</span>
            </div>
            <div style="display: flex; margin-bottom: 8px;">
              <span style="min-width: 150px; font-weight: 500; color: #303133;">大额支付联行号：</span>
              <span style="font-family: monospace; font-size: 15px; font-weight: 500;">305290002375</span>
            </div>
            <div style="display: flex;">
              <span style="min-width: 150px; font-weight: 500; color: #303133;">转账可备注：</span>
              <span style="color: #409EFF;">缴付投资款</span>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="orderGuideDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="exportOrderGuide">导出指引</el-button>
      </template>
    </el-dialog>

    <!-- 批量设置费用方案选择对话框 -->
    <el-dialog
      v-model="batchFeeDialogVisible"
      title="选择费用方案"
      width="600px"
    >
      <div style="margin-bottom: 20px">
        <strong>为选中的 {{ selectedRules.length }} 个产品设置默认费用</strong>
      </div>

      <el-radio-group v-model="selectedFeeTemplate" style="width: 100%">
        <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #dcdfe6; border-radius: 4px; cursor: pointer"
             :style="{ backgroundColor: selectedFeeTemplate === 'template1' ? '#f0f9ff' : 'white', borderColor: selectedFeeTemplate === 'template1' ? '#409EFF' : '#dcdfe6' }"
             @click="selectedFeeTemplate = 'template1'">
          <el-radio value="template1" style="margin-bottom: 10px">
            <strong>方案一（标准费率）</strong>
          </el-radio>
          <div style="margin-left: 24px; color: #606266">
            <div>· 100万 ≤ 认申购金额 &lt; 1000万：费率 <strong style="color: #409EFF">0.5%</strong></div>
            <div>· 认申购金额 ≥ 1000万：费率 <strong style="color: #67c23a">0%</strong></div>
          </div>
        </div>

        <div style="padding: 15px; border: 1px solid #dcdfe6; border-radius: 4px; cursor: pointer"
             :style="{ backgroundColor: selectedFeeTemplate === 'template2' ? '#f0f9ff' : 'white', borderColor: selectedFeeTemplate === 'template2' ? '#409EFF' : '#dcdfe6' }"
             @click="selectedFeeTemplate = 'template2'">
          <el-radio value="template2" style="margin-bottom: 10px">
            <strong>方案二（高费率）</strong>
          </el-radio>
          <div style="margin-left: 24px; color: #606266">
            <div>· 100万 ≤ 认申购金额 &lt; 1000万：费率 <strong style="color: #e6a23c">1%</strong></div>
            <div>· 认申购金额 ≥ 1000万：费率 <strong style="color: #67c23a">0%</strong></div>
          </div>
        </div>
      </el-radio-group>

      <div v-if="selectedRules.filter(r => r.fee_structure).length > 0"
           style="margin-top: 15px; padding: 10px; background-color: #fff3e0; border-radius: 4px; color: #e6a23c">
        <strong>⚠️ 注意：</strong>其中 {{ selectedRules.filter(r => r.fee_structure).length }} 个产品已有费用设置，将被覆盖！
      </div>

      <template #footer>
        <el-button @click="batchFeeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchSetFee">确定设置</el-button>
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

      <!-- 策略颜色图例 -->
      <div class="strategy-legend">
        <span class="legend-title">策略图例：</span>
        <div class="legend-items">
          <span
            v-for="(color, strategy) in strategyColors"
            :key="strategy"
            class="legend-item"
          >
            <span
              class="legend-color"
              :style="{ backgroundColor: color }"
            ></span>
            <span class="legend-text">{{ strategy }}</span>
          </span>
        </div>
      </div>

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
                  <div
                    class="fund-short-name"
                    :style="{ backgroundColor: getStrategyColor(fund.sub_strategy) }"
                  >
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
                  <div
                    class="fund-short-name"
                    :style="{ backgroundColor: getStrategyColor(fund.sub_strategy, true) }"
                  >
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
import html2canvas from 'html2canvas'

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8003'

// 细分策略颜色映射
const strategyColors = {
  'CTA策略': '#9C27B0',      // 紫色
  '主观多头': '#F44336',      // 红色
  '债券策略': '#4CAF50',      // 绿色
  '多策略': '#FF9800',        // 橙色
  '宏观策略': '#2196F3',      // 蓝色
  '稳健策略': '#00BCD4',      // 青色
  '股债混合': '#FFC107',      // 金色
  '股票多头': '#E91E63',      // 粉红
  '股票多空': '#795548',      // 棕色
  '量化多头': '#3F51B5',      // 靛蓝
  '量化稳健': '#009688',      // 青绿
}

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
const feeDialogVisible = ref(false)
const feeStructureForm = ref({
  fund_code: '',
  fund_name: '',
  fee_tiers: [],
  subscription_rule: '',
  redemption_rule: '',
  lock_period: ''
})

const orderGuideDialogVisible = ref(false)
const orderGuideTitle = ref('')
const orderGuideItems = ref([])
const orderGuideExportRef = ref(null)  // 用于导出的容器引用
const isExportMode = ref(false)  // 标记是否处于导出模式

const batchFeeDialogVisible = ref(false)
const selectedFeeTemplate = ref('template1')

const ruleForm = ref({
  fund_code: '',
  fund_name: '',
  subscription_rule: '',
  redemption_rule: '',
  lock_period: '',
  fee_structure: '',
  main_strategy: '',
  sub_strategy: ''
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
      // 获取数据后进行排序
      const rules = response.data.data

      // 按照：大类策略 -> 细分策略 -> 基金简称 进行排序
      rules.sort((a, b) => {
        // 1. 首先按大类策略排序
        const mainStrategyA = a.main_strategy || ''
        const mainStrategyB = b.main_strategy || ''
        const mainStrategyCompare = mainStrategyA.localeCompare(mainStrategyB, 'zh-CN')
        if (mainStrategyCompare !== 0) return mainStrategyCompare

        // 2. 大类策略相同时，按细分策略排序
        const subStrategyA = a.sub_strategy || ''
        const subStrategyB = b.sub_strategy || ''
        const subStrategyCompare = subStrategyA.localeCompare(subStrategyB, 'zh-CN')
        if (subStrategyCompare !== 0) return subStrategyCompare

        // 3. 细分策略相同时，按基金简称排序
        const fundNameA = getFundShortName(a.fund_name || '')
        const fundNameB = getFundShortName(b.fund_name || '')
        return fundNameA.localeCompare(fundNameB, 'zh-CN')
      })

      scheduleRules.value = rules
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
      // 如果提供了策略信息，保存策略
      if (ruleForm.value.main_strategy || ruleForm.value.sub_strategy) {
        try {
          await axios.post(`${API_BASE}/api/strategy`, {
            fund_code: ruleForm.value.fund_code,
            main_strategy: ruleForm.value.main_strategy,
            sub_strategy: ruleForm.value.sub_strategy
          })
        } catch (strategyError) {
          console.error('保存策略失败:', strategyError)
          // 策略保存失败不影响档期规则保存
        }
      }

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
    lock_period: '',
    fee_structure: '',
    main_strategy: '',
    sub_strategy: ''
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

// 处理产品名称变更
async function handleFundNameChange(row, newShortName) {
  // 检查产品名称是否为空
  if (!newShortName || newShortName.trim() === '') {
    ElMessage.warning('产品名称不能为空')
    loadScheduleRules() // 重新加载数据恢复原值
    return
  }

  // 如果简称没有变化，不需要更新
  const currentShortName = getFundShortName(row.fund_name)
  if (newShortName === currentShortName) {
    return
  }

  // 构建完整的基金名称
  // 保留原有的"龙舟-"前缀和"私募证券投资基金"后缀
  let fullName = newShortName

  // 如果原名称有"龙舟-"前缀，保留它
  if (row.fund_name && row.fund_name.startsWith('龙舟-')) {
    fullName = '龙舟-' + newShortName
  }

  // 如果原名称有"私募证券投资基金"，添加它
  if (row.fund_name && row.fund_name.includes('私募证券投资基金')) {
    fullName = fullName + '私募证券投资基金'
  }

  try {
    const response = await axios.patch(
      `${API_BASE}/api/funds/${row.fund_code}/fund-name`,
      { fund_name: fullName }
    )

    if (response.data.success) {
      ElMessage.success('产品名称更新成功')
      loadScheduleRules() // 重新加载数据
    }
  } catch (error) {
    console.error('更新产品名称失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新产品名称失败')
    loadScheduleRules() // 重新加载数据恢复原值
  }
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

  // 去掉"龙舟-"前缀（支持多种分隔符）
  shortName = shortName.replace(/^龙舟[-—\s]*/, '')

  // 检查是否有"私募证券投资基金"后面的后缀
  const match = shortName.match(/(.+?)私募证券投资基金(.*)$/)

  if (match) {
    const baseName = match[1].trim() // 基金名称主体部分
    let suffix = match[2].trim() // 后缀部分（如Z1号、C等）

    // 清理后缀中可能的多余空格或符号
    suffix = suffix.replace(/^[-\s]+/, '').replace(/[-\s]+$/, '')

    if (suffix) {
      // 有后缀，添加中文括号
      shortName = `${baseName}（${suffix}）`
    } else {
      // 无后缀
      shortName = baseName
    }
  } else {
    // 没有匹配到"私募证券投资基金"，尝试其他后缀
    shortName = shortName.replace(/私募投资基金.*$/, '')
    shortName = shortName.replace(/证券投资基金.*$/, '')
    shortName = shortName.replace(/投资基金.*$/, '')
  }

  // 去掉尾部的"-"或空格
  shortName = shortName.replace(/[-\s]+$/, '')

  return shortName.trim()
}

// 根据细分策略获取对应颜色
function getStrategyColor(subStrategy, isDarker = false) {
  // 如果策略为空或未定义，返回默认颜色
  if (!subStrategy) {
    return isDarker ? '#B0BEC5' : '#CFD8DC' // 灰色
  }

  // 获取策略对应的颜色
  const baseColor = strategyColors[subStrategy]

  if (!baseColor) {
    // 未匹配到策略，返回默认颜色
    return isDarker ? '#B0BEC5' : '#CFD8DC' // 灰色
  }

  // 如果需要更深的颜色（用于赎回日历），调暗基础颜色
  if (isDarker) {
    return adjustColorBrightness(baseColor, -20)
  }

  return baseColor
}

// 调整颜色亮度
function adjustColorBrightness(hex, percent) {
  // 将十六进制转换为RGB
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.max(0, Math.min(255, (num >> 16) + percent))
  const g = Math.max(0, Math.min(255, ((num >> 8) & 0x00FF) + percent))
  const b = Math.max(0, Math.min(255, (num & 0x0000FF) + percent))

  // 转换回十六进制
  return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')
}

// 获取费用结构摘要
function getFeeStructureSummary(feeStructureJson) {
  if (!feeStructureJson) {
    return '设置费用'
  }

  try {
    const feeStructure = JSON.parse(feeStructureJson)
    if (!feeStructure || feeStructure.length === 0) {
      return '设置费用'
    }

    // 提取第一个档位的费率（通常是主要费率）
    const firstTier = feeStructure[0]
    if (firstTier && firstTier.rate !== undefined) {
      return `${firstTier.rate}%`
    }

    return '设置费用'
  } catch (e) {
    return '设置费用'
  }
}

// 编辑费用结构
function editFeeStructure(row) {
  feeStructureForm.value.fund_code = row.fund_code
  feeStructureForm.value.fund_name = row.fund_name || row.fund_code

  // 保存原有的规则数据，避免覆盖
  feeStructureForm.value.subscription_rule = row.subscription_rule || ''
  feeStructureForm.value.redemption_rule = row.redemption_rule || ''
  feeStructureForm.value.lock_period = row.lock_period || ''

  // 解析现有的费用结构
  if (row.fee_structure) {
    try {
      feeStructureForm.value.fee_tiers = JSON.parse(row.fee_structure)
    } catch (e) {
      feeStructureForm.value.fee_tiers = []
    }
  } else {
    feeStructureForm.value.fee_tiers = []
  }

  // 如果没有档位，添加默认档位：100万<1000万 0.5%，≥1000万 0%
  if (feeStructureForm.value.fee_tiers.length === 0) {
    feeStructureForm.value.fee_tiers = [
      {
        amount_min: 100,
        amount_max: 1000,
        rate: 0.5,
        fee_type: '申购费'
      },
      {
        amount_min: 1000,
        amount_max: null,
        rate: 0,
        fee_type: '申购费'
      }
    ]
  }

  feeDialogVisible.value = true
}

// 添加费用档位
function addFeeTier() {
  feeStructureForm.value.fee_tiers.push({
    amount_min: 0,
    amount_max: null,
    rate: 0,
    fee_type: '申购费'
  })
}

// 删除费用档位
function removeFeeTier(index) {
  feeStructureForm.value.fee_tiers.splice(index, 1)
}

// 保存费用结构
async function saveFeeStructure() {
  try {
    // 验证数据
    for (let i = 0; i < feeStructureForm.value.fee_tiers.length; i++) {
      const tier = feeStructureForm.value.fee_tiers[i]
      if (tier.amount_min === null || tier.amount_min === '') {
        ElMessage.warning(`请填写第${i + 1}个档位的最小金额`)
        return
      }
      if (tier.rate === null || tier.rate === '') {
        ElMessage.warning(`请填写第${i + 1}个档位的费率`)
        return
      }
    }

    // 将费用结构转换为JSON字符串
    const feeStructureJson = JSON.stringify(feeStructureForm.value.fee_tiers)

    // 调用后端API保存，同时发送所有字段以避免覆盖
    const response = await axios.post(`${API_BASE}/api/fund-schedules/rules`, {
      fund_code: feeStructureForm.value.fund_code,
      fee_structure: feeStructureJson,
      subscription_rule: feeStructureForm.value.subscription_rule,
      redemption_rule: feeStructureForm.value.redemption_rule,
      lock_period: feeStructureForm.value.lock_period
    })

    if (response.data.success) {
      ElMessage.success('费用结构保存成功')
      feeDialogVisible.value = false
      loadScheduleRules()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

// 格式化金额显示
function formatAmount(amount) {
  if (amount === null || amount === undefined) {
    return '无上限'
  }
  return `${amount}万`
}

// 显示订单指引对话框
async function showOrderGuide() {
  if (selectedRules.value.length === 0) {
    ElMessage.warning('请先选择产品')
    return
  }

  orderGuideTitle.value = 'XX总的订单指引'
  orderGuideItems.value = []

  // 为每个选中的产品创建订单指引项
  for (const rule of selectedRules.value) {
    // 获取可用的档期日期列表（未来3个月）
    const availableSchedules = await getAvailableScheduleDates(rule)

    // 默认选择最近的档期
    const defaultSchedule = availableSchedules.length > 0 ? availableSchedules[0] : null

    // 计算余额+操作日和最迟打款日
    let balanceOperationDate = ''
    let latestPaymentDate = ''

    if (defaultSchedule) {
      balanceOperationDate = await calculateTradingDate(defaultSchedule, -2)
      latestPaymentDate = await calculateTradingDate(defaultSchedule, -1)
    }

    orderGuideItems.value.push({
      fund_code: rule.fund_code,
      fund_short_name: getFundShortName(rule.fund_name),
      fund_name: rule.fund_name,
      purchase_amount: 100, // 默认100万
      frontend_fee: 0,
      total_payment: 100,
      schedule_date: defaultSchedule,
      available_schedules: availableSchedules,
      balance_operation_date: balanceOperationDate,
      latest_payment_date: latestPaymentDate,
      fee_structure: rule.fee_structure
    })

    // 计算默认费用
    const lastItem = orderGuideItems.value[orderGuideItems.value.length - 1]
    calculateFee(lastItem)
  }

  orderGuideDialogVisible.value = true
}

// 获取下一个档期日期
async function getNextScheduleDate(rule) {
  try {
    // 获取当前月份和下个月
    const now = new Date()
    const currentYear = now.getFullYear()
    const currentMonth = now.getMonth() + 1

    // 计算未来2个月的档期日期
    const months = [
      { year: currentYear, month: currentMonth },
      { year: currentMonth === 12 ? currentYear + 1 : currentYear, month: currentMonth === 12 ? 1 : currentMonth + 1 }
    ]

    let nearestDate = null
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    for (const { year, month } of months) {
      const response = await axios.post(`${API_BASE}/api/fund-schedules/calculate`, {
        fund_code: rule.fund_code,
        year: year,
        month: month
      })

      if (response.data.success) {
        const dates = response.data.data.subscription_dates || []

        for (const dateObj of dates) {
          const scheduleDate = new Date(dateObj.date)
          scheduleDate.setHours(0, 0, 0, 0)

          // 找到第一个大于今天的日期
          if (scheduleDate > today) {
            if (!nearestDate || scheduleDate < nearestDate) {
              nearestDate = scheduleDate
            }
          }
        }
      }
    }

    if (nearestDate) {
      // 最迟打款日 = 档期日 - 1天
      const paymentDate = new Date(nearestDate)
      paymentDate.setDate(paymentDate.getDate() - 1)
      return paymentDate.toISOString().split('T')[0]
    } else {
      // 如果没有找到档期日，返回今天
      return new Date().toISOString().split('T')[0]
    }
  } catch (error) {
    console.error('获取档期日期失败:', error)
    return new Date().toISOString().split('T')[0]
  }
}

// 计算费用
function calculateFee(item) {
  if (!item.purchase_amount || item.purchase_amount <= 0) {
    item.frontend_fee = 0
    item.total_payment = 0
    return
  }

  // 解析费用结构
  let feeRate = 0

  if (item.fee_structure) {
    try {
      const feeStructure = JSON.parse(item.fee_structure)

      // 根据买入金额找到对应的费率档位
      for (const tier of feeStructure) {
        const amountMin = tier.amount_min || 0
        const amountMax = tier.amount_max

        // 检查金额是否在此档位范围内
        if (item.purchase_amount >= amountMin) {
          if (amountMax === null || amountMax === undefined || item.purchase_amount < amountMax) {
            feeRate = tier.rate || 0
            break
          }
        }
      }
    } catch (e) {
      console.error('解析费用结构失败:', e)
      feeRate = 0
    }
  }

  // 计算费用和合计
  item.frontend_fee = (item.purchase_amount * feeRate) / 100
  item.total_payment = item.purchase_amount + item.frontend_fee
}

// 获取可用的档期日期列表（未来3个月）
async function getAvailableScheduleDates(rule) {
  try {
    const now = new Date()
    const currentYear = now.getFullYear()
    const currentMonth = now.getMonth() + 1

    const allDates = []
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    // 计算未来3个月的档期日期
    for (let i = 0; i < 3; i++) {
      let month = currentMonth + i
      let year = currentYear

      while (month > 12) {
        month -= 12
        year += 1
      }

      const response = await axios.post(`${API_BASE}/api/fund-schedules/calculate`, {
        fund_code: rule.fund_code,
        year: year,
        month: month
      })

      if (response.data.success) {
        const dates = response.data.data.subscription_dates || []

        for (const dateObj of dates) {
          const scheduleDate = new Date(dateObj.date)
          scheduleDate.setHours(0, 0, 0, 0)

          // 只保留未来的日期
          if (scheduleDate > today) {
            allDates.push(dateObj.date)
          }
        }
      }
    }

    // 按日期排序
    allDates.sort()

    return allDates
  } catch (error) {
    console.error('获取可用档期失败:', error)
    return []
  }
}

// 计算交易日（offset为偏移天数，-1表示T-1，-2表示T-2）
// 会自动排除周末
async function calculateTradingDate(scheduleDate, offset) {
  if (!scheduleDate) return ''

  const date = new Date(scheduleDate)
  let daysToSubtract = Math.abs(offset)
  let tradingDaysCount = 0

  // 从档期日往前推算交易日
  while (tradingDaysCount < daysToSubtract) {
    date.setDate(date.getDate() - 1)

    // 检查是否是周末（0=周日, 6=周六）
    const dayOfWeek = date.getDay()
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      tradingDaysCount++
    }
  }

  return date.toISOString().split('T')[0]
}

// 当档期变化时更新余额+操作日和最迟打款日
async function updateDatesOnScheduleChange(item) {
  if (item.schedule_date) {
    item.balance_operation_date = await calculateTradingDate(item.schedule_date, -2)
    item.latest_payment_date = await calculateTradingDate(item.schedule_date, -1)
  }
}

// 计算订单指引合计行
function getOrderGuideSummary(param) {
  const { columns, data } = param
  const sums = []

  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }

    // 买入金额列
    if (index === 1) {
      const total = data.reduce((sum, row) => sum + (row.purchase_amount || 0), 0)
      sums[index] = total.toFixed(2)
      return
    }

    // 前端费用列
    if (index === 2) {
      const total = data.reduce((sum, row) => sum + (row.frontend_fee || 0), 0)
      sums[index] = total.toFixed(2)
      return
    }

    // 合计打款列
    if (index === 3) {
      const total = data.reduce((sum, row) => sum + (row.total_payment || 0), 0)
      sums[index] = total.toFixed(2)
      return
    }

    // 其他列显示空
    sums[index] = ''
  })

  return sums
}

// 重置订单指引
function resetOrderGuide() {
  orderGuideTitle.value = ''
  orderGuideItems.value = []
}

// 导出订单指引
async function exportOrderGuide() {
  if (!orderGuideExportRef.value) {
    ElMessage.error('导出失败：未找到导出内容')
    return
  }

  try {
    // 显示加载提示
    const loadingMessage = ElMessage.info({
      message: '正在生成图片，请稍候...',
      duration: 0
    })

    // 切换到导出模式（显示纯文本，隐藏输入框和下拉框）
    isExportMode.value = true

    // 等待DOM渲染完成
    await new Promise(resolve => setTimeout(resolve, 200))

    // 使用html2canvas捕获内容
    const canvas = await html2canvas(orderGuideExportRef.value, {
      backgroundColor: '#ffffff',
      scale: 2,  // 提高清晰度
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    // 恢复交互模式
    isExportMode.value = false

    // 将canvas转换为blob
    canvas.toBlob((blob) => {
      // 创建下载链接
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      const fileName = `${orderGuideTitle.value || '订单指引'}.png`
      link.href = url
      link.download = fileName
      link.click()

      // 清理
      URL.revokeObjectURL(url)

      // 关闭加载提示
      loadingMessage.close()
      ElMessage.success('导出成功')
    }, 'image/png')
  } catch (error) {
    console.error('导出失败:', error)
    // 确保恢复交互模式
    isExportMode.value = false
    ElMessage.error('导出失败，请重试')
  }
}

// 批量设置默认费用（打开选择对话框）
async function batchSetDefaultFee() {
  if (selectedRules.value.length === 0) {
    ElMessage.warning('请先选择产品')
    return
  }

  // 重置为方案一
  selectedFeeTemplate.value = 'template1'
  // 打开选择对话框
  batchFeeDialogVisible.value = true
}

// 确认批量设置费用
async function confirmBatchSetFee() {
  try {
    // 根据选择的方案确定费用结构
    let defaultFeeStructure
    if (selectedFeeTemplate.value === 'template1') {
      // 方案一：0.5% / 0%
      defaultFeeStructure = [
        {
          amount_min: 100,
          amount_max: 1000,
          rate: 0.5,
          fee_type: '申购费'
        },
        {
          amount_min: 1000,
          amount_max: null,
          rate: 0,
          fee_type: '申购费'
        }
      ]
    } else {
      // 方案二：1% / 0%
      defaultFeeStructure = [
        {
          amount_min: 100,
          amount_max: 1000,
          rate: 1,
          fee_type: '申购费'
        },
        {
          amount_min: 1000,
          amount_max: null,
          rate: 0,
          fee_type: '申购费'
        }
      ]
    }

    const feeStructureJson = JSON.stringify(defaultFeeStructure)

    let updatedCount = 0
    let errorCount = 0

    // 遍历选中的档期规则
    for (const rule of selectedRules.value) {
      try {
        await axios.post(`${API_BASE}/api/fund-schedules/rules`, {
          fund_code: rule.fund_code,
          fee_structure: feeStructureJson,
          subscription_rule: rule.subscription_rule,
          redemption_rule: rule.redemption_rule,
          lock_period: rule.lock_period
        })
        updatedCount++
      } catch (error) {
        console.error(`设置 ${rule.fund_code} 默认费用失败:`, error)
        errorCount++
      }
    }

    // 关闭对话框
    batchFeeDialogVisible.value = false

    if (updatedCount > 0) {
      const templateName = selectedFeeTemplate.value === 'template1' ? '方案一' : '方案二'
      ElMessage.success(`成功为 ${updatedCount} 个产品设置默认费用（${templateName}）`)
      loadScheduleRules()
    }

    if (errorCount > 0) {
      ElMessage.warning(`${errorCount} 个产品设置失败`)
    }
  } catch (error) {
    ElMessage.error('批量设置失败')
  }
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

.strategy-legend {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.legend-title {
  font-weight: 600;
  color: #303133;
  margin-right: 12px;
}

.legend-items {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 3px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.legend-text {
  font-size: 13px;
  color: #606266;
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.fund-short-name:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  filter: brightness(0.9);
}

</style>
