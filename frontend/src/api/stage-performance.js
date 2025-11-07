import request from './index'

/**
 * 阶段涨幅分析API
 */
export const stagePerformanceAPI = {
  // 获取产品近一周涨跌幅
  getWeeklyPerformance(params = {}) {
    return request.get('/api/stage-performance/weekly', { params })
  },

  // 获取自定义期间涨跌幅
  getPeriodPerformance(params = {}) {
    return request.get('/api/stage-performance/period', { params })
  }
}