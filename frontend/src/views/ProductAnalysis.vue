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
const exportContentRef = ref(null)  // 用于图片导出的内容区域
let navChart = null
let monthlyReturnChart = null

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

.recovery-description-full {
  font-size: 12px;
  color: #4b5563;
  line-height: 1.7;
  text-align: left;
  margin-top: 8px;
}
</style>
