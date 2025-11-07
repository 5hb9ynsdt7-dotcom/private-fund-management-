/**
 * 交易分析API服务
 * Transaction Analysis API Service
 */

import request from './index'

export const transactionAPI = {
  /**
   * 上传交易数据文件
   * @param {FormData} formData - 包含Excel文件的FormData
   * @param {boolean} overrideExisting - 是否覆盖已存在数据
   */
  uploadTransactions(formData, overrideExisting = false) {
    return request.post('/api/transaction/upload', formData, {
      params: {
        override_existing: overrideExisting
      },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取交易客户列表
   * @param {Object} params - 查询参数
   */
  getTransactionClients(params = {}) {
    return request.get('/api/transaction/clients', { params })
  },

  /**
   * 获取指定客户的交易记录
   * @param {string} groupId - 客户集团号
   * @param {Object} params - 查询参数
   */
  getClientTransactions(groupId, params = {}) {
    return request.get(`/api/transaction/clients/${groupId}/transactions`, { params })
  },

  /**
   * 删除客户交易记录
   * @param {string} groupId - 客户集团号
   */
  deleteClientTransactions(groupId) {
    return request.delete(`/api/transaction/clients/${groupId}`)
  },

  /**
   * 获取交易统计信息
   * @param {Object} params - 查询参数
   */
  getTransactionStats(params = {}) {
    return request.get('/api/transaction/stats', { params })
  },

  /**
   * 获取客户详细交易分析
   * @param {string} groupId - 客户集团号
   */
  getClientAnalysis(groupId) {
    return request.get(`/api/transaction/clients/${groupId}/analysis`)
  }
}

export default transactionAPI