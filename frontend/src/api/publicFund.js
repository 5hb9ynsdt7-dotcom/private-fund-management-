/**
 * 公募基金API接口封装
 * Public Fund API
 */

import request from './index'

export default {
  // ========== 基金主数据管理 ==========

  /**
   * 获取基金列表
   * @param {Object} params - 查询参数
   * @param {string} params.keyword - 搜索关键词（基金代码或名称）
   * @param {string} params.fund_type - 基金类型
   * @param {string} params.fund_company - 基金公司
   * @param {boolean} params.is_active - 是否仅查询活跃基金
   * @param {number} params.page - 页码
   * @param {number} params.page_size - 每页数量
   */
  getFundList(params) {
    return request({
      url: '/api/public-fund/funds',
      method: 'get',
      params
    })
  },

  /**
   * 获取基金详情
   * @param {string} fundCode - 基金代码
   */
  getFundDetail(fundCode) {
    return request({
      url: `/api/public-fund/funds/${fundCode}`,
      method: 'get'
    })
  },

  /**
   * 手动创建基金
   * @param {Object} data - 基金数据
   */
  createFund(data) {
    return request({
      url: '/api/public-fund/funds',
      method: 'post',
      data
    })
  },

  /**
   * 自动抓取基金信息
   * @param {string} fundCode - 基金代码
   */
  fetchFund(fundCode) {
    return request({
      url: `/api/public-fund/funds/fetch/${fundCode}`,
      method: 'post'
    })
  },

  /**
   * 更新基金信息
   * @param {string} fundCode - 基金代码
   * @param {Object} data - 更新数据
   */
  updateFund(fundCode, data) {
    return request({
      url: `/api/public-fund/funds/${fundCode}`,
      method: 'put',
      data
    })
  },

  /**
   * 删除基金
   * @param {string} fundCode - 基金代码
   */
  deleteFund(fundCode) {
    return request({
      url: `/api/public-fund/funds/${fundCode}`,
      method: 'delete'
    })
  },

  // ========== 净值数据管理 ==========

  /**
   * 获取基金净值列表
   * @param {string} fundCode - 基金代码
   * @param {Object} params - 查询参数
   * @param {string} params.start_date - 开始日期
   * @param {string} params.end_date - 结束日期
   * @param {string} params.sort - 排序方式 asc/desc
   */
  getNavList(fundCode, params) {
    return request({
      url: `/api/public-fund/nav/${fundCode}`,
      method: 'get',
      params
    })
  },

  /**
   * 手动录入净值
   * @param {Object} data - 净值数据
   */
  createNav(data) {
    return request({
      url: '/api/public-fund/nav',
      method: 'post',
      data
    })
  },

  /**
   * 批量上传净值（Excel）
   * @param {File} file - Excel文件
   */
  uploadNav(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: '/api/public-fund/nav/upload',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 批量删除净值
   * @param {Array<number>} navIds - 净值记录ID列表
   */
  deleteNavBatch(navIds) {
    return request({
      url: '/api/public-fund/nav/batch',
      method: 'delete',
      params: {
        nav_ids: navIds
      }
    })
  },

  /**
   * 计算日收益率
   * @param {string} fundCode - 基金代码
   */
  calculateReturns(fundCode) {
    return request({
      url: `/api/public-fund/nav/calculate-returns/${fundCode}`,
      method: 'post'
    })
  },

  /**
   * 刷新基金净值
   * @param {string} fundCode - 基金代码
   */
  refreshNav(fundCode) {
    return request({
      url: `/api/public-fund/nav/refresh/${fundCode}`,
      method: 'post'
    })
  },

  // ========== 投研分析 ==========

  /**
   * 单基金分析
   * @param {Object} data - 分析参数
   * @param {string} data.fund_code - 基金代码
   * @param {string} data.start_date - 开始日期
   * @param {string} data.end_date - 结束日期
   * @param {string} data.benchmark_code - 基准代码（可选）
   * @param {boolean} data.save_result - 是否保存结果
   */
  analyzeSingleFund(data) {
    return request({
      url: '/api/public-fund/analysis/single',
      method: 'post',
      data
    })
  }
}
