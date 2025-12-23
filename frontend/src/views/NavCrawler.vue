<template>
  <div class="nav-crawler-page">
    <!-- 页面标题 -->
    <el-page-header @back="() => $router.go(-1)">
      <template #content>
        <div class="page-title">
          <h2>净值抓取</h2>
          <p>从诺亚CRM系统抓取基金净值数据</p>
        </div>
      </template>
    </el-page-header>

    <el-tabs v-model="activeTab" style="margin-top: 20px">
      <!-- Tab 1: 净值抓取 -->
      <el-tab-pane label="净值抓取" name="crawler">
        <el-card class="token-card">
          <template #header>
            <div class="card-header">
              <span>认证配置</span>
              <el-button
                type="primary"
                size="small"
                @click="updateMappings"
                :loading="updatingMappings"
              >
                从配置文件更新映射
              </el-button>
            </div>
          </template>

          <el-form label-width="150px">
            <el-form-item label="Access Token">
              <el-input
                v-model="accessToken"
                type="textarea"
                :rows="3"
                placeholder="请粘贴从Request Headers中复制的 access-token 值"
              />
            </el-form-item>
            <el-form-item label="NFP Token">
              <el-input
                v-model="nfpToken"
                type="textarea"
                :rows="3"
                placeholder="请粘贴从Request Headers中复制的 nfp-token 值"
              />
            </el-form-item>
            <el-form-item label="FC Code">
              <el-input
                v-model="fcCode"
                placeholder="默认: 18814"
                style="width: 200px"
              />
            </el-form-item>
            <el-form-item>
              <el-space>
                <el-button
                  type="primary"
                  @click="saveTokens"
                  :disabled="!accessToken || !nfpToken"
                >
                  保存令牌
                </el-button>
                <el-button
                  type="danger"
                  @click="clearTokens"
                  :disabled="!accessToken && !nfpToken"
                >
                  清除令牌
                </el-button>
                <el-tag v-if="tokensSaved" type="success">已保存到本地</el-tag>
                <el-tag v-else type="info">未保存</el-tag>
              </el-space>
            </el-form-item>
          </el-form>

          <el-divider content-position="left">当前令牌状态</el-divider>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="Access Token">
              <template v-if="accessToken">
                <el-text
                  :type="getTokenExpiry(accessToken)?.includes('已过期') ? 'warning' : 'success'"
                >
                  {{ getTokenExpiry(accessToken) ? `已设置 (${getTokenExpiry(accessToken)})` : '已设置' }}
                </el-text>
              </template>
              <el-text v-else type="info">未设置</el-text>
            </el-descriptions-item>
            <el-descriptions-item label="NFP Token">
              <template v-if="nfpToken">
                <el-text
                  :type="getTokenExpiry(nfpToken)?.includes('已过期') ? 'warning' : 'success'"
                >
                  {{ getTokenExpiry(nfpToken) ? `已设置 (${getTokenExpiry(nfpToken)})` : '已设置' }}
                </el-text>
              </template>
              <el-text v-else type="info">未设置</el-text>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="funds-card" style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>已配置映射的基金 ({{ filteredMappedFunds.length }}/{{ funds.length }})</span>
              <el-button
                type="primary"
                @click="crawlAll"
                :loading="crawling"
                :disabled="!accessToken || !nfpToken || mappedFunds.length === 0"
              >
                批量抓取全部
              </el-button>
            </div>
          </template>

          <!-- 搜索框 -->
          <div class="search-bar" style="margin-bottom: 16px">
            <el-input
              v-model="mappedFundsSearch"
              placeholder="搜索基金代码或基金名称"
              clearable
              style="max-width: 400px"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <el-table
            :data="filteredMappedFunds"
            border
            stripe
            v-loading="loading"
            style="width: 100%"
          >
            <el-table-column
              type="index"
              label="#"
              width="60"
              align="center"
            />
            <el-table-column
              prop="fund_code"
              label="基金代码"
              width="120"
            />
            <el-table-column
              prop="fund_name"
              label="基金名称"
              min-width="200"
              show-overflow-tooltip
            />
            <el-table-column
              prop="noah_product_id"
              label="诺亚产品ID"
              width="450"
              show-overflow-tooltip
            />
            <el-table-column
              label="操作"
              width="150"
              fixed="right"
            >
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click="crawlSingle(row.fund_code)"
                  :loading="crawlingFunds[row.fund_code]"
                  :disabled="!accessToken || !nfpToken"
                >
                  抓取净值
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 抓取结果显示 -->
        <el-card
          v-if="crawlResults.length > 0"
          class="results-card"
          style="margin-top: 20px"
        >
          <template #header>
            <span>抓取结果</span>
          </template>

          <el-timeline>
            <el-timeline-item
              v-for="(result, index) in crawlResults"
              :key="index"
              :timestamp="result.timestamp"
              :type="result.success ? 'success' : 'danger'"
            >
              <el-tag :type="result.success ? 'success' : 'danger'">
                {{ result.fund_code }}
              </el-tag>
              <span style="margin-left: 10px">{{ result.fund_name }}</span>
              <div v-if="result.success" style="margin-top: 8px; color: #67C23A">
                ✓ 成功: 新增 {{ result.created_count }} 条，更新 {{ result.updated_count }} 条
              </div>
              <div v-else style="margin-top: 8px; color: #F56C6C">
                ✗ 失败: {{ result.message }}
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-tab-pane>

      <!-- Tab 2: 产品映射管理 -->
      <el-tab-pane label="产品映射管理" name="mapping">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>基金列表</span>
              <div>
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索基金代码或名称"
                  style="width: 200px; margin-right: 10px"
                  clearable
                />
                <el-button
                  type="danger"
                  @click="batchDeleteFunds"
                  :disabled="selectedFunds.length === 0"
                  style="margin-right: 10px"
                >
                  批量删除 ({{ selectedFunds.length }})
                </el-button>
                <el-button type="primary" @click="showAddFromUrlDialog">
                  从URL添加
                </el-button>
                <el-button type="success" @click="showAddMappingDialog" style="margin-left: 10px">
                  手动添加映射
                </el-button>
              </div>
            </div>
          </template>

          <el-table
            :data="filteredFunds"
            border
            stripe
            v-loading="loading"
            @selection-change="handleSelectionChange"
          >
            <el-table-column
              type="selection"
              width="55"
            />
            <el-table-column
              prop="fund_code"
              label="基金代码"
              width="120"
            />
            <el-table-column
              prop="fund_name"
              label="基金名称"
              min-width="200"
            />
            <el-table-column
              prop="noah_product_id"
              label="诺亚产品ID"
              width="250"
            >
              <template #default="{ row }">
                <el-tag v-if="row.has_mapping" type="success" size="small">
                  {{ row.noah_product_id }}
                </el-tag>
                <el-tag v-else type="info" size="small">未配置</el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="状态"
              width="100"
            >
              <template #default="{ row }">
                <el-tag v-if="row.has_mapping" type="success" size="small">已配置</el-tag>
                <el-tag v-else type="warning" size="small">未配置</el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="操作"
              width="200"
              fixed="right"
            >
              <template #default="{ row }">
                <el-button
                  v-if="row.has_mapping"
                  type="primary"
                  size="small"
                  @click="editMapping(row)"
                >
                  编辑
                </el-button>
                <el-button
                  v-else
                  type="success"
                  size="small"
                  @click="addMapping(row)"
                >
                  配置
                </el-button>
                <el-button
                  v-if="row.has_mapping"
                  type="danger"
                  size="small"
                  @click="deleteMapping(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加/编辑映射对话框 -->
    <el-dialog
      v-model="mappingDialogVisible"
      :title="mappingDialogTitle"
      width="600px"
    >
      <el-form :model="mappingForm" label-width="120px">
        <el-form-item label="基金代码">
          <el-input v-model="mappingForm.fund_code" :disabled="true" />
        </el-form-item>
        <el-form-item label="基金名称" required>
          <el-input
            v-model="mappingForm.fund_name"
            placeholder="请输入基金名称"
          />
        </el-form-item>
        <el-form-item label="诺亚产品ID" required>
          <el-input
            v-model="mappingForm.noah_product_id"
            placeholder="请输入32位UUID，如: f2ad8fae7bfd48e8a22dc347879e8ecc"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px">
            从产品详情页URL中的productId参数获取
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mappingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMappingSubmit" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 从URL添加映射对话框 -->
    <el-dialog
      v-model="urlDialogVisible"
      title="从产品URL添加映射"
      width="700px"
    >
      <el-alert
        title="使用说明"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <p>1. 在诺亚CRM中打开产品详情页</p>
        <p>2. 复制浏览器地址栏中的完整URL</p>
        <p>3. 粘贴到下方输入框，系统将自动提取productId和productCode并创建映射</p>
      </el-alert>

      <el-form label-width="120px">
        <el-form-item label="产品详情页URL" required>
          <el-input
            v-model="productUrl"
            type="textarea"
            :rows="4"
            placeholder="请粘贴完整的产品详情页URL，例如：https://crm.noah-fund.com/#/productManagement/ProductDetailGopher?productId=xxx&productCode=L02045&..."
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="urlDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addMappingFromUrl" :loading="submitting" :disabled="!productUrl">
          提取并保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const activeTab = ref('crawler')
