import request from './index'

/**
 * 净值管理API
 */
export const navAPI = {
  // 获取净值列表
  getNavList(params = {}) {
    return request.get('/api/nav/list', { params })
  },

  // 手动添加净值记录
  createNavManual(data) {
    return request.post('/api/nav/manual', data)
  },

  // 批量上传净值文件
  uploadNavFiles(files) {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })
    
    return request.post('/api/nav/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除净值记录
  deleteNavRecords(navIds) {
    return request.delete('/api/nav/', {
      data: { nav_ids: navIds }
    })
  },

  // 获取指定基金净值
  getNavByFund(fundCode, limit = 10) {
    return request.get(`/api/nav/fund/${fundCode}`, {
      params: { limit }
    })
  },

  // 获取净值统计
  getNavStatistics(fundCode, days = 30) {
    return request.get(`/api/nav/statistics/${fundCode}`, {
      params: { days }
    })
  },

  // 获取有净值数据的基金列表
  getFundsWithNav() {
    return request.get('/api/nav/funds')
  },

  // 创建净值记录
  createNav(data) {
    return request.post('/api/nav/', data)
  },

  // 删除单个净值记录
  deleteNav(navId) {
    return request.delete(`/api/nav/${navId}`)
  },

  // 批量删除净值记录
  batchDeleteNav(navIds) {
    return request.delete('/api/nav/', {
      data: { nav_ids: navIds }
    })
  },

  // 获取最新净值
  getLatestNav(fundCode) {
    return request.get(`/api/nav/latest/${fundCode}`)
  },

  // 预测净值
  predictNav(data) {
    return request.post('/api/nav/predict', data)
  },

  // 导出净值数据
  exportNavData(params = {}) {
    return request.get('/api/nav/export', {
      params,
      responseType: 'blob'
    })
  },

  // 上传净值文件（修正方法名）
  uploadNavFiles(formData) {
    return request.post('/api/nav/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}