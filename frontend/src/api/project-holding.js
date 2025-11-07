/**
 * 项目持仓分析API接口
 * Project Holding Analysis API
 */
import request from './index'

const projectHoldingAPI = {
  // 获取项目列表
  getProjectList: () => request.get('/api/project-holding/projects'),
  
  // 获取项目持仓详情
  getProjectDetail: (projectName) => request.get(`/api/project-holding/${encodeURIComponent(projectName)}`),
  
  // 创建资产配置记录
  createAssetRecord: (projectName, data) => 
    request.post(`/api/project-holding/${encodeURIComponent(projectName)}/asset`, data),
  
  // 创建行业配置记录
  createIndustryRecord: (projectName, data) => 
    request.post(`/api/project-holding/${encodeURIComponent(projectName)}/industry`, data),
  
  // 更新资产配置记录
  updateAssetRecord: (recordId, data) => 
    request.put(`/api/project-holding/asset/${recordId}`, data),
  
  // 更新行业配置记录
  updateIndustryRecord: (recordId, data) => 
    request.put(`/api/project-holding/industry/${recordId}`, data),
  
  // 删除资产配置记录
  deleteAssetRecord: (recordId) => 
    request.delete(`/api/project-holding/asset/${recordId}`),
  
  // 删除行业配置记录
  deleteIndustryRecord: (recordId) => 
    request.delete(`/api/project-holding/industry/${recordId}`),
  
  // 获取项目持仓分析
  getProjectAnalysis: (projectName, params = {}) => {
    const query = new URLSearchParams()
    if (params.startMonth) query.append('start_month', params.startMonth)
    if (params.endMonth) query.append('end_month', params.endMonth)
    
    const queryString = query.toString()
    const url = `/api/project-holding/${encodeURIComponent(projectName)}/analysis${queryString ? '?' + queryString : ''}`
    
    return request.get(url)
  },

  // 删除项目
  deleteProject: (projectName) => 
    request.delete(`/api/project-holding/projects/${encodeURIComponent(projectName)}`)
}

export default projectHoldingAPI