const accessToken = ref('')
const nfpToken = ref('')
const fcCode = ref('18814')
const searchKeyword = ref('')
const mappedFundsSearch = ref('')  // 已配置映射基金的搜索关键词
const tokensSaved = ref(false)

const funds = ref([])
const loading = ref(false)
const crawling = ref(false)
const updatingMappings = ref(false)
const crawlingFunds = ref({})
const crawlResults = ref([])

const mappingDialogVisible = ref(false)
const mappingDialogTitle = ref('')
const mappingForm = ref({
  fund_code: '',
  fund_name: '',
  noah_product_id: ''
})
const submitting = ref(false)

const urlDialogVisible = ref(false)
const productUrl = ref('')
const selectedFunds = ref([])

const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000'

// 本地存储键名
const TOKEN_STORAGE_KEY = 'noah_crm_tokens'

// 保存令牌到本地存储
const saveTokens = () => {
  try {
    const tokens = {
      accessToken: accessToken.value,
      nfpToken: nfpToken.value,
      fcCode: fcCode.value,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens))
    tokensSaved.value = true
    ElMessage.success('令牌已保存到本地浏览器')
  } catch (error) {
    console.error('保存令牌失败:', error)
    ElMessage.error('保存令牌失败')
  }
}

// 从本地存储加载令牌
const loadTokens = () => {
  try {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (stored) {
      const tokens = JSON.parse(stored)
      accessToken.value = tokens.accessToken || ''
      nfpToken.value = tokens.nfpToken || ''
      fcCode.value = tokens.fcCode || '18814'
      tokensSaved.value = true
      ElMessage.success('已从本地加载保存的令牌')
    }
  } catch (error) {
    console.error('加载令牌失败:', error)
  }
}

