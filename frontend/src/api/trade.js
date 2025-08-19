import request from './index'

/**
 * 交易分析API
 */
export const tradeAPI = {
  // 资金流向分析
  analyzeCashFlow(params = {}) {
    return request.get('/api/trade/flow-analysis', { params })
  },

  // 客户交易活跃度分析
  analyzeClientActivity(params = {}) {
    return request.get('/api/trade/client-activity', { params })
  },

  // 基金表现分析
  analyzeFundPerformance(params = {}) {
    return request.get('/api/trade/fund-performance', { params })
  },

  // 季节性交易分析
  analyzeSeasonalPatterns(params = {}) {
    return request.get('/api/trade/seasonal-analysis', { params })
  }
}