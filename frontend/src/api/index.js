import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: 'http://localhost:8001',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 可以在这里添加token等认证信息
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('响应错误:', error)
    
    // 统一错误处理
    const { response } = error
    let message = '请求失败'
    
    if (response) {
      switch (response.status) {
        case 400:
          message = response.data?.detail || '请求参数错误'
          break
        case 404:
          message = response.data?.detail?.error || '资源未找到'
          break
        case 500:
          message = response.data?.detail?.error || '服务器内部错误'
          break
        default:
          message = `请求失败 (${response.status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时，请重试'
    } else {
      message = '网络错误，请检查网络连接'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request