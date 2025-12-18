/**
 * 基准指数数据获取工具
 * 数据来源：Tushare Pro API（本地持久化存储 + 增量更新）
 */

// 指数定义（与后端 Tushare 服务保持一致）
const INDICES = [
  { name: '沪深300', code: '000300.SH' },
  { name: '中证500', code: '000905.SH' },
  { name: '中证1000', code: '000852.SH' },
  { name: '中证A500', code: '000510.SH' },
  { name: '中证800', code: '000906.SH' },
  { name: '中证2000', code: '932000.CSI' },
  { name: '上证指数', code: '000001.SH' },
]

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * 检查并初始化指数数据（首次使用）
 * @param {string} indexCode - 指数代码
 * @returns {Promise<boolean>} 是否成功初始化
 */
async function ensureIndexInitialized(indexCode) {
  try {
    // 先检查指数状态
    const statusResponse = await fetch(`${API_BASE_URL}/api/tushare/indices/status`)
    if (!statusResponse.ok) {
      console.error(`获取指数状态失败: ${statusResponse.status}`)
      return false
    }

    const statusData = await statusResponse.json()
    const indexStatus = statusData.data?.find(item => item.ts_code === indexCode)

    // 如果已有数据，直接返回成功
    if (indexStatus && indexStatus.total_records > 0) {
      console.log(`✓ 指数 ${indexCode} 已初始化，共 ${indexStatus.total_records} 条记录`)
      return true
    }

    // 如果没有数据，执行初始化
    console.log(`正在初始化指数 ${indexCode}...`)
    const initResponse = await fetch(
      `${API_BASE_URL}/api/tushare/indices/${indexCode}/initialize`,
      { method: 'POST' }
    )

    if (!initResponse.ok) {
      console.error(`初始化指数失败: ${initResponse.status}`)
      return false
    }

    const initData = await initResponse.json()
    console.log(`✓ 初始化成功:`, initData)
    return initData.status === 'success'

  } catch (error) {
    console.error(`初始化指数异常: ${indexCode}`, error)
    return false
  }
}

/**
 * 获取指数历史数据（从 Tushare Pro API，本地持久化存储）
 * @param {string} indexCode - 指数代码（如 '000905.SH'）
 * @param {string} startDate - 开始日期（可选），格式 'YYYY-MM-DD'
 * @param {string} endDate - 结束日期（可选），格式 'YYYY-MM-DD'
 * @returns {Promise<Array>} 返回格式: [{date: '2024-12-27', value: 5899.17}, ...]
 */
export async function fetchBenchmarkData(indexCode, startDate = null, endDate = null) {
  try {
    console.log(`正在从 Tushare 获取指数 ${indexCode} 数据...`)

    // 1. 确保指数已初始化
    const initialized = await ensureIndexInitialized(indexCode)
    if (!initialized) {
      console.error(`指数 ${indexCode} 初始化失败`)
      return []
    }

    // 2. 尝试增量更新数据
    try {
      const updateResponse = await fetch(
        `${API_BASE_URL}/api/tushare/indices/${indexCode}/update`,
        { method: 'POST' }
      )
      if (updateResponse.ok) {
        const updateData = await updateResponse.json()
        console.log(`更新结果:`, updateData.message)
      }
    } catch (updateError) {
      console.warn(`增量更新失败（跳过）:`, updateError.message)
    }

    // 3. 获取本地存储的数据
    let url = `${API_BASE_URL}/api/tushare/indices/${indexCode}/data`
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    if (params.toString()) url += `?${params.toString()}`

    const dataResponse = await fetch(url)
    if (!dataResponse.ok) {
      console.error(`获取指数数据失败: ${dataResponse.status}`)
      return []
    }

    const result = await dataResponse.json()

    if (result.status !== 'success' || !result.data) {
      console.error(`指数 ${indexCode} 无数据`)
      return []
    }

    const benchmarkData = result.data

    console.log(`✓ 成功获取指数 ${indexCode} 数据，共 ${benchmarkData.length} 条`)
    if (benchmarkData.length > 0) {
      console.log(`  首条: ${benchmarkData[0].date} = ${benchmarkData[0].value}`)
      console.log(`  末条: ${benchmarkData[benchmarkData.length - 1].date} = ${benchmarkData[benchmarkData.length - 1].value}`)
    }

    return benchmarkData

  } catch (error) {
    console.error(`✗ 获取指数 ${indexCode} 数据异常:`, error)
    return []
  }
}

/**
 * 批量获取多个指数的数据
 * @param {Array<string>} indexCodes - 指数代码数组
 * @returns {Promise<Object>} 返回格式: {indexCode: [{date, value}, ...]}
 */
export async function fetchMultipleBenchmarks(indexCodes) {
  const uniqueCodes = [...new Set(indexCodes.filter(code => code))]

  // 并发获取所有指数数据
  const promises = uniqueCodes.map(code => fetchBenchmarkData(code))
  const results = await Promise.all(promises)

  // 构建映射对象
  const indexDataMap = {}
  uniqueCodes.forEach((code, index) => {
    indexDataMap[code] = results[index]
  })

  return indexDataMap
}

// 导出指数定义，供其他模块使用
export { INDICES }
