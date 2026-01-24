<template>
  <div class="portfolio-backtest-container">
    <!-- 已保存组合列表卡片 -->
    <el-card class="saved-portfolios-card">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-icon><FolderOpened /></el-icon>
            <span>已保存的组合</span>
            <span v-if="savedPortfolios.length > 0" class="portfolio-count">({{ savedPortfolios.length }}个)</span>
          </div>
        </div>
      </template>
      <div v-if="savedPortfolios.length > 0" class="saved-portfolios-list">
        <el-tag
          v-for="portfolio in savedPortfolios"
          :key="portfolio.id"
          type="info"
          closable
          @close="deletePortfolioConfirm(portfolio)"
          @click="loadPortfolio(portfolio.id)"
          class="portfolio-tag"
        >
          <el-icon><Folder /></el-icon>
          {{ portfolio.portfolio_name }} ({{ portfolio.product_count }}个产品)
        </el-tag>
      </div>
      <div v-else class="empty-portfolios">
        <el-text type="info">暂无保存的组合，配置组合后点击「保存组合」按钮即可保存</el-text>
      </div>
    </el-card>

    <!-- 操作栏和组合构建区域 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <div style="display: flex; align-items: center; gap: 16px;">
            <span>组合回测系统</span>
            <el-input
              v-model="portfolioName"
              placeholder="输入组合名称"
              style="width: 200px"
              clearable
            />
          </div>
          <el-button-group>
            <el-button
              type="success"
              :disabled="portfolioItems.length === 0 || !portfolioName || portfolioName.trim() === ''"
              @click="savePortfolio"
            >
              <el-icon><DocumentAdd /></el-icon>
              保存组合
            </el-button>
            <el-button type="primary" :disabled="portfolioItems.length === 0" @click="runBacktest">
              <el-icon><DataAnalysis /></el-icon>
              开始回测
            </el-button>
            <el-button @click="resetPortfolio">
              <el-icon><RefreshRight /></el-icon>
              重置
            </el-button>
          </el-button-group>
        </div>
      </template>

      <!-- 组合构建区域 -->
      <div class="portfolio-builder">
        <el-row :gutter="20">
          <!-- 左侧：产品选择 -->
          <el-col :span="12">
            <div class="section-title">
              <el-icon><Menu /></el-icon>
              <span>产品选择</span>
            </div>

            <el-form label-width="120px">
              <el-form-item label="选择产品">
                <el-select
                  v-model="selectedFundCode"
                  filterable
                  remote
                  reserve-keyword
                  placeholder="输入基金代码或名称搜索"
                  :remote-method="searchFunds"
                  :loading="fundSearchLoading"
                  style="width: 100%"
                  @change="addFundToPortfolio"
                >
                  <el-option
                    v-for="fund in fundList"
                    :key="fund.fund_code"
                    :label="`${fund.fund_code} - ${fund.fund_name}`"
                    :value="fund.fund_code"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="配置方式">
                <el-radio-group v-model="weightMode">
                  <el-radio value="weight">按权重</el-radio>
                  <el-radio value="amount">按金额</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>

            <!-- 组合列表 -->
            <el-table
              :data="portfolioItems"
              border
              style="width: 100%; margin-top: 10px"
              max-height="400"
            >
              <el-table-column prop="fund_code" label="基金代码" width="120" />
              <el-table-column prop="fund_name" label="基金名称" min-width="180" />
              <el-table-column label="权重/金额" width="180">
                <template #default="{ row }">
                  <el-input-number
                    v-if="weightMode === 'weight'"
                    v-model="row.weight"
                    :min="0"
                    :max="100"
                    :precision="2"
                    size="small"
                    style="width: 140px"
                    @change="normalizeWeights"
                  >
                    <template #append>%</template>
                  </el-input-number>
                  <el-input-number
                    v-else
                    v-model="row.amount"
                    :min="0"
                    :precision="2"
                    size="small"
                    style="width: 140px"
                  >
                    <template #append>万元</template>
                  </el-input-number>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" fixed="right">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeFromPortfolio($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="weightMode === 'weight' && portfolioItems.length > 0" class="weight-summary">
              <el-tag :type="totalWeight === 100 ? 'success' : 'warning'">
                总权重：{{ totalWeight.toFixed(2) }}%
                <span v-if="totalWeight !== 100"> (需要等于100%)</span>
              </el-tag>
            </div>
          </el-col>

          <!-- 右侧：回测参数 -->
          <el-col :span="12">
            <div class="section-title">
              <el-icon><Setting /></el-icon>
              <span>回测参数</span>
            </div>

            <el-form :model="backtestParams" label-width="140px">
              <el-form-item label="初始资金">
                <el-input-number
                  v-model="backtestParams.initialCapital"
                  :min="10"
                  :step="100"
                  :precision="2"
                  style="width: 100%"
                >
                  <template #append>万元</template>
                </el-input-number>
              </el-form-item>

              <el-form-item label="回测范围">
                <el-date-picker
                  v-model="backtestParams.startDate"
                  type="date"
                  placeholder="期初日期"
                  value-format="YYYY-MM-DD"
                  style="width: 48%; margin-right: 4%"
                />
                <el-date-picker
                  v-model="backtestParams.endDate"
                  type="date"
                  placeholder="期末日期"
                  value-format="YYYY-MM-DD"
                  style="width: 48%"
                />
              </el-form-item>

              <el-form-item label="对比基准">
                <el-select v-model="backtestParams.benchmark" placeholder="选择基准指数" style="width: 100%" clearable>
                  <el-option label="无" value="" />
                  <el-option label="沪深300" value="000300" />
                  <el-option label="中证500" value="000905" />
                  <el-option label="上证指数" value="000001" />
                  <el-option label="创业板指" value="399006" />
                  <el-option label="恒生指数" value="HSI" />
                </el-select>
              </el-form-item>
            </el-form>

            <!-- 快捷设置 -->
            <div class="quick-settings">
              <div class="section-subtitle">快捷时间设置</div>
              <el-space wrap>
                <el-button size="small" @click="setDateRange(365)">近1年</el-button>
                <el-button size="small" @click="setDateRange(365 * 2)">近2年</el-button>
                <el-button size="small" @click="setDateRange(365 * 3)">近3年</el-button>
                <el-button size="small" @click="setDateRange(365 * 5)">近5年</el-button>
                <el-button size="small" @click="setDateRange(0)">全部时间</el-button>
                <el-button size="small" @click="setEndDateToday">今天</el-button>
              </el-space>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 回测结果区域 -->
    <el-card v-if="backtestResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>回测结果</span>
          <el-button type="primary" @click="exportReport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </template>

      <!-- 持仓信息 -->
      <div class="position-info-section">
        <div class="section-title">
          <el-icon><Wallet /></el-icon>
          <span>持仓信息</span>
          <span v-if="backtestParams.startDate && backtestParams.endDate" class="backtest-period">
            （回测时间：{{ backtestParams.startDate }} 至 {{ backtestParams.endDate }}）
          </span>
        </div>
        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="持仓成本" :precision="2" suffix="万元" :value="backtestResult.positionInfo.cost">
              <template #prefix>
                <el-icon style="color: #909399">
                  <Money />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="持仓市值" :precision="2" suffix="万元" :value="backtestResult.positionInfo.marketValue">
              <template #prefix>
                <el-icon style="color: #409EFF">
                  <Coin />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="持仓收益" :precision="2" suffix="万元" :value="backtestResult.positionInfo.profit">
              <template #prefix>
                <el-icon :style="{ color: backtestResult.positionInfo.profit >= 0 ? '#F56C6C' : '#67C23A' }">
                  <CaretTop v-if="backtestResult.positionInfo.profit >= 0" />
                  <CaretBottom v-else />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="持仓收益率" :precision="2" suffix="%" :value="backtestResult.positionInfo.profitRate * 100">
              <template #prefix>
                <el-icon :style="{ color: backtestResult.positionInfo.profitRate >= 0 ? '#F56C6C' : '#67C23A' }">
                  <TrendCharts />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <!-- 核心指标 -->
      <div class="metrics-grid">
        <div class="section-title">
          <el-icon><DataAnalysis /></el-icon>
          <span>核心指标</span>
        </div>
        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="6">
            <el-statistic title="累计收益率" :precision="2" suffix="%" :value="backtestResult.metrics.totalReturn * 100">
              <template #prefix>
                <el-icon :style="{ color: backtestResult.metrics.totalReturn >= 0 ? '#F56C6C' : '#67C23A' }">
                  <CaretTop v-if="backtestResult.metrics.totalReturn >= 0" />
                  <CaretBottom v-else />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="年化收益率" :precision="2" suffix="%" :value="backtestResult.metrics.annualizedReturn * 100">
              <template #prefix>
                <el-icon :style="{ color: backtestResult.metrics.annualizedReturn >= 0 ? '#F56C6C' : '#67C23A' }">
                  <TrendCharts />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="年化波动率" :precision="2" suffix="%" :value="backtestResult.metrics.annualizedVolatility * 100">
              <template #prefix>
                <el-icon style="color: #E6A23C">
                  <Orange />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="最大回撤" :precision="2" suffix="%" :value="backtestResult.metrics.maxDrawdown * 100">
              <template #prefix>
                <el-icon style="color: #67C23A">
                  <Bottom />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>

        <el-divider />

        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="夏普比率" :precision="2" :value="backtestResult.metrics.sharpeRatio">
              <template #prefix>
                <el-icon style="color: #409EFF">
                  <Histogram />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="索提诺比率" :precision="2" :value="backtestResult.metrics.sortinoRatio">
              <template #prefix>
                <el-icon style="color: #409EFF">
                  <DataLine />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="卡玛比率" :precision="2" :value="backtestResult.metrics.calmarRatio">
              <template #prefix>
                <el-icon style="color: #409EFF">
                  <PieChart />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="月度胜率" :precision="2" suffix="%" :value="backtestResult.metrics.winRate * 100">
              <template #prefix>
                <el-icon style="color: #67C23A">
                  <CircleCheck />
                </el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <!-- 组合构成分析 -->
      <div class="portfolio-composition-section">
        <div class="section-title">
          <el-icon><PieChart /></el-icon>
          <span>组合构成分析</span>
        </div>
        <el-row :gutter="20" style="margin-top: 16px">
          <!-- 左侧：策略分布饼图 -->
          <el-col :span="10">
            <div class="chart-title">大类策略分布</div>
            <div ref="strategyPieChartRef" style="width: 100%; height: 400px;"></div>
          </el-col>
          <!-- 右侧：产品构成表格 -->
          <el-col :span="14">
            <div class="chart-title">产品构成明细</div>
            <el-table :data="portfolioCompositionData" border style="width: 100%; margin-top: 10px" height="400" class="composition-table">
              <el-table-column prop="strategy" label="策略" width="97" />
              <el-table-column prop="product_name" label="产品" width="179" />
              <el-table-column prop="amount" label="金额" width="97" align="left">
                <template #default="{ row }">
                  {{ Math.round(row.amount) }} 万
                </template>
              </el-table-column>
              <el-table-column prop="ratio" label="占比" width="96" align="left">
                <template #default="{ row }">
                  {{ (row.ratio * 100).toFixed(2) }}%
                </template>
              </el-table-column>
              <el-table-column prop="features" label="产品特征" min-width="121">
                <template #default="{ row }">
                  <span style="color: #909399; white-space: pre-wrap;">{{ row.features || '-' }}</span>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
        </el-row>
      </div>

      <!-- 净值曲线图 -->
      <div class="chart-section">
        <div class="section-title">
          <el-icon><DataLine /></el-icon>
          <span>组合净值曲线</span>
        </div>
        <div ref="navChartRef" style="width: 100%; height: 450px;"></div>
      </div>

      <!-- 创新高分析表 -->
      <div v-if="backtestResult?.newHighAnalysis?.keyEvents?.length > 0" class="new-high-analysis-section">
        <div class="section-title">
          <el-icon><TrendCharts /></el-icon>
          <span>创新高关键事件分析</span>
        </div>

        <!-- 分析总结 -->
        <div class="analysis-summary" style="margin-bottom: 20px; padding: 16px; background: #f5f7fa; border-radius: 4px;">
          <el-row :gutter="20">
            <el-col :span="4">
              <div class="summary-item">
                <div class="summary-label">总创新高次数</div>
                <div class="summary-value" style="color: #909399;">{{ backtestResult.newHighAnalysis.summary.totalHighs }}次</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="summary-label">关键事件</div>
                <div class="summary-value" style="color: #409EFF;">{{ backtestResult.newHighAnalysis.summary.keyEventCount }}次</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="summary-label">🔴 压力测试</div>
                <div class="summary-value" style="color: #F56C6C;">{{ backtestResult.newHighAnalysis.summary.tagCounts['压力测试'] }}次</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="summary-label">🟡 漫长调整</div>
                <div class="summary-value" style="color: #E6A23C;">{{ backtestResult.newHighAnalysis.summary.tagCounts['漫长调整'] }}次</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="summary-label">🟢 趋势突破</div>
                <div class="summary-value" style="color: #67C23A;">{{ backtestResult.newHighAnalysis.summary.tagCounts['趋势突破'] }}次</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="summary-item">
                <div class="summary-label">🟦 逆势创高</div>
                <div class="summary-value" style="color: #409EFF;">{{ backtestResult.newHighAnalysis.summary.tagCounts['逆势创高'] }}次</div>
              </div>
            </el-col>
          </el-row>
          <el-divider style="margin: 16px 0;" />
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="summary-item">
                <div class="summary-label">模式类型</div>
                <div class="summary-value" style="color: #67C23A; font-size: 16px;">{{ backtestResult.newHighAnalysis.summary.pattern }}</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="summary-item">
                <div class="summary-label">市场依赖度</div>
                <div class="summary-value" style="color: #E6A23C; font-size: 16px;">{{ backtestResult.newHighAnalysis.summary.marketDependency }}</div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 关键事件表格 -->
        <el-table
          :data="backtestResult.newHighAnalysis.keyEvents"
          border
          style="width: 100%"
          :header-cell-style="{ background: '#f5f7fa', color: '#606266' }">
          <el-table-column prop="标签符号" label="标签" width="80" align="center">
            <template #default="scope">
              <span style="font-size: 20px;">{{ scope.row.标签符号 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="标签" label="事件类型" width="160" align="center">
            <template #default="scope">
              <template v-if="scope.row.标签.includes('+')">
                <!-- 合并标签，多个tag -->
                <span v-for="(tag, index) in scope.row.标签.split('+')" :key="index">
                  <el-tag
                    :type="tag === '压力测试' ? 'danger' : tag === '漫长调整' ? 'warning' : tag === '趋势突破' ? 'success' : 'primary'"
                    size="small"
                    style="margin: 2px;">
                    {{ tag }}
                  </el-tag>
                </span>
              </template>
              <template v-else>
                <!-- 单个标签 -->
                <el-tag
                  :type="scope.row.标签 === '压力测试' ? 'danger' : scope.row.标签 === '漫长调整' ? 'warning' : scope.row.标签 === '趋势突破' ? 'success' : 'primary'"
                  size="small">
                  {{ scope.row.标签 }}
                </el-tag>
              </template>
            </template>
          </el-table-column>
          <el-table-column prop="创新高日期" label="创新高日期" width="120" align="center" />
          <el-table-column prop="净值" label="净值" width="100" align="center">
            <template #default="scope">
              {{ scope.row.净值.toFixed(4) }}
            </template>
          </el-table-column>
          <el-table-column prop="距上次新高天数" label="距上次新高天数" width="140" align="center">
            <template #default="scope">
              <span v-if="scope.row.距上次新高天数">{{ scope.row.距上次新高天数 }}天</span>
              <span v-else style="color: #909399;">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="期间指数涨跌" label="期间指数涨跌" width="140" align="center">
            <template #default="scope">
              <span v-if="scope.row.期间指数涨跌 !== null" :style="{ color: scope.row.期间指数涨跌 >= 0 ? '#F56C6C' : '#67C23A' }">
                {{ scope.row.期间指数涨跌 > 0 ? '+' : '' }}{{ scope.row.期间指数涨跌 }}%
              </span>
              <span v-else style="color: #909399;">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="此后最大回撤" label="此后最大回撤" width="140" align="center">
            <template #default="scope">
              <span :style="{ color: scope.row.此后最大回撤 < -5 ? '#F56C6C' : scope.row.此后最大回撤 < -2 ? '#E6A23C' : '#67C23A' }">
                {{ scope.row.此后最大回撤.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="回撤修复天数" label="回撤修复天数" width="140" align="center">
            <template #default="scope">
              <span v-if="scope.row.回撤修复天数">{{ scope.row.回撤修复天数 }}天</span>
              <span v-else style="color: #909399;">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="备注" label="备注（市场环境）" min-width="200">
            <template #default="scope">
              {{ scope.row.备注 }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 说明文字 -->
        <div style="margin-top: 12px; padding: 12px; background: #fef0f0; border-left: 4px solid #F56C6C; font-size: 13px; color: #606266;">
          <div style="font-weight: 600; margin-bottom: 8px;">筛选标准说明：</div>
          <div>🔴 <strong>压力测试</strong>：此后最大回撤 ≤ -10%（暴露组合风控极限）</div>
          <div>🟡 <strong>漫长调整</strong>：此后最大回撤 ≤ -3% 且 回撤修复 ≥ 60天（漫长磨底期）</div>
          <div>🟢 <strong>趋势突破</strong>：距上次新高 ≥ 90天（走出盘整的新起点）</div>
          <div>🟦 <strong>逆势创高</strong>：期间指数涨跌 ≤ -3%（独立α能力）</div>
          <div style="margin-top: 8px; color: #909399;">注：表格仅展示关键事件，稳健期的创新高未列示</div>
        </div>
      </div>

      <!-- 回撤曲线图 -->
      <div class="chart-section">
        <div class="section-title">
          <el-icon><Bottom /></el-icon>
          <span>回撤曲线</span>
        </div>
        <div ref="drawdownChartRef" style="width: 100%; height: 350px;"></div>
      </div>

      <!-- 最大回撤信息 -->
      <div v-if="backtestResult?.maxDrawdownInfo" class="max-drawdown-info-section">
        <el-descriptions :column="3" border size="default">
          <el-descriptions-item label="最大回撤">
            <span style="color: #67C23A; font-weight: bold; font-size: 16px;">
              {{ (backtestResult.maxDrawdownInfo.maxDrawdown * 100).toFixed(2) }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="回撤发生时间">
            <span style="font-size: 14px;">
              {{ backtestResult.maxDrawdownInfo.peakDate }} 至 {{ backtestResult.maxDrawdownInfo.valleyDate }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="修复时间">
            <span v-if="backtestResult.maxDrawdownInfo.recoveryDate" style="font-size: 14px;">
              {{ backtestResult.maxDrawdownInfo.recoveryDays }} 天
              <span style="color: #909399; margin-left: 8px;">
                ({{ backtestResult.maxDrawdownInfo.valleyDate }} 至 {{ backtestResult.maxDrawdownInfo.recoveryDate }})
              </span>
            </span>
            <span v-else style="color: #F56C6C; font-size: 14px;">尚未恢复</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 季度收益贡献图 -->
      <div class="chart-section">
        <div class="section-title">
          <el-icon><TrendCharts /></el-icon>
          <span>季度收益贡献分析</span>
        </div>
        <div ref="quarterlyContributionChartRef" style="width: 100%; height: 450px;"></div>
      </div>

      <!-- 区间收益表 -->
      <div class="table-section">
        <div class="section-title">
          <el-icon><Calendar /></el-icon>
          <span>区间收益</span>
        </div>
        <el-table :data="backtestResult.monthlyReturns" border style="width: 100%" :fit="true">
          <el-table-column prop="year" label="年份" min-width="80" align="center" fixed="left" />
          <el-table-column label="1月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.jan !== null" :style="{ color: row.jan >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.jan * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="2月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.feb !== null" :style="{ color: row.feb >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.feb * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="3月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.mar !== null" :style="{ color: row.mar >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.mar * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="4月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.apr !== null" :style="{ color: row.apr >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.apr * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="5月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.may !== null" :style="{ color: row.may >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.may * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="6月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.jun !== null" :style="{ color: row.jun >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.jun * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="7月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.jul !== null" :style="{ color: row.jul >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.jul * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="8月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.aug !== null" :style="{ color: row.aug >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.aug * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="9月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.sep !== null" :style="{ color: row.sep >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.sep * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="10月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.oct !== null" :style="{ color: row.oct >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.oct * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="11月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.nov !== null" :style="{ color: row.nov >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.nov * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="12月" min-width="70" align="center">
            <template #default="{ row }">
              <span v-if="row.dec !== null" :style="{ color: row.dec >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold' }">
                {{ (row.dec * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
          <el-table-column label="全年" min-width="80" align="center" fixed="right">
            <template #default="{ row }">
              <span v-if="row.annual !== null" :style="{ color: row.annual >= 0 ? '#F56C6C' : '#67C23A', fontWeight: 'bold', fontSize: '14px' }">
                {{ (row.annual * 100).toFixed(2) }}%
              </span>
              <span v-else style="color: #C0C4CC">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty
      v-if="!backtestResult"
      description="配置组合参数后，点击【开始回测】查看结果"
      :image-size="200"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElLoading, ElMessageBox } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000'

// 产品搜索
const fundList = ref([])
const fundSearchLoading = ref(false)
const selectedFundCode = ref('')

// 组合构建
const portfolioItems = ref([])
const weightMode = ref('weight') // 'weight' 或 'amount'
const portfolioName = ref('') // 组合名称

// 已保存的组合
const savedPortfolios = ref([])

// 回测参数
const backtestParams = ref({
  initialCapital: 1000, // 初始资金（万元）
  startDate: null,
  endDate: null,
  dateRange: null, // 保留用于兼容
  benchmark: '', // 对比基准
  rebalanceFrequency: 'none', // 默认不调仓
  reinvestDividend: false, // 默认不分红再投资
  considerFees: false // 默认不考虑费用
})


// 回测结果
const backtestResult = ref(null)
const navChartRef = ref(null)
const drawdownChartRef = ref(null)
const strategyPieChartRef = ref(null)
const quarterlyContributionChartRef = ref(null)

// 组合构成数据
const portfolioCompositionData = ref([])

// 计算总权重
const totalWeight = computed(() => {
  return portfolioItems.value.reduce((sum, item) => sum + (item.weight || 0), 0)
})

// 搜索基金
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

// 添加基金到组合
function addFundToPortfolio() {
  if (!selectedFundCode.value) return

  // 检查是否已存在
  const exists = portfolioItems.value.find(item => item.fund_code === selectedFundCode.value)
  if (exists) {
    ElMessage.warning('该产品已在组合中')
    selectedFundCode.value = ''
    return
  }

  const fund = fundList.value.find(f => f.fund_code === selectedFundCode.value)
  if (!fund) return

  portfolioItems.value.push({
    fund_code: fund.fund_code,
    fund_name: fund.fund_name,
    weight: weightMode.value === 'weight' ? 0 : undefined,
    amount: weightMode.value === 'amount' ? 0 : undefined
  })

  selectedFundCode.value = ''
  ElMessage.success('已添加到组合')
}

// 从组合中移除
function removeFromPortfolio(index) {
  portfolioItems.value.splice(index, 1)
}

// 归一化权重
function normalizeWeights() {
  // 可选：自动归一化权重到100%
  // 这里暂不自动归一化，让用户手动调整
}

// 设置日期范围（结束时间始终为今天）
function setDateRange(days) {
  // 结束时间始终使用当前日期
  const endDate = new Date()
  endDate.setHours(0, 0, 0, 0)

  let startDate

  if (days === 0) {
    // 全部时间 - 设置一个较早的日期
    startDate = new Date('2010-01-01')
  } else {
    startDate = new Date()
    startDate.setDate(startDate.getDate() - days)
  }

  backtestParams.value.startDate = startDate.toISOString().split('T')[0]
  backtestParams.value.endDate = endDate.toISOString().split('T')[0]
}

// 将结束日期设置为今天（保持开始日期不变）
function setEndDateToday() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // 如果已有开始日期，保持开始日期不变
  if (backtestParams.value.startDate) {
    backtestParams.value.endDate = today.toISOString().split('T')[0]
  } else {
    // 如果没有设置过开始日期，默认设置近1年到今天
    const start = new Date()
    start.setDate(start.getDate() - 365)
    backtestParams.value.startDate = start.toISOString().split('T')[0]
    backtestParams.value.endDate = today.toISOString().split('T')[0]
  }
}

// 重置组合
function resetPortfolio() {
  portfolioItems.value = []
  backtestResult.value = null
  ElMessage.success('已重置')
}

// 运行回测
async function runBacktest() {
  // 验证输入
  if (portfolioItems.value.length === 0) {
    ElMessage.warning('请至少添加一个产品')
    return
  }

  if (weightMode.value === 'weight' && totalWeight.value !== 100) {
    ElMessage.warning('总权重必须等于100%')
    return
  }

  if (!backtestParams.value.startDate || !backtestParams.value.endDate) {
    ElMessage.warning('请选择回测时间范围')
    return
  }

  const loading = ElLoading.service({
    lock: true,
    text: '正在计算回测结果...',
    background: 'rgba(0, 0, 0, 0.7)'
  })

  try {
    // 准备回测请求数据
    const requestData = {
      portfolio: portfolioItems.value.map(item => ({
        fund_code: item.fund_code,
        weight: weightMode.value === 'weight' ? item.weight / 100 : null,
        amount: weightMode.value === 'amount' ? item.amount : null
      })),
      initial_capital: backtestParams.value.initialCapital,
      start_date: backtestParams.value.startDate,
      end_date: backtestParams.value.endDate,
      benchmark: backtestParams.value.benchmark || null,
      rebalance_frequency: backtestParams.value.rebalanceFrequency,
      reinvest_dividend: backtestParams.value.reinvestDividend,
      consider_fees: backtestParams.value.considerFees,
      weight_mode: weightMode.value
    }

    const response = await axios.post(`${API_BASE}/api/portfolio-backtest/run`, requestData)

    if (response.data.success) {
      backtestResult.value = response.data.data

      // 准备组合构成数据
      prepareCompositionData()

      ElMessage.success('回测完成')

      // 等待DOM更新后绘制图表
      await nextTick()
      drawCharts()
    }
  } catch (error) {
    console.error('回测失败:', error)
    ElMessage.error(error.response?.data?.detail || '回测失败')
  } finally {
    loading.close()
  }
}

// 准备组合构成数据
async function prepareCompositionData() {
  if (!backtestResult.value || portfolioItems.value.length === 0) {
    portfolioCompositionData.value = []
    return
  }

  // 计算总金额
  let totalAmount = 0
  if (weightMode.value === 'weight') {
    // 权重模式：使用初始资金
    totalAmount = backtestParams.value.initialCapital
  } else {
    // 金额模式：使用所有产品金额之和
    totalAmount = portfolioItems.value.reduce((sum, item) => sum + (item.amount || 0), 0)
  }

  // 为每个产品获取详细信息并准备数据
  const compositionPromises = portfolioItems.value.map(async (item) => {
    // 计算该产品的金额
    let productAmount = 0
    if (weightMode.value === 'weight') {
      productAmount = totalAmount * (item.weight / 100)
    } else {
      productAmount = item.amount || 0
    }

    // 获取产品策略信息和基金详情
    let strategyInfo = null
    let fundInfo = null

    try {
      // 获取策略信息
      const strategyResponse = await axios.get(`${API_BASE}/api/strategy/${item.fund_code}`)
      if (strategyResponse.data) {
        strategyInfo = strategyResponse.data
        console.log(`${item.fund_code} 策略信息:`, strategyInfo)
      }
    } catch (error) {
      console.error(`获取产品 ${item.fund_code} 策略信息失败:`, error)
    }

    try {
      // 获取基金详情（获取简称）
      const fundResponse = await axios.get(`${API_BASE}/api/nav/funds`, {
        params: { search: item.fund_code }
      })
      if (fundResponse.data.success) {
        const funds = fundResponse.data.data.funds || []
        fundInfo = funds.find(f => f.fund_code === item.fund_code)
      }
    } catch (error) {
      console.error(`获取产品 ${item.fund_code} 基金信息失败:`, error)
    }

    const compositionItem = {
      fund_code: item.fund_code,
      product_name: fundInfo?.short_name || fundInfo?.fund_name || item.fund_name, // 优先使用简称
      strategy: strategyInfo?.sub_strategy || '未分类', // 细分策略
      main_strategy: strategyInfo?.main_strategy || '未分类', // 大类策略
      amount: productAmount,
      ratio: productAmount / totalAmount,
      features: fundInfo?.product_features || '' // 产品特征
    }

    console.log(`${item.fund_code} 组合数据:`, compositionItem)
    return compositionItem
  })

  portfolioCompositionData.value = await Promise.all(compositionPromises)
  console.log('完整组合构成数据:', portfolioCompositionData.value)

  // 对产品构成数据进行排序
  sortCompositionData()

  // 等待表格渲染后设置行高
  await nextTick()
  setCompositionTableRowHeight()
}

// 对产品构成数据进行排序
function sortCompositionData() {
  // 定义策略排序规则
  const strategyOrder = {
    // 成长配置
    '主观多头': 1,
    '量化多头': 2,
    '股票多头': 3,
    '股票多空': 4,
    // 尾部对冲
    '宏观策略': 5,
    'CTA策略': 6,
    // 稳健配置
    '量化稳健': 7,
    '债券策略': 8,
  }

  portfolioCompositionData.value.sort((a, b) => {
    const orderA = strategyOrder[a.strategy] || 999
    const orderB = strategyOrder[b.strategy] || 999
    return orderA - orderB
  })

  console.log('排序后的组合构成数据:', portfolioCompositionData.value)
}

// 设置产品构成表格的行高
function setCompositionTableRowHeight() {
  const tableHeight = 400 // 表格总高度
  const headerHeight = 45 // 表头固定高度
  const productCount = portfolioCompositionData.value.length

  if (productCount === 0) return

  const remainingHeight = tableHeight - headerHeight
  const rowHeight = remainingHeight / productCount

  console.log(`表格总高度: ${tableHeight}px, 表头: ${headerHeight}px, 产品数: ${productCount}, 每行高度: ${rowHeight}px`)

  // 使用nextTick确保DOM已更新
  nextTick(() => {
    const rows = document.querySelectorAll('.composition-table .el-table__body-wrapper .el-table__row')
    rows.forEach(row => {
      row.style.height = `${rowHeight}px`
    })
  })
}

// 绘制图表
function drawCharts() {
  if (!backtestResult.value) return

  // 绘制策略分布饼图
  drawStrategyPieChart()
  // 绘制净值曲线
  drawNavChart()
  // 绘制回撤曲线
  drawDrawdownChart()
  // 绘制季度收益贡献图表
  drawQuarterlyContributionChart()
  // 设置表格行高
  setCompositionTableRowHeight()
}

// 绘制策略分布饼图
function drawStrategyPieChart() {
  if (!strategyPieChartRef.value || portfolioCompositionData.value.length === 0) return

  const chart = echarts.init(strategyPieChartRef.value)

  // 按大类策略聚合数据
  const strategyMap = new Map()
  portfolioCompositionData.value.forEach(item => {
    const strategy = item.main_strategy || '未分类'
    console.log(`聚合产品 ${item.fund_code}, 大类策略: ${strategy}, 金额: ${item.amount}`)
    if (strategyMap.has(strategy)) {
      strategyMap.set(strategy, strategyMap.get(strategy) + item.amount)
    } else {
      strategyMap.set(strategy, item.amount)
    }
  })

  console.log('策略聚合结果:', Object.fromEntries(strategyMap))

  // 转换为饼图数据格式
  const pieData = Array.from(strategyMap.entries()).map(([name, value]) => ({
    name,
    value
  }))

  console.log('饼图数据:', pieData)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} 万元 ({d}%)'
    },
    series: [
      {
        name: '策略分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: true
        },
        data: pieData
      }
    ]
  }

  chart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 绘制净值曲线
function drawNavChart() {
  if (!navChartRef.value) return

  const chart = echarts.init(navChartRef.value)

  const dates = backtestResult.value.navCurve.map(item => item.date)
  const navValues = backtestResult.value.navCurve.map(item => item.nav)

  // 构建系列数据
  const series = [
    {
      name: '组合净值',
      type: 'line',
      data: navValues,
      smooth: true,
      showSymbol: false,
      lineStyle: {
        width: 2,
        color: '#F56C6C'  // 红色
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
          { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
        ])
      }
    }
  ]

  // 如果有基准数据，添加基准曲线
  if (backtestResult.value.benchmarkNavCurve && backtestResult.value.benchmarkNavCurve.length > 0) {
    const benchmarkValues = backtestResult.value.benchmarkNavCurve.map(item => item.nav)
    series.push({
      name: '基准净值',
      type: 'line',
      data: benchmarkValues,
      smooth: true,
      showSymbol: false,
      lineStyle: {
        width: 2,
        type: 'dashed',  // 虚线
        color: '#409EFF'  // 蓝色
      }
    })
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>'
        params.forEach(param => {
          result += `${param.seriesName}: ${param.data.toFixed(4)}<br/>`
        })
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      top: '12%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: series
  }

  chart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 绘制回撤曲线
function drawDrawdownChart() {
  if (!drawdownChartRef.value) return

  const chart = echarts.init(drawdownChartRef.value)

  const dates = backtestResult.value.drawdownCurve.map(item => item.date)
  const drawdowns = backtestResult.value.drawdownCurve.map(item => item.drawdown * 100)

  // 构建系列数据
  const series = [
    {
      name: '组合回撤',
      type: 'line',
      data: drawdowns,
      smooth: true,
      showSymbol: false,
      lineStyle: {
        width: 2,
        color: '#67C23A'  // 绿色
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(103, 194, 58, 0.3)' },
          { offset: 1, color: 'rgba(103, 194, 58, 0.05)' }
        ])
      }
    }
  ]

  // 如果有基准回撤数据，添加基准回撤曲线
  if (backtestResult.value.benchmarkDrawdownCurve && backtestResult.value.benchmarkDrawdownCurve.length > 0) {
    const benchmarkDrawdowns = backtestResult.value.benchmarkDrawdownCurve.map(item => item.drawdown * 100)
    series.push({
      name: '基准回撤',
      type: 'line',
      data: benchmarkDrawdowns,
      smooth: true,
      showSymbol: false,
      lineStyle: {
        width: 2,
        type: 'dashed',  // 虚线
        color: '#409EFF'  // 蓝色
      }
    })
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        let result = params[0].axisValue + '<br/>'
        params.forEach(param => {
          result += `${param.seriesName}: ${param.data.toFixed(2)}%<br/>`
        })
        return result
      }
    },
    legend: {
      data: series.map(s => s.name),
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      top: '12%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: series
  }

  chart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 绘制季度收益贡献图表
function drawQuarterlyContributionChart() {
  if (!quarterlyContributionChartRef.value || !backtestResult.value?.quarterlyContributions) return

  const chart = echarts.init(quarterlyContributionChartRef.value)

  const quarterlyData = backtestResult.value.quarterlyContributions

  if (!quarterlyData || quarterlyData.length === 0) return

  // 只提取当前组合中的产品代码
  const fundCodes = new Set()
  const fundCodeToName = {}

  // 从当前组合中获取产品代码和名称映射
  portfolioCompositionData.value.forEach(item => {
    fundCodes.add(item.fund_code)
    fundCodeToName[item.fund_code] = item.product_name
  })

  // 准备数据
  const quarters = quarterlyData.map(item => item.quarter)
  const cumulativeData = quarterlyData.map(item => item.cumulative)

  // 为每个产品准备系列数据
  const series = []

  // 生成颜色方案
  const colors = [
    '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
    '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#8dc1a9'
  ]

  const legendData = []
  let colorIndex = 0
  fundCodes.forEach(fundCode => {
    const data = quarterlyData.map(item => {
      return item.contributions[fundCode] || 0
    })

    const displayName = fundCodeToName[fundCode] || fundCode
    legendData.push(displayName)

    series.push({
      name: displayName,
      type: 'bar',
      stack: 'total',
      data: data,
      itemStyle: {
        color: colors[colorIndex % colors.length]
      }
    })

    colorIndex++
  })

  // 添加累计收益折线图
  legendData.push('累计收益')
  series.push({
    name: '累计收益',
    type: 'line',
    yAxisIndex: 1,
    data: cumulativeData,
    smooth: true,
    showSymbol: true,
    symbolSize: 8,
    lineStyle: {
      width: 3,
      color: '#FF6B6B'
    },
    itemStyle: {
      color: '#FF6B6B'
    }
  })

  // ========== 严格的双Y轴0刻度线对齐算法 ==========
  // 原理：0刻度线在Y轴上的相对位置 = |min| / (max - min)
  // 左右两轴的这个比例必须完全相等

  // 步骤1：计算左轴数据范围（季度收益 - 柱状图堆叠数据）
  const leftAxisData = []
  quarterlyData.forEach(item => {
    let positiveSum = 0
    let negativeSum = 0
    Object.values(item.contributions).forEach(value => {
      if (value > 0) positiveSum += value
      else negativeSum += value
    })
    leftAxisData.push(positiveSum, negativeSum)
  })

  const leftDataMax = Math.max(...leftAxisData, 0)
  const leftDataMin = Math.min(...leftAxisData, 0)

  // 步骤2：计算右轴数据范围（累计收益 - 折线图数据）
  const rightDataMax = Math.max(...cumulativeData, 0)
  const rightDataMin = Math.min(...cumulativeData, 0)

  // 步骤3：为数据添加10%的视觉边距
  const leftDataMaxWithPadding = leftDataMax * 1.1
  const leftDataMinWithPadding = leftDataMin * 1.1
  const rightDataMaxWithPadding = rightDataMax * 1.1
  const rightDataMinWithPadding = rightDataMin * 1.1

  // 步骤4：计算0刻度线的相对位置（以左轴为基准）
  // zeroRatio = |min| / (max - min)，表示0点在轴上的位置比例
  const leftRange = leftDataMaxWithPadding - leftDataMinWithPadding
  const zeroRatio = Math.abs(leftDataMinWithPadding) / leftRange

  // 步骤5：根据zeroRatio反推右轴的min和max
  // 已知：zeroRatio = |rightMin| / (rightMax - rightMin)
  // 且：rightMax >= rightDataMaxWithPadding
  // 求解：rightMin 和 rightMax，使得0点位置与左轴对齐

  let leftAxisMin, leftAxisMax, rightAxisMin, rightAxisMax

  leftAxisMin = leftDataMinWithPadding
  leftAxisMax = leftDataMaxWithPadding

  // 根据0点位置比例计算右轴范围
  // zeroRatio = |rightMin| / (rightMax - rightMin)
  // 变形得：rightMax = rightMin / zeroRatio + rightMin
  // 即：rightMax = rightMin * (1/zeroRatio - 1) + rightMin = rightMin * (1 - zeroRatio) / zeroRatio

  if (zeroRatio === 0) {
    // 左轴没有负值，右轴也不应该有负值
    rightAxisMin = 0
    rightAxisMax = rightDataMaxWithPadding
  } else if (zeroRatio === 1) {
    // 左轴没有正值，右轴也不应该有正值
    rightAxisMin = rightDataMinWithPadding
    rightAxisMax = 0
  } else {
    // 一般情况：根据zeroRatio计算右轴范围
    // 确保右轴能容纳数据的同时保持0点对齐
    const rightRangeFromMax = rightDataMaxWithPadding / (1 - zeroRatio)
    const rightRangeFromMin = Math.abs(rightDataMinWithPadding) / zeroRatio

    // 取较大的范围以确保数据都能显示
    const rightRange = Math.max(rightRangeFromMax, rightRangeFromMin)

    rightAxisMax = rightRange * (1 - zeroRatio)
    rightAxisMin = -rightRange * zeroRatio
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: function(params) {
        let result = `${params[0].axisValue}<br/>`

        // 显示各产品贡献
        params.forEach(item => {
          if (item.seriesType === 'bar') {
            const value = item.value
            if (value !== 0) {
              result += `${item.seriesName}: ${value.toFixed(2)} 万元<br/>`
            }
          }
        })

        // 显示累计收益
        const cumulativeItem = params.find(item => item.seriesName === '累计收益')
        if (cumulativeItem) {
          result += `<strong>累计收益: ${cumulativeItem.value.toFixed(2)} 万元</strong>`
        }

        return result
      }
    },
    legend: {
      data: legendData,
      top: 10,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      top: 50,
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: quarters
    },
    yAxis: [
      {
        type: 'value',
        name: '季度收益（万元）',
        position: 'left',
        min: leftAxisMin,
        max: leftAxisMax,
        axisLabel: {
          formatter: function(value) {
            return Math.round(value)
          }
        },
        splitLine: {
          show: true
        }
      },
      {
        type: 'value',
        name: '累计收益（万元）',
        position: 'right',
        min: rightAxisMin,
        max: rightAxisMax,
        axisLabel: {
          formatter: function(value) {
            return Math.round(value)
          }
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: series
  }

  chart.setOption(option)

  // 响应式
  window.addEventListener('resize', () => {
    chart.resize()
  })
}

// 导出报告
function exportReport() {
  ElMessage.info('导出功能开发中...')
}

// 加载已保存的组合列表
async function loadSavedPortfolios() {
  try {
    const response = await axios.get(`${API_BASE}/api/portfolio-backtest/portfolios`)
    if (response.data.success) {
      savedPortfolios.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载组合列表失败:', error)
  }
}

// 保存组合
async function savePortfolio() {
  if (!portfolioName.value || portfolioName.value.trim() === '') {
    ElMessage.warning('请输入组合名称')
    return
  }

  if (portfolioItems.value.length === 0) {
    ElMessage.warning('组合不能为空')
    return
  }

  if (weightMode.value === 'weight' && totalWeight.value !== 100) {
    ElMessage.warning('总权重必须等于100%')
    return
  }

  try {
    const response = await axios.post(`${API_BASE}/api/portfolio-backtest/save`, {
      portfolio_name: portfolioName.value,
      portfolio: portfolioItems.value.map(item => ({
        fund_code: item.fund_code,
        weight: weightMode.value === 'weight' ? item.weight / 100 : null,
        amount: weightMode.value === 'amount' ? item.amount : null
      })),
      initial_capital: backtestParams.value.initialCapital,
      weight_mode: weightMode.value,
      rebalance_frequency: 'none',
      reinvest_dividend: false,
      consider_fees: false
    })

    if (response.data.success) {
      ElMessage.success(`组合 "${portfolioName.value}" 保存成功`)
      await loadSavedPortfolios()
    }
  } catch (error) {
    console.error('保存组合失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存组合失败')
  }
}

// 加载组合
async function loadPortfolio(portfolioId) {
  try {
    const response = await axios.get(`${API_BASE}/api/portfolio-backtest/portfolios/${portfolioId}`)

    if (response.data.success) {
      const data = response.data.data

      // 设置组合名称
      portfolioName.value = data.portfolio_name

      // 设置配置模式
      weightMode.value = data.weight_mode

      // 获取产品信息并设置组合项
      portfolioItems.value = []
      for (const item of data.portfolio) {
        // 搜索产品信息
        try {
          const fundResponse = await axios.get(`${API_BASE}/api/nav/funds`, {
            params: { search: item.fund_code }
          })

          if (fundResponse.data.success) {
            const funds = fundResponse.data.data.funds || []
            const fund = funds.find(f => f.fund_code === item.fund_code)

            if (fund) {
              portfolioItems.value.push({
                fund_code: fund.fund_code,
                fund_name: fund.fund_name,
                weight: item.weight ? item.weight * 100 : undefined,
                amount: item.amount
              })
            }
          }
        } catch (err) {
          console.error(`获取产品 ${item.fund_code} 信息失败:`, err)
        }
      }

      // 设置回测参数（只设置初始资金）
      backtestParams.value.initialCapital = data.initial_capital

      ElMessage.success(`已加载组合 "${data.portfolio_name}"`)
    }
  } catch (error) {
    console.error('加载组合失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载组合失败')
  }
}

// 删除组合确认
async function deletePortfolioConfirm(portfolio) {
  try {
    await ElMessageBox.confirm(
      `确定要删除组合 "${portfolio.portfolio_name}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 执行删除
    const response = await axios.delete(`${API_BASE}/api/portfolio-backtest/portfolios/${portfolio.id}`)

    if (response.data.success) {
      ElMessage.success(`组合 "${portfolio.portfolio_name}" 已删除`)
      await loadSavedPortfolios()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除组合失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除组合失败')
    }
  }
}

onMounted(() => {
  // 初始化日期范围为近1年
  setDateRange(365)
  // 加载已保存的组合列表
  loadSavedPortfolios()
})
</script>

<style scoped>
.portfolio-backtest-container {
  padding: 20px;
}

.saved-portfolios-card {
  margin-bottom: 20px;
}

.header-card,
.result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.portfolio-builder {
  padding: 20px 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #303133;
}

.backtest-period {
  font-size: 13px;
  font-weight: normal;
  color: #606266;
  margin-left: 8px;
}

.section-subtitle {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #606266;
}

.weight-summary {
  margin-top: 12px;
  text-align: right;
}

.quick-settings {
  margin-top: 24px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.position-info-section {
  padding: 20px 0;
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.metrics-grid {
  padding: 20px 0;
}

.portfolio-composition-section {
  padding: 20px 0;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
  padding-left: 8px;
  border-left: 3px solid #409EFF;
}

.chart-section,
.table-section {
  margin-top: 30px;
}

/* 统计数字样式 */
.el-statistic {
  text-align: center;
}

.el-statistic :deep(.el-statistic__head) {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.el-statistic :deep(.el-statistic__content) {
  font-size: 24px;
  font-weight: 600;
}

/* 已保存组合列表样式 */
.saved-portfolios-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.empty-portfolios {
  padding: 12px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.portfolio-count {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
  margin-left: 8px;
}

.portfolio-tag {
  cursor: pointer;
  padding: 8px 12px;
  font-size: 14px;
  transition: all 0.3s;
}

.portfolio-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.portfolio-tag .el-icon {
  margin-right: 4px;
}

/* 产品构成表格样式 */
.composition-table {
  height: 400px !important;
}

.composition-table :deep(.el-table__header-wrapper) {
  height: 45px;
}

.composition-table :deep(.el-table__header-wrapper .el-table__cell) {
  padding: 12px 0;
  height: 45px;
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}

.composition-table :deep(.el-table__body-wrapper) {
  height: 355px !important;
  overflow-y: hidden;
}

.composition-table :deep(.el-table__row) {
  /* 行高将通过 JavaScript 动态设置 */
}

.composition-table :deep(.el-table__cell .cell) {
  line-height: normal;
  display: flex;
  align-items: center;
}

.max-drawdown-info-section {
  margin: 20px 0;
  padding: 0 20px;
}

.max-drawdown-info-section :deep(.el-descriptions__label) {
  font-weight: 600;
  width: 120px;
}

.max-drawdown-info-section :deep(.el-descriptions__content) {
  font-size: 14px;
}

.new-high-analysis-section {
  margin: 20px 0;
  padding: 0 20px;
}

.analysis-summary .summary-item {
  text-align: center;
}

.analysis-summary .summary-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.analysis-summary .summary-value {
  font-size: 18px;
  font-weight: 600;
}
</style>
