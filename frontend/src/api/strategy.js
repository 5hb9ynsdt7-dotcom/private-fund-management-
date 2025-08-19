import request from './index'

/**
 * 策略管理API
 */
export const strategyAPI = {
  // 创建/更新策略
  createOrUpdateStrategy(data) {
    return request.post('/api/strategy/', data)
  },

  // 获取策略列表
  getStrategyList(params = {}) {
    return request.get('/api/strategy/', { params })
  },

  // 获取单个基金策略
  getStrategyByFund(fundCode) {
    return request.get(`/api/strategy/${fundCode}`)
  },

  // 删除策略
  deleteStrategy(fundCode) {
    return request.delete(`/api/strategy/${fundCode}`)
  },

  // 获取大类策略枚举
  getMainStrategyOptions() {
    return request.get('/api/strategy/enums/main-strategies')
  },

  // 获取策略分布统计
  getStrategyDistribution() {
    return request.get('/api/strategy/statistics/distribution')
  },

  // 获取策略统计数据
  getStrategyStatistics() {
    return request.get('/api/strategy/statistics')
  },

  // 更新QD状态
  updateQdStatus(fundCode, isQd) {
    return request.patch(`/api/strategy/${fundCode}/qd-status`, {
      is_qd: isQd
    })
  },

  // 批量删除策略
  batchDeleteStrategy(fundCodes) {
    return request.delete('/api/strategy/batch', {
      data: { fund_codes: fundCodes }
    })
  },

  // 批量更新策略
  batchUpdateStrategy(data) {
    return request.patch('/api/strategy/batch', data)
  },

  // 导出策略数据
  exportStrategyData(params = {}) {
    return request.get('/api/strategy/export', {
      params,
      responseType: 'blob'
    })
  },

  // 上传策略文件
  uploadStrategyFiles(formData) {
    return request.post('/api/strategy/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}