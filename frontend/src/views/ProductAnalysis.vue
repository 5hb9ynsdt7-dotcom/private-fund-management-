<template>
  <div class="product-analysis">
    <!-- 页面头部 -->
    <div class="page-header">
      <div>
        <h2>产品分析</h2>
        <p class="page-description">产品全维度指标分析与风险评估</p>
      </div>
      <el-button
        v-if="analysisData"
        type="primary"
        @click="downloadPDF"
        :loading="downloadLoading"
      >
        <el-icon><Download /></el-icon>
        下载分析报告
      </el-button>
    </div>

    <!-- 产品选择 -->
    <el-card class="filter-section">
      <el-row :gutter="16" align="middle">
        <el-col :span="8">
          <el-select
            v-model="selectedFundCode"
            placeholder="选择产品"
            filterable
            clearable
            style="width: 100%"
            @change="loadProductAnalysis"
          >
            <el-option
              v-for="fund in fundList"
              :key="fund.fund_code"
              :label="`${fund.fund_code} - ${fund.fund_name}`"
              :value="fund.fund_code"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="selectedBenchmark"
            placeholder="选择对比基准（可选）"
            clearable
            style="width: 100%"
            @change="loadProductAnalysis"
          >
            <el-option label="沪深300" value="000300.SH" />
            <el-option label="中证500" value="000905.SH" />
            <el-option label="中证1000" value="000852.SH" />
            <el-option label="中证2000" value="932000.CSI" />
            <el-option label="中证800" value="000906.SH" />
            <el-option label="上证指数" value="000001.SH" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadProductAnalysis" :loading="loading">
            <el-icon><Search /></el-icon>
            分析
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 导出内容区域 -->
    <div ref="exportContentRef" class="export-content">
      <!-- 产品信息标题 -->
      <div v-if="analysisData" class="product-info-header">
      <div class="product-title-section">
        <h3 class="product-title">{{ analysisData.short_name }}</h3>
        <div class="product-meta">
          <span class="strategy-tag">{{ analysisData.category_level1 }}</span>
          <span class="strategy-divider">|</span>
          <span class="strategy-tag">{{ analysisData.category_level2 }}</span>
        </div>
      </div>
      <div class="analysis-period">
        分析周期：{{ formatDate(analysisData.data_start_date) }} - {{ formatDate(analysisData.data_end_date) }}
      </div>
    </div>

    <!-- 基础指标卡片 -->
    <el-row :gutter="24" class="stats-section" v-if="analysisData">
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="累计收益率"
            :value="analysisData.basic_metrics.cumulative_return"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon :style="`color: ${analysisData.basic_metrics.cumulative_return >= 0 ? '#f56c6c' : '#67c23a'}`">
                <TrendCharts />
              </el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="年化收益率"
            :value="analysisData.basic_metrics.annualized_return"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon style="color: #409eff"><DataLine /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="最大回撤"
            :value="analysisData.basic_metrics.max_drawdown"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon style="color: #e6a23c"><Bottom /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="年化波动率"
            :value="analysisData.basic_metrics.volatility"
            :precision="2"
            suffix="%"
          >
            <template #prefix>
              <el-icon style="color: #909399"><Grid /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="夏普比率"
            :value="analysisData.basic_metrics.sharpe_ratio"
            :precision="2"
          >
            <template #prefix>
              <el-icon style="color: #67c23a"><Histogram /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <el-statistic
            title="卡玛比率"
            :value="analysisData.basic_metrics.calmar_ratio"
            :precision="2"
          >
            <template #prefix>
              <el-icon style="color: #f56c6c"><Trophy /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="24" v-if="analysisData">
      <el-col :span="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>净值走势与回撤</span>
            </div>
          </template>
          <div ref="navChartRef" style="width: 100%; height: 900px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 持有期分析 -->
    <el-row :gutter="24" v-if="analysisData">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>持有期收益分析</span>
              <el-tag>任意时间买入持有</el-tag>
            </div>
          </template>
          <el-table :data="analysisData.holding_period_analysis" border stripe>
            <el-table-column prop="period" label="持有期" align="center" />
            <el-table-column prop="sample_count" label="样本数" align="center" />
            <el-table-column label="盈利概率" align="center">
              <template #default="scope">
                <span class="percent-text" :style="`color: ${scope.row.profit_probability >= 50 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.profit_probability.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="平均收益" align="center">
              <template #default="scope">
                <span class="percent-text" :style="`color: ${scope.row.avg_return >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.avg_return >= 0 ? '+' : '' }}{{ scope.row.avg_return.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="最佳收益" align="center">
              <template #default="scope">
                <span class="percent-text" style="color: #f56c6c">
                  +{{ scope.row.max_return.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="最差收益" align="center">
              <template #default="scope">
                <span class="percent-text" style="color: #67c23a">
                  {{ scope.row.min_return.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 年度月度收益表 -->
    <el-row :gutter="24" v-if="analysisData">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>年度月度收益明细</span>
            </div>
          </template>
          <el-table :data="analysisData.monthly_returns.yearly_table" border stripe style="width: 100%">
            <el-table-column prop="year" label="年份" align="center" fixed />
            <el-table-column label="1月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_1 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_1 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_1 >= 0 ? '+' : '' }}{{ Number(scope.row.month_1).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="2月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_2 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_2 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_2 >= 0 ? '+' : '' }}{{ Number(scope.row.month_2).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="3月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_3 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_3 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_3 >= 0 ? '+' : '' }}{{ Number(scope.row.month_3).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="4月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_4 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_4 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_4 >= 0 ? '+' : '' }}{{ Number(scope.row.month_4).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="5月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_5 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_5 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_5 >= 0 ? '+' : '' }}{{ Number(scope.row.month_5).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="6月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_6 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_6 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_6 >= 0 ? '+' : '' }}{{ Number(scope.row.month_6).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="7月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_7 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_7 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_7 >= 0 ? '+' : '' }}{{ Number(scope.row.month_7).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="8月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_8 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_8 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_8 >= 0 ? '+' : '' }}{{ Number(scope.row.month_8).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="9月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_9 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_9 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_9 >= 0 ? '+' : '' }}{{ Number(scope.row.month_9).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="10月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_10 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_10 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_10 >= 0 ? '+' : '' }}{{ Number(scope.row.month_10).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="11月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_11 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_11 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_11 >= 0 ? '+' : '' }}{{ Number(scope.row.month_11).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="12月" align="center">
              <template #default="scope">
                <span v-if="scope.row.month_12 !== null"
                      class="percent-text"
                      :style="`color: ${scope.row.month_12 >= 0 ? '#f56c6c' : '#67c23a'}`">
                  {{ scope.row.month_12 >= 0 ? '+' : '' }}{{ Number(scope.row.month_12).toFixed(2) }}%
                </span>
                <span v-else style="color: #d1d5db">-</span>
              </template>
            </el-table-column>
            <el-table-column label="年度收益" align="center">
              <template #default="scope">
                <span v-if="scope.row.year_return !== null && scope.row.year_return !== undefined"
                      class="percent-text"
                      :style="`color: ${scope.row.year_return >= 0 ? '#f56c6c' : '#67c23a'}; font-weight: 600;`">
                  {{ scope.row.year_return >= 0 ? '+' : '' }}{{ Number(scope.row.year_return).toFixed(2) }}%
                </span>
                <span v-else style="color: #C0C4CC;">-</span>
              </template>
            </el-table-column>
            <el-table-column label="胜率" align="center" fixed="right">
              <template #default="scope">
                <span class="percent-text" style="color: #409eff; font-weight: 600;">
                  {{ Number(scope.row.win_rate).toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 月度收益分析 -->
    <el-row :gutter="24" v-if="analysisData">
      <el-col :span="16">
        <el-card class="monthly-card">
          <template #header>
            <div class="card-header">
              <span>月度收益分布</span>
            </div>
          </template>
          <div ref="monthlyReturnChartRef" style="width: 100%; height: 450px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="monthly-card">
          <template #header>
            <div class="card-header">
              <span>月度胜率统计</span>
            </div>
          </template>
          <div class="monthly-stats">
            <el-statistic
              title="月度胜率"
              :value="analysisData.monthly_stats.win_rate"
              :precision="2"
              suffix="%"
            >
              <template #prefix>
                <el-icon style="color: #409eff"><TrendCharts /></el-icon>
              </template>
            </el-statistic>
            <el-divider />
            <el-row :gutter="16">
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">上涨月份</div>
                  <div class="value positive">{{ analysisData.monthly_stats.positive_months }}个</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">下跌月份</div>
                  <div class="value negative">{{ analysisData.monthly_stats.negative_months }}个</div>
                </div>
              </el-col>
            </el-row>
            <el-divider />
            <el-row :gutter="16">
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">最佳月度</div>
                  <div class="value positive">+{{ analysisData.monthly_stats.best_month.toFixed(2) }}%</div>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="mini-stat">
                  <div class="label">最差月度</div>
                  <div class="value negative">{{ analysisData.monthly_stats.worst_month.toFixed(2) }}%</div>
                </div>
              </el-col>
            </el-row>
            <el-divider />
            <el-row :gutter="16">
              <el-col :span="24">
                <div class="mini-stat">
                  <div class="label">平均月度收益</div>
                  <div class="value" :class="analysisData.monthly_stats.avg_monthly_return >= 0 ? 'positive' : 'negative'">
                    {{ analysisData.monthly_stats.avg_monthly_return >= 0 ? '+' : '' }}{{ analysisData.monthly_stats.avg_monthly_return.toFixed(2) }}%
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最高点回本分析 -->
    <el-row :gutter="24" v-if="analysisData" class="compact-analysis">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最高点回本分析</span>
              <el-tag v-if="analysisData.peak_recovery.status === 'current_peak'" type="success">当前在历史最高点</el-tag>
              <el-tag v-else-if="analysisData.peak_recovery.status === 'recovered'" type="success">已回本</el-tag>
              <el-tag v-else type="warning">尚未回本</el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">历史最高净值</div>
                <div class="recovery-value-compact">{{ analysisData.peak_recovery.peak_nav }}</div>
                <div class="recovery-date-compact">{{ analysisData.peak_recovery.peak_date }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">
                  {{ analysisData.peak_recovery.status === 'current_peak' ? '当前状态' :
                     analysisData.peak_recovery.status === 'recovered' ? '回本时间' : '距最高点' }}
                </div>
                <div class="recovery-value-compact"
                     :style="`color: ${analysisData.peak_recovery.status === 'not_recovered' ? '#e6a23c' : '#67c23a'}`">
                  <template v-if="analysisData.peak_recovery.status === 'current_peak'">
                    在最高点
                  </template>
                  <template v-else-if="analysisData.peak_recovery.status === 'recovered'">
                    {{ analysisData.peak_recovery.recovery_days }}天
                  </template>
                  <template v-else>
                    {{ analysisData.peak_recovery.days_since_peak }}天
                  </template>
                </div>
                <div class="recovery-date-compact" v-if="analysisData.peak_recovery.recovery_date">
                  {{ analysisData.peak_recovery.recovery_date }}
                </div>
              </div>
            </el-col>
            <el-col :span="8" v-if="analysisData.peak_recovery.status === 'not_recovered'">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">当前回撤</div>
                <div class="recovery-value-compact" style="color: #e6a23c">
                  {{ analysisData.peak_recovery.current_drawdown_from_peak.toFixed(2) }}%
                </div>
                <div class="recovery-date-compact">需上涨 {{ Math.abs(analysisData.peak_recovery.current_drawdown_from_peak).toFixed(2) }}%</div>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="16" style="margin-top: 16px;">
            <el-col :span="24">
              <div class="recovery-description-section">
                <div class="recovery-label-compact">说明</div>
                <div class="recovery-description-full" v-if="analysisData.peak_recovery.status === 'not_recovered'">
                  在 {{ analysisData.peak_recovery.peak_date }} 最高点买入，至今 {{ analysisData.peak_recovery.days_since_peak }} 天，
                  仍亏损 {{ Math.abs(analysisData.peak_recovery.current_drawdown_from_peak).toFixed(2) }}%，尚未回本。
                </div>
                <div class="recovery-description-full" v-else-if="analysisData.peak_recovery.status === 'recovered'">
                  在 {{ analysisData.peak_recovery.peak_date }} 最高点买入，
                  经过 {{ analysisData.peak_recovery.recovery_days }} 天后在 {{ analysisData.peak_recovery.recovery_date }} 成功回本。
                </div>
                <div class="recovery-description-full" v-else>
                  产品当前净值处于历史最高点，表现优异。
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史最大回撤修复分析 -->
    <el-row :gutter="24" v-if="analysisData" class="compact-analysis">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>历史最大回撤修复分析</span>
              <el-tag v-if="analysisData.max_drawdown_analysis.is_recovered" type="success">已修复</el-tag>
              <el-tag v-else type="danger">尚未修复</el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="8">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">最大回撤</div>
                <div class="recovery-value-compact" style="color: #f56c6c">
                  {{ analysisData.max_drawdown_analysis.max_drawdown }}%
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">峰值</div>
                <div class="recovery-value-compact">{{ analysisData.max_drawdown_analysis.peak_nav }}</div>
                <div class="recovery-date-compact">{{ analysisData.max_drawdown_analysis.peak_date }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">谷底</div>
                <div class="recovery-value-compact" style="color: #67c23a">{{ analysisData.max_drawdown_analysis.trough_nav }}</div>
                <div class="recovery-date-compact">{{ analysisData.max_drawdown_analysis.trough_date }}</div>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="16" style="margin-top: 12px;">
            <el-col :span="8">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">回撤持续</div>
                <div class="recovery-value-compact" style="color: #e6a23c">
                  {{ analysisData.max_drawdown_analysis.drawdown_days }}天
                </div>
              </div>
            </el-col>
            <el-col :span="8" v-if="analysisData.max_drawdown_analysis.is_recovered">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">修复时间</div>
                <div class="recovery-value-compact" style="color: #67c23a">
                  {{ analysisData.max_drawdown_analysis.recovery_days }}天
                </div>
              </div>
            </el-col>
            <el-col :span="8" v-if="analysisData.max_drawdown_analysis.is_recovered">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">完整周期</div>
                <div class="recovery-value-compact">
                  {{ analysisData.max_drawdown_analysis.total_recovery_days }}天
                </div>
              </div>
            </el-col>
            <el-col :span="8" v-if="!analysisData.max_drawdown_analysis.is_recovered">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">距谷底</div>
                <div class="recovery-value-compact" style="color: #909399">
                  {{ analysisData.max_drawdown_analysis.days_since_trough }}天
                </div>
              </div>
            </el-col>
            <el-col :span="8" v-if="!analysisData.max_drawdown_analysis.is_recovered">
              <div class="recovery-item-compact">
                <div class="recovery-label-compact">当前净值</div>
                <div class="recovery-value-compact">{{ analysisData.max_drawdown_analysis.current_nav }}</div>
                <div class="recovery-date-compact">
                  距峰 {{ analysisData.max_drawdown_analysis.current_drawdown_from_peak.toFixed(2) }}%
                </div>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="16" style="margin-top: 16px;">
            <el-col :span="24">
              <div class="recovery-description-section">
                <div class="recovery-label-compact">说明</div>
                <div class="recovery-description-full" v-if="analysisData.max_drawdown_analysis.is_recovered">
                  历史最大回撤发生在 {{ analysisData.max_drawdown_analysis.peak_date }} 至 {{ analysisData.max_drawdown_analysis.trough_date }} 期间，
                  从净值 {{ analysisData.max_drawdown_analysis.peak_nav }} 回撤至 {{ analysisData.max_drawdown_analysis.trough_nav }}，
                  回撤幅度 {{ Math.abs(analysisData.max_drawdown_analysis.max_drawdown).toFixed(2) }}%，
                  持续 {{ analysisData.max_drawdown_analysis.drawdown_days }} 天。
                  随后经过 {{ analysisData.max_drawdown_analysis.recovery_days }} 天，
                  在 {{ analysisData.max_drawdown_analysis.recovery_date }} 成功修复至峰值水平。
                  从峰值到完全修复总计 {{ analysisData.max_drawdown_analysis.total_recovery_days }} 天。
                </div>
                <div class="recovery-description-full" v-else>
                  历史最大回撤发生在 {{ analysisData.max_drawdown_analysis.peak_date }} 至 {{ analysisData.max_drawdown_analysis.trough_date }} 期间，
                  从净值 {{ analysisData.max_drawdown_analysis.peak_nav }} 回撤至 {{ analysisData.max_drawdown_analysis.trough_nav }}，
                  回撤幅度 {{ Math.abs(analysisData.max_drawdown_analysis.max_drawdown).toFixed(2) }}%，
                  持续 {{ analysisData.max_drawdown_analysis.drawdown_days }} 天。
                  从谷底至今已过 {{ analysisData.max_drawdown_analysis.days_since_trough }} 天，
                  当前净值 {{ analysisData.max_drawdown_analysis.current_nav }}，
                  距峰值仍有 {{ Math.abs(analysisData.max_drawdown_analysis.current_drawdown_from_peak).toFixed(2) }}% 的差距，尚未完全修复。
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 产品深度分析模块 -->
    <el-card class="deep-analysis-card" v-if="analysisData && deepAnalysisData.exists">
      <template #header>
        <div class="card-header">
          <span>产品深度分析</span>
          <span class="analysis-period-sub" v-if="deepAnalysisData.analysis_period">
            分析区间：{{ deepAnalysisData.analysis_period.start_date }} 至 {{ deepAnalysisData.analysis_period.end_date }}
          </span>
        </div>
      </template>

      <!-- 上半部分：文字内容 -->
      <div class="analysis-summary-horizontal">
        <!-- 策略描述 -->
        <div class="summary-section" v-if="deepAnalysisData.strategy_description">
          <h4>策略特征</h4>
          <p class="strategy-desc">{{ deepAnalysisData.strategy_description }}</p>
        </div>

        <!-- 核心亮点和主要风险并排 -->
        <el-row :gutter="24">
          <!-- 核心亮点 -->
          <el-col :span="12" v-if="deepAnalysisData.highlights && deepAnalysisData.highlights.length > 0">
            <div class="summary-section">
              <h4>核心亮点</h4>
              <ul class="highlight-list">
                <li v-for="(highlight, index) in deepAnalysisData.highlights" :key="index">
                  <el-icon color="#67C23A"><SuccessFilled /></el-icon>
                  <span>{{ highlight }}</span>
                </li>
              </ul>
            </div>
          </el-col>

          <!-- 主要风险 -->
          <el-col :span="12" v-if="deepAnalysisData.risks && deepAnalysisData.risks.length > 0">
            <div class="summary-section">
              <h4>主要风险</h4>
              <ul class="risk-list">
                <li v-for="(risk, index) in deepAnalysisData.risks" :key="index">
                  <el-icon color="#F56C6C"><WarningFilled /></el-icon>
                  <span>{{ risk }}</span>
                </li>
              </ul>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 分隔线 -->
      <el-divider style="margin: 20px 0;" />

      <!-- 会世元丰CTA2号 (L03092): 两个独立图表 -->
      <el-row :gutter="24" v-loading="sectorChartLoading" v-if="selectedFundCode === 'L03092'">
        <el-col :span="12">
          <div class="chart-title">板块持仓配置（堆叠）</div>
          <div ref="allocationChartRef" style="width: 100%; height: 450px;"></div>
        </el-col>
        <el-col :span="12">
          <div class="chart-title">板块收益贡献（堆叠）</div>
          <div ref="returnChartRef" style="width: 100%; height: 450px;"></div>
        </el-col>
      </el-row>

      <!-- 磐泽多策略 (L02798): 多空配置图 -->
      <div v-loading="sectorChartLoading" v-if="selectedFundCode === 'L02798'">
        <div class="chart-title">各月行业配置多空结构 (2025年1月—2026年2月)</div>
        <div class="chart-subtitle">正值=多头 负值=空头</div>
        <div ref="longShortChartRef" style="width: 100%; height: 500px;"></div>
      </div>

      <!-- 国源恰金2号 (L03143): 多空配置图 -->
      <div v-loading="sectorChartLoading" v-if="selectedFundCode === 'L03143'">
        <div class="chart-title">各月行业配置结构 (2025年10月—2026年2月)</div>
        <div class="chart-subtitle">包含现金管理工具及期货对冲</div>
        <div ref="longShortChartRef" style="width: 100%; height: 500px;"></div>
      </div>
    </el-card>

    </div>
    <!-- 导出内容区域结束 -->

    <!-- 空状态 -->
    <el-empty v-if="!analysisData && !loading" description="请选择产品进行分析" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { SuccessFilled, WarningFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import html2canvas from 'html2canvas'
import { fetchMultipleBenchmarks } from '@/utils/benchmarkData'

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8003'

const loading = ref(false)
const downloadLoading = ref(false)
const selectedFundCode = ref('')
const selectedBenchmark = ref('')
const fundList = ref([])
const analysisData = ref(null)
const benchmarkData = ref(null)
const navChartRef = ref(null)
const monthlyReturnChartRef = ref(null)
const allocationChartRef = ref(null)  // 板块持仓配置图表引用
const returnChartRef = ref(null)  // 板块收益贡献图表引用
const longShortChartRef = ref(null)  // 多空配置图表引用
const exportContentRef = ref(null)  // 用于图片导出的内容区域
let navChart = null
let monthlyReturnChart = null
let allocationChart = null  // 板块持仓配置图表实例
let returnChart = null  // 板块收益贡献图表实例
let longShortChart = null  // 多空配置图表实例

// 新增：产品深度分析数据
const deepAnalysisData = ref({
  exists: false,
  highlights: [],
  risks: [],
  strategy_description: '',
  analysis_period: null
})

// 新增：行业配置数据
const sectorAllocationData = ref([])
const sectorChartLoading = ref(false)

// 指数名称映射
const indexNameMap = {
  '000300.SH': '沪深300',
  '000905.SH': '中证500',
  '000852.SH': '中证1000',
  '932000.CSI': '中证2000',
  '000906.SH': '中证800',
  '000001.SH': '上证指数'
}

onMounted(() => {
  loadFundList()
})

const loadFundList = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/nav/funds`)
    fundList.value = response.data.data.funds
  } catch (error) {
    ElMessage.error('加载产品列表失败')
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${year}年${month}月${day}日`
}

const loadProductAnalysis = async () => {
  if (!selectedFundCode.value) {
    ElMessage.warning('请选择产品')
    return
  }

  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/product-analysis/${selectedFundCode.value}`)
    analysisData.value = response.data.data

    // 如果选择了基准，获取基准数据
    if (selectedBenchmark.value) {
      const indexDataMap = await fetchMultipleBenchmarks([selectedBenchmark.value])
      benchmarkData.value = indexDataMap[selectedBenchmark.value] || []
    } else {
      benchmarkData.value = null
    }

    await nextTick()
    renderNavChart()
    renderMonthlyReturnChart()

    // 新增：加载产品深度分析数据
    await loadDeepAnalysisData(selectedFundCode.value)

    ElMessage.success('分析完成')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '分析失败')
  } finally {
    loading.value = false
  }
}

const renderNavChart = () => {
  if (!navChartRef.value || !analysisData.value) return

  if (navChart) {
    navChart.dispose()
  }

  navChart = echarts.init(navChartRef.value)

  // 准备图例数据
  const legendData = ['净值', '回撤']

  // 如果有基准数据，添加到图例
  if (benchmarkData.value && benchmarkData.value.length > 0) {
    const benchmarkName = indexNameMap[selectedBenchmark.value] || selectedBenchmark.value
    legendData.splice(1, 0, benchmarkName + '(归一)')
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params) => {
        let result = `<div style="margin-bottom: 5px; font-weight: 600;">${params[0].axisValue}</div>`
        params.forEach(param => {
          if (param.value !== null && param.value !== undefined) {
            const value = Number(param.value).toFixed(2)
            // 如果是回撤数据，添加%符号
            const suffix = param.seriesName === '回撤' ? '%' : ''
            result += `<div>${param.marker} ${param.seriesName}: <span style="font-weight: 600;">${value}${suffix}</span></div>`
          }
        })
        return result
      }
    },
    legend: {
      data: legendData
    },
    grid: [
      {
        left: '3%',
        right: '4%',
        top: '5%',
        height: '35%'
      },
      {
        left: '3%',
        right: '4%',
        top: '60%',
        height: '35%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: analysisData.value.nav_curve.dates,
        gridIndex: 0
      },
      {
        type: 'category',
        data: analysisData.value.nav_curve.dates,
        gridIndex: 1,
        position: 'top',
        axisLine: { onZero: false }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '净值',
        gridIndex: 0,
        min: (value) => {
          // 动态计算最小值，确保从合理位置开始
          const minVal = Math.floor(value.min * 10) / 10
          return Math.max(0.4, minVal - 0.1)
        },
        scale: true,
        axisLabel: {
          formatter: (value) => value.toFixed(1)
        }
      },
      {
        type: 'value',
        name: '回撤(%)',
        gridIndex: 1,
        max: 0,
        nameGap: 35,
        axisLabel: {
          formatter: '{value}%'
        }
      }
    ],
    series: [
      {
        name: '净值',
        type: 'line',
        data: analysisData.value.nav_curve.values,
        smooth: true,
        symbol: 'none',
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: '回撤',
        type: 'line',
        data: analysisData.value.nav_curve.drawdowns,
        smooth: true,
        symbol: 'none',
        xAxisIndex: 1,
        yAxisIndex: 1,
        areaStyle: {
          color: '#67C23A',
          opacity: 0.3
        },
        itemStyle: {
          color: '#67C23A'
        },
        lineStyle: {
          color: '#67C23A'
        }
      }
    ]
  }

  // 如果有基准数据，添加基准曲线（归一化）
  if (benchmarkData.value && benchmarkData.value.length > 0) {
    const benchmarkName = indexNameMap[selectedBenchmark.value] || selectedBenchmark.value

    // 创建日期到基准值的映射
    const benchmarkMap = {}
    benchmarkData.value.forEach(item => {
      benchmarkMap[item.date] = item.value
    })

    // 获取产品净值的日期和值
    const productDates = analysisData.value.nav_curve.dates
    const productNavs = analysisData.value.nav_curve.values

    // 找到第一个有基准数据的日期
    let firstDate = null
    let firstBenchmarkValue = null
    let firstProductNav = null

    for (let i = 0; i < productDates.length; i++) {
      if (benchmarkMap[productDates[i]]) {
        firstDate = productDates[i]
        firstBenchmarkValue = benchmarkMap[productDates[i]]
        firstProductNav = productNavs[i]
        break
      }
    }

    // 如果找到了起点，进行归一化
    if (firstDate && firstBenchmarkValue && firstProductNav) {
      const normalizedBenchmark = productDates.map(date => {
        if (benchmarkMap[date]) {
          // 归一化：(当前基准值 / 起点基准值) * 起点产品净值
          return (benchmarkMap[date] / firstBenchmarkValue) * firstProductNav
        }
        return null
      })

      // 添加基准曲线到series
      option.series.splice(1, 0, {
        name: benchmarkName + '(归一)',
        type: 'line',
        data: normalizedBenchmark,
        smooth: true,
        symbol: 'none',
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#E6A23C'
        },
        lineStyle: {
          width: 2,
          type: 'dashed'
        }
      })
    }
  }

  navChart.setOption(option)
}

const renderMonthlyReturnChart = () => {
  if (!monthlyReturnChartRef.value || !analysisData.value) return

  if (monthlyReturnChart) {
    monthlyReturnChart.dispose()
  }

  monthlyReturnChart = echarts.init(monthlyReturnChartRef.value)

  const monthlyData = analysisData.value.monthly_returns.returns
  const colors = monthlyData.returns.map(val => val >= 0 ? '#F56C6C' : '#67C23A')

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const value = params[0].value
        return `${params[0].axisValue}<br/>收益率: ${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: monthlyData.months,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '收益率(%)',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '月度收益',
        type: 'bar',
        data: monthlyData.returns,
        itemStyle: {
          color: (params) => {
            return params.value >= 0 ? '#F56C6C' : '#67C23A'
          }
        }
      }
    ]
  }

  monthlyReturnChart.setOption(option)
}

// 下载为图片
const downloadPDF = async () => {
  if (!exportContentRef.value || !analysisData.value) {
    ElMessage.warning('暂无分析数据')
    return
  }

  downloadLoading.value = true
  const loadingInstance = ElLoading.service({
    lock: true,
    text: '正在生成图片...',
    background: 'rgba(0, 0, 0, 0.7)'
  })

  try {
    await nextTick()

    // 等待所有图表渲染完成
    await new Promise(resolve => setTimeout(resolve, 500))

    // 临时设置导出区域的宽度为足够大，确保内容不被截断
    const originalWidth = exportContentRef.value.style.width
    const originalMinWidth = exportContentRef.value.style.minWidth
    exportContentRef.value.style.width = '1600px'
    exportContentRef.value.style.minWidth = '1600px'

    // 等待DOM更新
    await nextTick()

    // 重新调整图表大小以适应新宽度
    if (navChart) {
      navChart.resize()
    }
    if (monthlyReturnChart) {
      monthlyReturnChart.resize()
    }

    await new Promise(resolve => setTimeout(resolve, 300))

    // 使用html2canvas截取内容
    const canvas = await html2canvas(exportContentRef.value, {
      scale: 2, // 适当降低以控制文件大小，但保证清晰度
      useCORS: true,
      logging: false,
      backgroundColor: '#f5f5f5',
      width: 1600,
      height: exportContentRef.value.scrollHeight,
      x: 0,
      y: 0
    })

    // 恢复原始宽度
    exportContentRef.value.style.width = originalWidth
    exportContentRef.value.style.minWidth = originalMinWidth

    // 恢复图表大小
    await nextTick()
    if (navChart) {
      navChart.resize()
    }
    if (monthlyReturnChart) {
      monthlyReturnChart.resize()
    }

    // 转换为图片并下载
    canvas.toBlob((blob) => {
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      const fileName = `${analysisData.value.fund_code}-${analysisData.value.short_name}-分析报告-${new Date().toISOString().split('T')[0]}.png`
      link.href = url
      link.download = fileName
      link.click()
      URL.revokeObjectURL(url)

      ElMessage.success('图片已下载')
    }, 'image/png', 1.0)

  } catch (error) {
    console.error('生成图片失败:', error)
    ElMessage.error('生成图片失败，请重试')
  } finally {
    downloadLoading.value = false
    loadingInstance.close()
  }
}

// 新增：加载产品深度分析数据
const loadDeepAnalysisData = async (productCode) => {
  try {
    console.log('开始加载产品深度分析数据:', productCode)

    // 1. 获取分析摘要
    const summaryResponse = await axios.get(`${API_BASE}/api/product-deep-analysis/${productCode}/analysis-summary`)
    const summaryData = summaryResponse.data

    if (summaryData.exists) {
      deepAnalysisData.value = summaryData
      console.log('分析摘要加载成功:', summaryData)

      // 2. 获取行业配置数据
      const allocationResponse = await axios.get(`${API_BASE}/api/product-deep-analysis/${productCode}/sector-allocation`)
      const allocationData = allocationResponse.data

      if (allocationData.data && allocationData.data.length > 0) {
        sectorAllocationData.value = allocationData.data
        console.log('行业配置数据加载成功，共', allocationData.total_months, '个月')

        // 3. 根据产品代码绘制不同类型的图表
        await nextTick()
        if (productCode === 'L03092') {
          // 会世元丰CTA2号：两个独立图表
          await drawAllocationAndReturnCharts()
        } else if (productCode === 'L02798') {
          // 磐泽多策略：多空配置图
          await drawLongShortChart()
        } else if (productCode === 'L03143') {
          // 国源恰金2号：多空配置图
          await drawLongShortChart()
        }
      } else {
        console.log('该产品暂无行业配置数据')
      }
    } else {
      deepAnalysisData.value.exists = false
      console.log('该产品暂无深度分析数据')
    }
  } catch (error) {
    console.error('加载产品深度分析数据失败:', error)
    deepAnalysisData.value.exists = false
  }
}

// 新增：绘制板块持仓配置和收益贡献两个图表
const drawAllocationAndReturnCharts = async () => {
  if (!allocationChartRef.value || !returnChartRef.value || !sectorAllocationData.value.length) {
    console.warn('无法绘制图表：缺少容器或数据')
    return
  }

  sectorChartLoading.value = true

  try {
    // 准备数据
    const months = []
    const monthLabels = []  // 显示用的月份标签 (8月, 9月...)
    const sectorsMap = new Map()

    // 遍历所有月份数据
    for (const monthData of sectorAllocationData.value) {
      months.push(monthData.month)
      // 从 "2025-08" 提取 "8月"
      const monthNum = monthData.month.split('-')[1]
      monthLabels.push(`${parseInt(monthNum)}月`)

      // 处理多头仓位
      for (const longPos of monthData.long_positions) {
        if (!sectorsMap.has(longPos.sector_name)) {
          sectorsMap.set(longPos.sector_name, { type: 'long', allocationData: [], returnData: [] })
        }
        sectorsMap.get(longPos.sector_name).allocationData.push(longPos.allocation_pct)
      }

      // 补齐缺失数据
      for (const [sectorName, sectorInfo] of sectorsMap.entries()) {
        while (sectorInfo.allocationData.length < months.length) {
          sectorInfo.allocationData.push(0)
        }
      }
    }

    // 定义板块颜色映射（CTA产品板块）
    const sectorColors = {
      '豆脂饲料': '#e74c3c',
      '股指期货': '#3498db',
      '能源化工': '#2ecc71',
      '工业金属': '#f39c12',
      '黑色系': '#9b59b6',
      '软商品': '#1abc9c',
      '贵金属': '#e67e22',
      '国债期货': '#95a5a6'
    }

    // ========== 图表1: 板块持仓配置（堆叠） ==========
    if (allocationChart) {
      allocationChart.dispose()
    }
    allocationChart = echarts.init(allocationChartRef.value)

    const allocationSeries = []
    for (const [sectorName, sectorInfo] of sectorsMap.entries()) {
      allocationSeries.push({
        name: sectorName,
        type: 'bar',
        stack: 'total',
        data: sectorInfo.allocationData,
        itemStyle: { color: sectorColors[sectorName] || '#5470C6' },
        label: {
          show: false  // 不显示每个分段的标签，避免太拥挤
        }
      })
    }

    const allocationOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          let result = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>`
          params.forEach(item => {
            if (item.value > 0) {
              result += `<div>${item.marker} ${item.seriesName}: ${item.value.toFixed(1)}%</div>`
            }
          })
          return result
        }
      },
      legend: {
        bottom: 5,
        type: 'scroll',
        orient: 'horizontal',
        pageIconSize: 10,
        textStyle: { fontSize: 11 },
        data: allocationSeries.map(s => s.name)
      },
      grid: {
        left: '8%',
        right: '5%',
        top: '10px',
        bottom: '60px',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: monthLabels,
        axisLabel: { fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        name: '配置比例(%)',
        max: 100,
        axisLabel: { formatter: '{value}%', fontSize: 10 },
        splitLine: { lineStyle: { type: 'dashed' } }
      },
      series: allocationSeries
    }

    allocationChart.setOption(allocationOption)

    // ========== 图表2: 板块收益贡献（堆叠） ==========
    // 模拟收益数据（实际应该从后端获取）
    const returnDataMock = {
      '股指期货': [1.86, -0.75, -0.71, -0.38, 0.47, 0.56],
      '贵金属': [-0.06, 1.34, 0.74, 0.67, 2.42, 2.57],
      '豆脂饲料': [0.67, -0.69, -0.05, 0.58, -0.83, 0.30],
      '能源化工': [-0.55, 0.17, 0.71, 0.42, 0.87, -0.58],
      '工业金属': [0.18, -0.30, 0.30, 0.93, 1.10, 0.36],
      '黑色系': [0.16, -0.45, 0.06, 0.51, 0.27, -0.24],
      '软商品': [0.38, 0.25, 0.01, -0.03, 0.37, 0.03],
      '国债期货': [-0.38, -0.29, 0.24, -0.17, 0.05, 0.06]
    }

    if (returnChart) {
      returnChart.dispose()
    }
    returnChart = echarts.init(returnChartRef.value)

    // 计算月度总收益
    const monthlyTotals = []
    for (let i = 0; i < months.length; i++) {
      let total = 0
      for (const sector in returnDataMock) {
        total += returnDataMock[sector][i]
      }
      monthlyTotals.push(total)
    }

    const returnSeries = []
    for (const [sectorName, returnData] of Object.entries(returnDataMock)) {
      returnSeries.push({
        name: sectorName,
        type: 'bar',
        stack: 'total',
        data: returnData,
        itemStyle: { color: sectorColors[sectorName] || '#5470C6' }
      })
    }

    const returnOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          let result = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>`
          let positiveItems = []
          let negativeItems = []

          params.forEach(item => {
            if (item.value > 0) {
              positiveItems.push(item)
            } else if (item.value < 0) {
              negativeItems.push(item)
            }
          })

          if (positiveItems.length > 0) {
            result += '<div style="color: #f56c6c; font-weight: bold; margin-top: 5px;">● 正贡献</div>'
            positiveItems.forEach(item => {
              result += `<div>${item.marker} ${item.seriesName}: +${item.value.toFixed(2)}%</div>`
            })
          }

          if (negativeItems.length > 0) {
            result += '<div style="color: #67c23a; font-weight: bold; margin-top: 5px;">● 负贡献</div>'
            negativeItems.forEach(item => {
              result += `<div>${item.marker} ${item.seriesName}: ${item.value.toFixed(2)}%</div>`
            })
          }

          return result
        }
      },
      legend: {
        bottom: 5,
        type: 'scroll',
        orient: 'horizontal',
        pageIconSize: 10,
        textStyle: { fontSize: 11 },
        data: returnSeries.map(s => s.name)
      },
      grid: {
        left: '8%',
        right: '5%',
        top: '10px',
        bottom: '60px',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: monthLabels,
        axisLabel: { fontSize: 11 }
      },
      yAxis: {
        type: 'value',
        name: '收益贡献(%)',
        axisLabel: { formatter: '{value}%', fontSize: 10 },
        splitLine: { lineStyle: { type: 'dashed' } }
      },
      series: returnSeries
    }

    returnChart.setOption(returnOption)

    // 在图表上方添加月度总收益标注
    returnOption.series.push({
      name: '月度总收益',
      type: 'line',
      data: monthlyTotals,
      symbol: 'none',
      lineStyle: { width: 0 },
      label: {
        show: true,
        position: monthlyTotals.map(v => v >= 0 ? 'top' : 'bottom'),
        formatter: function(params) {
          const value = params.value
          return value >= 0 ? `+${value.toFixed(2)}%` : `${value.toFixed(2)}%`
        },
        fontSize: 11,
        fontWeight: 'bold',
        color: '#000',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        padding: [2, 4],
        borderRadius: 3
      },
      z: 10
    })
    returnChart.setOption(returnOption)

    console.log('板块配置和收益图表绘制完成')
  } catch (error) {
    console.error('绘制图表失败:', error)
  } finally {
    sectorChartLoading.value = false
  }
}

// 新增：绘制磐泽多策略多空配置图
const drawLongShortChart = async () => {
  if (!longShortChartRef.value || !sectorAllocationData.value.length) {
    console.warn('无法绘制多空配置图：缺少容器或数据')
    return
  }

  sectorChartLoading.value = true

  try {
    // 准备数据
    const months = []
    const monthLabels = []
    const sectorsMap = new Map()

    // 第一遍：收集所有板块名称
    for (const monthData of sectorAllocationData.value) {
      for (const longPos of monthData.long_positions) {
        if (!sectorsMap.has(longPos.sector_name)) {
          sectorsMap.set(longPos.sector_name, { longData: [], shortData: [] })
        }
      }
      for (const shortPos of monthData.short_positions) {
        if (!sectorsMap.has(shortPos.sector_name)) {
          sectorsMap.set(shortPos.sector_name, { longData: [], shortData: [] })
        }
      }
    }

    // 第二遍：按月份填充数据
    for (const monthData of sectorAllocationData.value) {
      months.push(monthData.month)
      const [year, month] = monthData.month.split('-')
      monthLabels.push(`${year}-${month}`)

      // 创建当前月份的数据映射
      const currentMonthLong = {}
      const currentMonthShort = {}

      for (const longPos of monthData.long_positions) {
        currentMonthLong[longPos.sector_name] = longPos.allocation_pct
      }
      for (const shortPos of monthData.short_positions) {
        currentMonthShort[shortPos.sector_name] = -shortPos.allocation_pct
      }

      // 为所有板块填充当前月份的数据
      for (const [sectorName, sectorInfo] of sectorsMap.entries()) {
        sectorInfo.longData.push(currentMonthLong[sectorName] || 0)
        sectorInfo.shortData.push(currentMonthShort[sectorName] || 0)
      }
    }

    // 定义板块颜色映射（股票行业）
    const sectorColors = {
      '信息技术': '#4169E1',
      '金融': '#F4A460',
      '可选消费': '#CD853F',
      '可选消费(空)': '#CD853F',
      '材料': '#5F9EA0',
      '能源': '#87CEEB',
      '公用事业': '#B0C4DE',
      '公用事业(空)': '#B0C4DE',
      '房地产': '#FF6347',
      '指数(空)': '#FFA07A',
      '金属(空)': '#FFB6C1',
      '半导体': '#9370DB',
      // L03143专用颜色
      '现金管理工具': '#E8E8E8',
      '有色金属': '#DAA520',
      '汽车': '#FF6B6B',
      '电力设备': '#4ECDC4',
      '电子': '#556FB5',
      '家用电器': '#95E1D3',
      '基础化工': '#F38181',
      '期货-有色金属': '#DAA520',
      '社会服务': '#AA96DA',
      '其他': '#FCBAD3',
      '医药生物': '#A8E6CF',
      '电池': '#FFD93D',
      '非银金融': '#6BCB77',
      '农林牧渔': '#C7CEEA',
      '商贸零售': '#FFEAA7',
      '石油石化': '#74B9FF',
      '期货-化工': '#F38181',
      '科技': '#A29BFE'
    }

    // 创建多空配置图
    if (longShortChart) {
      longShortChart.dispose()
    }
    longShortChart = echarts.init(longShortChartRef.value)

    const series = []

    // 添加多头series（正值，实心）
    for (const [sectorName, sectorInfo] of sectorsMap.entries()) {
      if (sectorInfo.longData.some(v => v > 0)) {
        series.push({
          name: sectorName,
          type: 'bar',
          stack: 'total',
          data: sectorInfo.longData,
          itemStyle: {
            color: sectorColors[sectorName] || '#5470C6'
          }
        })
      }
    }

    // 添加空头series（负值，带斜纹）
    for (const [sectorName, sectorInfo] of sectorsMap.entries()) {
      if (sectorInfo.shortData.some(v => v < 0)) {
        const shortName = sectorName + '(空)'
        series.push({
          name: shortName,
          type: 'bar',
          stack: 'total',
          data: sectorInfo.shortData,
          itemStyle: {
            color: {
              type: 'pattern',
              image: createHatchPattern(sectorColors[sectorName] || '#5470C6'),
              repeat: 'repeat'
            }
          }
        })
      }
    }

    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function(params) {
          let result = `<div style="font-weight: bold; margin-bottom: 5px;">${params[0].axisValue}</div>`

          // 分组显示：多头 vs 空头
          let longItems = []
          let shortItems = []

          params.forEach(item => {
            if (item.value > 0) {
              longItems.push(item)
            } else if (item.value < 0) {
              shortItems.push(item)
            }
          })

          if (longItems.length > 0) {
            result += '<div style="color: #4169E1; font-weight: bold; margin-top: 5px;">● 多头</div>'
            longItems.forEach(item => {
              result += `<div>${item.marker} ${item.seriesName}: ${item.value.toFixed(1)}%</div>`
            })
          }

          if (shortItems.length > 0) {
            result += '<div style="color: #FF6347; font-weight: bold; margin-top: 5px;">● 空头</div>'
            shortItems.forEach(item => {
              result += `<div>${item.marker} ${item.seriesName}: ${Math.abs(item.value).toFixed(1)}%</div>`
            })
          }

          return result
        }
      },
      legend: {
        bottom: 10,
        type: 'scroll',
        orient: 'horizontal',
        pageIconSize: 10,
        textStyle: { fontSize: 11 },
        data: series.map(s => s.name)
      },
      grid: {
        left: '5%',
        right: '5%',
        top: '40px',
        bottom: '80px',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: monthLabels,
        axisLabel: {
          fontSize: 11,
          rotate: 0
        }
      },
      yAxis: {
        type: 'value',
        name: '配置比例(%)',
        axisLabel: { formatter: '{value}%', fontSize: 10 },
        splitLine: { lineStyle: { type: 'dashed' } }
      },
      series: series
    }

    longShortChart.setOption(option)
    console.log('多空配置图绘制完成')
  } catch (error) {
    console.error('绘制多空配置图失败:', error)
  } finally {
    sectorChartLoading.value = false
  }
}

// 辅助函数：创建斜纹图案
function createHatchPattern(color) {
  const canvas = document.createElement('canvas')
  canvas.width = 10
  canvas.height = 10
  const ctx = canvas.getContext('2d')

  ctx.strokeStyle = color
  ctx.lineWidth = 2

  // 绘制斜纹
  ctx.beginPath()
  ctx.moveTo(0, 10)
  ctx.lineTo(10, 0)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(-2, 2)
  ctx.lineTo(2, -2)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(8, 12)
  ctx.lineTo(12, 8)
  ctx.stroke()

  return canvas
}
</script>

<style scoped>
.product-analysis {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.page-description {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.filter-section {
  margin-bottom: 24px;
}

/* 导出内容区域样式 */
.export-content {
  background-color: #f5f5f5;
  padding: 20px;
}

.product-info-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 24px 32px;
  margin-bottom: 24px;
  color: white;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.25);
}

.product-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.product-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: white;
  letter-spacing: 0.5px;
}

