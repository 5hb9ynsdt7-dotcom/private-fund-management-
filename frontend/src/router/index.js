import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/nav'
  },
  {
    path: '/nav',
    name: 'NavManagement',
    component: () => import('../views/NavManagement.vue'),
    meta: { title: '净值管理', layout: 'table' }
  },
  {
    path: '/nav/detail/:fundCode',
    name: 'FundNavDetail',
    component: () => import('../views/FundNavDetail.vue'),
    meta: { title: '基金净值详情', layout: 'table' }
  },
  {
    path: '/nav-crawler',
    name: 'NavCrawler',
    component: () => import('../views/NavCrawler.vue'),
    meta: { title: '净值抓取' }
  },
  {
    path: '/strategy',
    name: 'StrategyManagement',
    component: () => import('../views/StrategyManagement.vue'),
    meta: { title: '策略管理', layout: 'table' }
  },
  {
    path: '/product-analysis',
    name: 'ProductAnalysis',
    component: () => import('../views/ProductAnalysis.vue'),
    meta: { title: '产品分析' }
  },
  {
    path: '/fund-schedule',
    name: 'FundSchedule',
    component: () => import('../views/FundSchedule.vue'),
    meta: { title: '产品档期' }
  },
  {
    path: '/position',
    name: 'PositionAnalysis',
    component: () => import('../views/PositionAnalysis.vue'),
    meta: { title: '持仓分析', layout: 'table' }
  },
  {
    path: '/position/detail/:groupId',
    name: 'PositionDetail',
    component: () => import('../views/PositionDetail.vue'),
    meta: { title: '持仓详情', layout: 'table' }
  },
  {
    path: '/trade',
    name: 'TradeAnalysis',
    component: () => import('../views/TradeAnalysis.vue'),
    meta: { title: '交易分析', layout: 'table' }
  },
  {
    path: '/trade/:groupId',
    name: 'TradeDetail',
    component: () => import('../views/TradeDetail.vue'),
    meta: { title: '交易详情', layout: 'table' }
  },
  {
    path: '/project-holding',
    name: 'ProjectHoldingList',
    component: () => import('../views/ProjectHoldingList.vue'),
    meta: { title: '项目持仓分析', layout: 'table' }
  },
  {
    path: '/project-holding/:projectName',
    name: 'ProjectHoldingDetail',
    component: () => import('../views/ProjectHoldingDetail.vue'),
    meta: { title: '项目持仓详情', layout: 'table' }
  },
  {
    path: '/stage-performance',
    name: 'StagePerformance',
    component: () => import('../views/StagePerformance.vue'),
    meta: { title: '阶段涨幅', layout: 'table' }
  },
  {
    path: '/quantitative-analysis',
    name: 'QuantitativeAnalysis',
    component: () => import('../views/QuantitativeAnalysis/index.vue'),
    meta: { title: '量化分析' },
    redirect: '/quantitative-analysis/product-list',
    children: [
      {
        path: 'product-list',
        name: 'QuantProductList',
        component: () => import('../views/QuantitativeAnalysis/ProductList.vue'),
        meta: { title: '产品列表', layout: 'table' }
      },
      {
        path: 'summary-analysis',
        name: 'QuantSummaryAnalysis',
        component: () => import('../views/QuantitativeAnalysis/SummaryAnalysis.vue'),
        meta: { title: '汇总分析', layout: 'table' }
      },
      {
        path: 'single-product/:productId',
        name: 'QuantSingleProduct',
        component: () => import('../views/QuantitativeAnalysis/SingleProductAnalysis.vue'),
        meta: { title: '单品分析', layout: 'table' }
      }
    ]
  },
  {
    path: '/public-fund',
    name: 'PublicFundLibrary',
    component: () => import('../views/PublicFund/FundLibrary.vue'),
    meta: { title: '公募基金库', layout: 'table' }
  },
  {
    path: '/public-fund/detail/:fundCode',
    name: 'PublicFundDetail',
    component: () => import('../views/PublicFund/FundDetail.vue'),
    meta: { title: '基金详情', layout: 'table' }
  },
  {
    path: '/portfolio',
    name: 'PortfolioList',
    component: () => import('../views/Portfolio/PortfolioList.vue'),
    meta: { title: '实盘组合', layout: 'table' }
  },
  {
    path: '/portfolio/:id',
    name: 'PortfolioDetail',
    component: () => import('../views/Portfolio/PortfolioDetail.vue'),
    meta: { title: '组合详情', layout: 'table' }
  },
  {
    path: '/portfolio-backtest',
    name: 'PortfolioBacktest',
    component: () => import('../views/PortfolioBacktest.vue'),
    meta: { title: '组合回测', layout: 'table' }
  },
  {
    path: '/performance-pk',
    name: 'PerformancePK',
    component: () => import('../views/PerformancePK.vue'),
    meta: { title: '业绩PK', layout: 'table' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta?.title) {
    document.title = `${to.meta.title} - Private Fund Management`
  }
  next()
})

export default router