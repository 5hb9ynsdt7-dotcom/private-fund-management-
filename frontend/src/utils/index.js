/**
 * 通用工具函数
 */

import { ElMessage } from 'element-plus'

/**
 * 日期格式化工具
 */
export const formatDate = (date, format = 'YYYY-MM-DD') => {
  if (!date) return ''
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  
  switch (format) {
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`
    case 'YYYY年MM月DD日':
      return `${year}年${month}月${day}日`
    case 'MM/DD/YYYY':
      return `${month}/${day}/${year}`
    default:
      return `${year}-${month}-${day}`
  }
}

/**
 * 数字格式化工具
 */
export const formatNumber = (number, decimals = 2, showSign = false) => {
  if (number === null || number === undefined || isNaN(number)) return '--'
  
  const num = Number(number)
  const formatted = num.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
  
  if (showSign && num > 0) {
    return `+${formatted}`
  }
  return formatted
}

/**
 * 货币格式化
 */
export const formatCurrency = (amount, currency = '¥') => {
  if (amount === null || amount === undefined || isNaN(amount)) return '--'
  
  const num = Number(amount)
  const formatted = Math.abs(num).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
  
  return `${currency}${num >= 0 ? '' : '-'}${formatted}`
}

/**
 * 百分比格式化
 */
export const formatPercent = (value, decimals = 2, showSign = false) => {
  if (value === null || value === undefined || isNaN(value)) return '--'
  
  const num = Number(value)
  const formatted = num.toFixed(decimals)
  
  if (showSign && num > 0) {
    return `+${formatted}%`
  }
  return `${formatted}%`
}

/**
 * 文件大小格式化
 */
export const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
}

/**
 * 防抖函数
 */
export const debounce = (func, wait = 300) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 节流函数
 */
export const throttle = (func, limit = 300) => {
  let inThrottle
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 深拷贝
 */
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime())
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  if (obj instanceof Object) {
    const clonedObj = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
}

/**
 * 下载文件
 */
export const downloadFile = (data, filename, type = 'application/octet-stream') => {
  const blob = new Blob([data], { type })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

/**
 * 复制到剪贴板
 */
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('复制成功')
    return true
  } catch (err) {
    console.error('复制失败:', err)
    ElMessage.error('复制失败')
    return false
  }
}

/**
 * 生成唯一ID
 */
export const generateId = () => {
  return Math.random().toString(36).substring(2) + Date.now().toString(36)
}

/**
 * 获取文件扩展名
 */
export const getFileExtension = (filename) => {
  return filename.slice((filename.lastIndexOf('.') - 1 >>> 0) + 2)
}

/**
 * 验证文件类型
 */
export const validateFileType = (file, allowedTypes = []) => {
  if (!allowedTypes.length) return true
  
  const extension = getFileExtension(file.name).toLowerCase()
  return allowedTypes.includes(extension)
}

/**
 * 表格排序比较函数
 */
export const sortCompare = (a, b, key, order = 'asc') => {
  let aVal = a[key]
  let bVal = b[key]
  
  // 处理null/undefined
  if (aVal === null || aVal === undefined) aVal = ''
  if (bVal === null || bVal === undefined) bVal = ''
  
  // 数字比较
  if (typeof aVal === 'number' && typeof bVal === 'number') {
    return order === 'asc' ? aVal - bVal : bVal - aVal
  }
  
  // 字符串比较
  aVal = String(aVal).toLowerCase()
  bVal = String(bVal).toLowerCase()
  
  if (order === 'asc') {
    return aVal.localeCompare(bVal)
  } else {
    return bVal.localeCompare(aVal)
  }
}