.product-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strategy-tag {
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
  backdrop-filter: blur(10px);
}

.strategy-divider {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 300;
}

.analysis-period {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 400;
  letter-spacing: 0.3px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
}

.chart-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 15px;
  text-align: center;
}

.chart-subtitle {
  font-size: 12px;
  color: #909399;
  margin-bottom: 10px;
  text-align: center;
}

.monthly-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.monthly-stats {
  padding: 20px;
}

.mini-stat {
  text-align: center;
  padding: 10px 0;
}

.mini-stat .label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.mini-stat .value {
  font-size: 20px;
  font-weight: 600;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.mini-stat .value.positive {
  color: #f56c6c;
}

.mini-stat .value.negative {
  color: #67c23a;
}

.risk-item {
  text-align: center;
  padding: 20px;
  background-color: #f9fafb;
  border-radius: 8px;
}

.risk-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.risk-value {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.percent-text {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

.recovery-item {
  text-align: center;
  padding: 20px;
}

.recovery-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
  font-weight: 500;
}

.recovery-value {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
  margin-bottom: 8px;
}

.recovery-date {
  font-size: 13px;
  color: #9ca3af;
}

.recovery-description {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  text-align: left;
  padding: 10px 0;
}

.compact-analysis {
  margin-bottom: 16px;
}

.recovery-item-compact {
  text-align: center;
  padding: 10px 5px;
}

.recovery-label-compact {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
  font-weight: 500;
}

.recovery-value-compact {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
  margin-bottom: 4px;
}

.recovery-date-compact {
  font-size: 11px;
  color: #9ca3af;
}

.recovery-description-compact {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.5;
  text-align: left;
  padding: 5px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recovery-description-section {
  padding: 10px 15px;
  background-color: #f9fafb;
  border-radius: 6px;
}

/* 产品深度分析样式 */
.deep-analysis-card {
  margin-bottom: 20px;
}

.analysis-period-sub {
  font-size: 13px;
  color: #909399;
  font-weight: normal;
}

.analysis-summary-horizontal {
  padding: 10px 0;
}

.analysis-summary {
  padding: 10px;
}

.summary-section {
  margin-bottom: 20px;
}

.summary-section h4 {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 3px solid #409EFF;
}

.strategy-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  padding: 10px;
  background: #F5F7FA;
  border-radius: 4px;
}

.highlight-list,
.risk-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.highlight-list li,
.risk-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.highlight-list li .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.risk-list li .el-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.sector-chart-container {
  height: 600px;
  width: 100%;
  margin-top: 10px;
}

.sector-chart {
  width: 100%;
  height: 100%;
}

.recovery-description-full {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.7;
  text-align: left;
  margin-top: 8px;
}
</style>
