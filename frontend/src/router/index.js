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
    meta: { title: '净值管理' }
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
    meta: { title: '策略管理' }
  },
  {
    path: '/position',
    name: 'PositionAnalysis',
    component: () => import('../views/PositionAnalysis.vue'),
    meta: { title: '持仓分析' }
  },
  {
    path: '/position/detail/:groupId',
    name: 'PositionDetail',
    component: () => import('../views/PositionDetail.vue'),
    meta: { title: '持仓详情' }
  },
  {
    path: '/trade',
    name: 'TradeAnalysis',
    component: () => import('../views/TradeAnalysis.vue'),
    meta: { title: '交易分析' }
  },
  {
    path: '/trade/:groupId',
    name: 'TradeDetail',
    component: () => import('../views/TradeDetail.vue'),
    meta: { title: '交易详情' }
  },
  {
    path: '/project-holding',
    name: 'ProjectHoldingList',
    component: () => import('../views/ProjectHoldingList.vue'),
    meta: { title: '项目持仓分析' }
  },
  {
    path: '/project-holding/:projectName',
    name: 'ProjectHoldingDetail',
    component: () => import('../views/ProjectHoldingDetail.vue'),
    meta: { title: '项目持仓详情' }
  },
  {
    path: '/stage-performance',
    name: 'StagePerformance',
    component: () => import('../views/StagePerformance.vue'),
    meta: { title: '阶段涨幅' }
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