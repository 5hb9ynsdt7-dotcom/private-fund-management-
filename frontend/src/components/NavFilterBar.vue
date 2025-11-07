<template>
  <div class="nav-filter-bar">
    <el-form inline size="default" class="filter-form">
      <el-form-item label="基金代码">
        <el-input
          v-model="fundCodeFilter"
          placeholder="输入基金代码"
          clearable
          style="width: 200px"
          @input="handleFilter"
          @keyup.enter="handleFilter"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      
      <el-form-item label="基金名称">
        <el-input
          v-model="fundNameFilter"
          placeholder="输入基金名称"
          clearable
          style="width: 200px"
          @input="handleFilter"
          @keyup.enter="handleFilter"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="handleFilter">
          <el-icon><Search /></el-icon>
          筛选当前页
        </el-button>
        
        <el-button type="success" @click="handleShowAll" :disabled="!hasFilter">
          <el-icon><View /></el-icon>
          显示所有记录
        </el-button>
        
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </el-form-item>
    </el-form>
    
    <!-- 筛选结果提示 -->
    <div v-if="hasFilter" class="filter-info">
      <el-alert
        :title="filterSummaryText"
        type="info"
        :closable="false"
        show-icon
        size="small"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'

const emit = defineEmits(['filter', 'reset', 'show-all'])

// 筛选文本
const fundCodeFilter = ref('')
const fundNameFilter = ref('')

// 是否有筛选条件
const hasFilter = computed(() => {
  return fundCodeFilter.value.trim() || fundNameFilter.value.trim()
})

// 筛选摘要文本
const filterSummaryText = computed(() => {
  const filters = []
  if (fundCodeFilter.value.trim()) {
    filters.push(`基金代码: ${fundCodeFilter.value}`)
  }
  if (fundNameFilter.value.trim()) {
    filters.push(`基金名称: ${fundNameFilter.value}`)
  }
  return `正在筛选 ${filters.join('、')} 的记录`
})

// 表格过滤函数
const filterTable = () => {
  const fundCodeTerm = fundCodeFilter.value.toLowerCase().trim()
  const fundNameTerm = fundNameFilter.value.toLowerCase().trim()
  
  // 等待DOM更新后再执行筛选
  nextTick(() => {
    // 尝试多种选择器来找到表格
    const possibleSelectors = [
      '.el-table__body-wrapper tbody tr',
      '.el-table__body tbody tr', 
      '.el-table tbody tr',
      'table tbody tr'
    ]
    
    let rows = null
    for (const selector of possibleSelectors) {
      rows = document.querySelectorAll(selector)
      if (rows.length > 0) {
        console.log(`找到表格行，使用选择器: ${selector}`)
        break
      }
    }
    
    if (!rows || rows.length === 0) {
      console.warn('未找到表格行元素')
      return
    }
    
    let visibleCount = 0
    
    rows.forEach((row, index) => {
      let fundCodeText = ''
      let fundNameText = ''
      
      // 获取基金代码和基金名称列
      if (row.cells && row.cells.length > 0) {
        // 表格结构：选择列(0) + 序号列(1) + 基金代码列(2) + 基金名称列(3) + 其他列...
        
        // 基金代码在第3列（索引2）
        if (row.cells[2]) {
          fundCodeText = row.cells[2].textContent || row.cells[2].innerText
        }
        
        // 基金名称在第4列（索引3）
        if (row.cells[3]) {
          fundNameText = row.cells[3].textContent || row.cells[3].innerText
        }
        
        // 如果基金代码列没有找到，尝试查找包含基金代码格式的单元格
        if (!fundCodeText) {
          for (let i = 0; i < row.cells.length; i++) {
            const cellText = row.cells[i].textContent || row.cells[i].innerText
            if (cellText && /L\d{5}/.test(cellText)) { // 基金代码格式匹配
              fundCodeText = cellText
              break
            }
          }
        }
        
        // 如果基金名称列没有找到，尝试查找包含中文的较长文本单元格
        if (!fundNameText) {
          for (let i = 0; i < row.cells.length; i++) {
            const cellText = row.cells[i].textContent || row.cells[i].innerText
            if (cellText && cellText.length > 10 && /[\u4e00-\u9fa5]/.test(cellText)) { // 包含中文且长度大于10
              fundNameText = cellText
              break
            }
          }
        }
      }
      
      if (fundCodeText || fundNameText) {
        const fundCode = fundCodeText.toLowerCase().trim()
        const fundName = fundNameText.toLowerCase().trim()
        
        // 检查是否匹配筛选条件
        let shouldShow = true
        
        if (fundCodeTerm) {
          shouldShow = shouldShow && fundCode.includes(fundCodeTerm)
        }
        
        if (fundNameTerm) {
          shouldShow = shouldShow && fundName.includes(fundNameTerm)
        }
        
        row.style.display = shouldShow ? '' : 'none'
        if (shouldShow) visibleCount++
        
        // 调试日志（仅显示前几行）
        if (index < 3) {
          console.log(`行 ${index}: 基金代码="${fundCode}", 基金名称="${fundName}", 筛选条件(代码:"${fundCodeTerm}", 名称:"${fundNameTerm}"), 显示=${shouldShow}`)
        }
      }
    })
    
    console.log(`筛选完成: 显示 ${visibleCount} 行，隐藏 ${rows.length - visibleCount} 行`)
  })
}

// 处理筛选
const handleFilter = () => {
  filterTable()
  emit('filter', { fundCode: fundCodeFilter.value, fundName: fundNameFilter.value })
}

// 处理显示所有记录
const handleShowAll = () => {
  if (!hasFilter.value) {
    console.warn('请先输入筛选条件')
    return
  }
  
  console.log('显示所有记录:', { fundCode: fundCodeFilter.value, fundName: fundNameFilter.value })
  // 优先使用基金代码，如果没有则使用基金名称
  const searchTerm = fundCodeFilter.value.trim() || fundNameFilter.value.trim()
  emit('show-all', searchTerm)
}

// 处理重置
const handleReset = () => {
  fundCodeFilter.value = ''
  fundNameFilter.value = ''
  filterTable()
  emit('reset')
}
</script>

<style scoped>
.nav-filter-bar {
  margin-bottom: 16px;
}

.filter-form {
  margin-bottom: 0;
}

.filter-info {
  margin-top: 8px;
}

/* 表单项间距调整 */
.el-form-item {
  margin-bottom: 12px;
  margin-right: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .nav-filter-bar {
    margin-bottom: 12px;
  }
  
  .filter-form {
    display: block;
  }
  
  .filter-form .el-form-item {
    display: block;
    margin-right: 0;
    margin-bottom: 12px;
  }
  
  .filter-form .el-form-item .el-input {
    width: 100% !important;
  }
}
</style>