// 清除令牌
const clearTokens = () => {
  ElMessageBox.confirm('确定要清除保存的令牌吗？', '确认清除', {
    confirmButtonText: '清除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    accessToken.value = ''
    nfpToken.value = ''
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    tokensSaved.value = false
    ElMessage.success('令牌已清除')
  }).catch(() => {
    // 用户取消
  })
}

// 监听token变化，更新保存状态
watch([accessToken, nfpToken], () => {
  try {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (stored) {
      const tokens = JSON.parse(stored)
      tokensSaved.value = (
        tokens.accessToken === accessToken.value &&
        tokens.nfpToken === nfpToken.value
      )
    } else {
      tokensSaved.value = false
    }
  } catch (error) {
    tokensSaved.value = false
  }
})

// 解析JWT token获取过期时间
const getTokenExpiry = (token) => {
  if (!token) return null

  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null

    const payload = JSON.parse(atob(parts[1]))
    if (payload.exp) {
      const expDate = new Date(payload.exp * 1000)
      const now = new Date()

      if (expDate < now) {
        return '已过期，请重新获取'
      }

      const days = Math.floor((expDate - now) / (1000 * 60 * 60 * 24))
      if (days > 0) {
        return `有效期剩余${days}天`
      } else {
        const hours = Math.floor((expDate - now) / (1000 * 60 * 60))
        return `有效期剩余${hours}小时`
      }
    }
    return null
  } catch (error) {
    return null
  }
}

// 计算属性：已配置映射的基金
const mappedFunds = computed(() => {
  // 后端已按基金代码降序排列，直接过滤即可
  return funds.value.filter(f => f.has_mapping)
})

// 计算属性：已配置映射基金的搜索过滤
const filteredMappedFunds = computed(() => {
  if (!mappedFundsSearch.value) {
    return mappedFunds.value
  }
  const keyword = mappedFundsSearch.value.toLowerCase()
  return mappedFunds.value.filter(f =>
    f.fund_code.toLowerCase().includes(keyword) ||
    f.fund_name.toLowerCase().includes(keyword)
  )
})

