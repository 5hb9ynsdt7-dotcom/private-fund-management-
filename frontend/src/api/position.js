import request from './index'

/**
 * 持仓分析API
 */
export const positionAPI = {
  // 获取持仓列表
  getPositionList(params = {}) {
    return request.get('/api/position/list', { params })
  },

  // 客户持仓分析
  analyzeClientPositions(groupId) {
    return request.get(`/api/position/client/${groupId}`)
  },

  // 基金持仓分析
  analyzeFundPositions(fundCode) {
    return request.get(`/api/position/fund/${fundCode}`)
  },

  // 获取基金前十大持有人
  getFundTopHolders(fundCode, topN = 10) {
    return request.get(`/api/position/fund/${fundCode}/top-holders`, {
      params: { top_n: topN }
    })
  },

  // 持仓集中度分析
  analyzePositionConcentration(fundCode) {
    return request.get(`/api/position/fund/${fundCode}/concentration`)
  },

  // 按理财师汇总持仓
  getPositionsByPlanner(planner = null) {
    return request.get('/api/position/summary/by-planner', {
      params: planner ? { domestic_planner: planner } : {}
    })
  },

  // 持仓统计概览
  getPositionStatistics() {
    return request.get('/api/position/statistics/overview')
  },

  // 批量上传持仓数据
  uploadPositions(formData, overrideExisting = false) {
    return request.post(`/api/position/upload?override_existing=${overrideExisting}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取客户列表
  getClientList(params = {}) {
    return request.get('/api/position/clients', { params })
  },

  // 获取客户持仓详情
  getClientPositionDetail(groupId, asOfDate = null, startDate = null, endDate = null) {
    const params = {}
    if (asOfDate) params.as_of_date = asOfDate
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return request.get(`/api/position/clients/${groupId}`, { params })
  },

  // 删除客户及其所有持仓
  deleteClient(groupId) {
    return request.delete(`/api/position/clients/${groupId}`)
  },

  // 上传客户分红数据
  uploadClientDividends(formData, overrideExisting = false) {
    return request.post('/api/position/client-dividends/upload', formData, {
      params: { override_existing: overrideExisting },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}