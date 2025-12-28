/**
 * 实盘组合API接口封装
 * Portfolio API
 */

import request from './index'

export default {
  // ========== 组合管理 ==========

  /**
   * 创建组合
   * @param {Object} data - 组合数据
   * @param {string} data.portfolio_name - 组合名称
   * @param {string} data.description - 组合描述
   * @param {number} data.initial_amount - 初始金额
   */
  createPortfolio(data) {
    return request({
      url: '/api/portfolio',
      method: 'post',
      data
    })
  },

  /**
   * 获取组合列表
   * @param {Object} params - 查询参数
   * @param {boolean} params.is_active - 是否激活
   */
  getPortfolioList(params) {
    return request({
      url: '/api/portfolio',
      method: 'get',
      params
    })
  },

  /**
   * 获取组合详情
   * @param {number} portfolioId - 组合ID
   */
  getPortfolioDetail(portfolioId) {
    return request({
      url: `/api/portfolio/${portfolioId}`,
      method: 'get'
    })
  },

  /**
   * 更新组合
   * @param {number} portfolioId - 组合ID
   * @param {Object} data - 更新数据
   */
  updatePortfolio(portfolioId, data) {
    return request({
      url: `/api/portfolio/${portfolioId}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除组合
   * @param {number} portfolioId - 组合ID
   */
  deletePortfolio(portfolioId) {
    return request({
      url: `/api/portfolio/${portfolioId}`,
      method: 'delete'
    })
  },

  // ========== 交易管理 ==========

  /**
   * 添加交易记录
   * @param {number} portfolioId - 组合ID
   * @param {Object} data - 交易数据
   * @param {string} data.fund_code - 基金代码
   * @param {string} data.transaction_type - 交易类型 buy/sell
   * @param {string} data.transaction_date - 交易日期
   * @param {number} data.amount - 交易金额
   * @param {number} data.shares - 交易份额
   * @param {number} data.nav - 交易净值
   * @param {number} data.fee - 手续费
   * @param {string} data.note - 备注
   */
  addTransaction(portfolioId, data) {
    return request({
      url: `/api/portfolio/${portfolioId}/transaction`,
      method: 'post',
      data
    })
  },

  /**
   * 获取交易记录
   * @param {number} portfolioId - 组合ID
   * @param {Object} params - 查询参数
   * @param {number} params.limit - 返回记录数量
   */
  getTransactions(portfolioId, params) {
    return request({
      url: `/api/portfolio/${portfolioId}/transactions`,
      method: 'get',
      params
    })
  },

  /**
   * 删除交易记录
   * @param {number} portfolioId - 组合ID
   * @param {number} transactionId - 交易ID
   */
  deleteTransaction(portfolioId, transactionId) {
    return request({
      url: `/api/portfolio/${portfolioId}/transaction/${transactionId}`,
      method: 'delete'
    })
  },

  // ========== 净值管理 ==========

  /**
   * 保存净值快照
   * @param {number} portfolioId - 组合ID
   * @param {Object} params - 参数
   * @param {string} params.nav_date - 净值日期
   */
  savePortfolioNav(portfolioId, params) {
    return request({
      url: `/api/portfolio/${portfolioId}/nav`,
      method: 'post',
      params
    })
  },

  /**
   * 获取净值历史
   * @param {number} portfolioId - 组合ID
   * @param {Object} params - 查询参数
   * @param {string} params.start_date - 开始日期
   * @param {string} params.end_date - 结束日期
   */
  getNavHistory(portfolioId, params) {
    return request({
      url: `/api/portfolio/${portfolioId}/nav-history`,
      method: 'get',
      params
    })
  }
}