// 计算属性：搜索过滤后的基金列表
const filteredFunds = computed(() => {
  if (!searchKeyword.value) {
    return funds.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return funds.value.filter(f =>
    f.fund_code.toLowerCase().includes(keyword) ||
    f.fund_name.toLowerCase().includes(keyword)
  )
})

// 加载基金列表
const loadMappedFunds = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/nav-crawler/mapped-funds`)
    if (response.data.success) {
      funds.value = response.data.data.funds
      const mappedCount = response.data.data.mapped_count
      ElMessage.success(`加载了 ${funds.value.length} 个基金，其中 ${mappedCount} 个已配置映射`)
    }
  } catch (error) {
    console.error('加载基金列表失败:', error)
    ElMessage.error('加载基金列表失败')
  } finally {
    loading.value = false
  }
}

// 从配置文件更新产品映射
const updateMappings = async () => {
  updatingMappings.value = true
  try {
    const response = await axios.post(`${API_BASE}/api/nav-crawler/update-mappings`)
    if (response.data.success) {
      ElMessage.success(response.data.message)
      await loadMappedFunds()
    }
  } catch (error) {
    console.error('更新映射失败:', error)
    ElMessage.error('更新映射失败')
  } finally {
    updatingMappings.value = false
  }
}

// 显示添加映射对话框
const showAddMappingDialog = () => {
  mappingDialogTitle.value = '添加产品映射'
  mappingForm.value = {
    fund_code: '',
    fund_name: '',
    noah_product_id: ''
  }
  mappingDialogVisible.value = true
}

// 显示从URL添加映射对话框
const showAddFromUrlDialog = () => {
  productUrl.value = ''
  urlDialogVisible.value = true
}

// 从URL添加映射
const addMappingFromUrl = async () => {
  if (!productUrl.value) {
    ElMessage.warning('请输入产品URL')
    return
  }

  submitting.value = true
  try {
    const response = await axios.post(`${API_BASE}/api/nav-crawler/add-mapping-from-url`, {
      url: productUrl.value
    })

    if (response.data.success) {
      const data = response.data.data
      ElMessage.success(
        `成功提取并保存：${data.fund_code} (${data.fund_name})\n` +
        `Product ID: ${data.noah_product_id}`
      )
      urlDialogVisible.value = false
      productUrl.value = ''
      await loadMappedFunds()
    }
  } catch (error) {
    console.error('从URL添加映射失败:', error)
    const errorMsg = error.response?.data?.detail || '从URL添加映射失败'
    ElMessage.error(errorMsg)
  } finally {
    submitting.value = false
  }
}

// 添加映射
const addMapping = (fund) => {
  mappingDialogTitle.value = `配置产品映射 - ${fund.fund_code}`
  mappingForm.value = {
    fund_code: fund.fund_code,
    fund_name: fund.fund_name,
    noah_product_id: ''
  }
  mappingDialogVisible.value = true
}

// 编辑映射
const editMapping = (fund) => {
  mappingDialogTitle.value = `编辑产品映射 - ${fund.fund_code}`
  mappingForm.value = {
    fund_code: fund.fund_code,
    fund_name: fund.fund_name,
    noah_product_id: fund.noah_product_id
  }
  mappingDialogVisible.value = true
}

// 保存映射
const saveMappingSubmit = async () => {
  if (!mappingForm.value.fund_name) {
    ElMessage.warning('请输入基金名称')
    return
  }

  if (!mappingForm.value.noah_product_id) {
    ElMessage.warning('请输入诺亚产品ID')
    return
  }

  submitting.value = true
  try {
    const response = await axios.post(`${API_BASE}/api/nav-crawler/add-mapping`, {
      fund_code: mappingForm.value.fund_code,
      fund_name: mappingForm.value.fund_name,
      noah_product_id: mappingForm.value.noah_product_id
    })

    if (response.data.success) {
      ElMessage.success(response.data.message)
      mappingDialogVisible.value = false
      await loadMappedFunds()
    }
  } catch (error) {
    console.error('保存映射失败:', error)
    const errorMsg = error.response?.data?.detail || '保存映射失败'
    ElMessage.error(errorMsg)
  } finally {
    submitting.value = false
  }
}

// 删除映射
const deleteMapping = async (fund) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除基金 ${fund.fund_code} 的产品ID映射吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await axios.delete(`${API_BASE}/api/nav-crawler/mapping/${fund.fund_code}`)

    if (response.data.success) {
      ElMessage.success(response.data.message)
      await loadMappedFunds()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除映射失败:', error)
      const errorMsg = error.response?.data?.detail || '删除映射失败'
      ElMessage.error(errorMsg)
    }
  }
}

// 处理表格选中变化
const handleSelectionChange = (selection) => {
  selectedFunds.value = selection
}

// 批量删除基金
const batchDeleteFunds = async () => {
  if (selectedFunds.value.length === 0) {
    ElMessage.warning('请先选择要删除的基金')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedFunds.value.length} 个基金吗？此操作不可恢复！`,
      '确认批量删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 批量删除逻辑
    let successCount = 0
    let failedCount = 0

    for (const fund of selectedFunds.value) {
      try {
        const response = await axios.delete(`${API_BASE}/api/funds/${fund.fund_code}`)
        if (response.data.success) {
          successCount++
        } else {
          failedCount++
        }
      } catch (error) {
        console.error(`删除基金 ${fund.fund_code} 失败:`, error)
        failedCount++
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功删除 ${successCount} 个基金${failedCount > 0 ? `，失败 ${failedCount} 个` : ''}`)
      selectedFunds.value = []
      await loadMappedFunds()
    } else {
      ElMessage.error('批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 抓取单个基金
const crawlSingle = async (fundCode) => {
  if (!accessToken.value || !nfpToken.value) {
    ElMessage.warning('请先配置认证令牌')
    return
  }

  crawlingFunds.value[fundCode] = true

  try {
    const response = await axios.post(`${API_BASE}/api/nav-crawler/crawl/single`, {
      fund_code: fundCode,
      access_token: accessToken.value,
      nfp_token: nfpToken.value
    })

    if (response.data.success) {
      const result = response.data.data
      crawlResults.value.unshift({
        timestamp: new Date().toLocaleString(),
        success: true,
        fund_code: result.fund_code,
        fund_name: result.fund_name,
        created_count: result.created_count,
        updated_count: result.updated_count
      })
      ElMessage.success(
        `${fundCode} 净值抓取成功！\n` +
        `新增 ${result.created_count} 条，更新 ${result.updated_count} 条`
      )
    }
  } catch (error) {
    console.error('抓取失败:', error)
    const errorMsg = error.response?.data?.detail || '抓取失败'
    crawlResults.value.unshift({
      timestamp: new Date().toLocaleString(),
      success: false,
      fund_code: fundCode,
      fund_name: '',
      message: errorMsg
    })
    ElMessage.error(`${fundCode} 抓取失败: ${errorMsg}`)
  } finally {
    crawlingFunds.value[fundCode] = false
  }
}

// 批量抓取所有基金
const crawlAll = async () => {
  if (!accessToken.value || !nfpToken.value) {
    ElMessage.warning('请先配置认证令牌')
    return
  }

  crawling.value = true
  ElMessage.info('开始批量抓取，请稍候...')

  try {
    const response = await axios.post(`${API_BASE}/api/nav-crawler/crawl/batch`, {
      fund_codes: null,
      access_token: accessToken.value,
      nfp_token: nfpToken.value
    })

    if (response.data.success) {
      const result = response.data.data

      result.results.forEach(r => {
        crawlResults.value.unshift({
          timestamp: new Date().toLocaleString(),
          success: r.success,
          fund_code: r.fund_code,
          fund_name: r.fund_name || '',
          created_count: r.created_count || 0,
          updated_count: r.updated_count || 0,
          message: r.message || ''
        })
      })

      ElMessage.success(
        `批量抓取完成！共 ${result.total_funds} 个基金，` +
        `新增 ${result.total_created} 条，更新 ${result.total_updated} 条`
      )
    }
  } catch (error) {
    console.error('批量抓取失败:', error)
    const errorMsg = error.response?.data?.detail || '批量抓取失败'
    ElMessage.error(errorMsg)
  } finally {
    crawling.value = false
  }
}

onMounted(() => {
  loadMappedFunds()
  loadTokens()
})
</script>

<style scoped>
.nav-crawler-page {
  padding: 20px;
}

.page-title h2 {
  margin: 0;
  color: #303133;
}

.page-title p {
  margin: 4px 0 0 0;
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-alert p {
  margin: 4px 0;
  line-height: 1.6;
}
</style>
