<template>
  <div class="quantitative-analysis-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>量化分析</h2>
      <p class="page-description">量化多头产品超额收益分析与风险评估</p>
    </div>

    <!-- 标签页导航 -->
    <el-tabs v-model="activeTab" type="card" @tab-click="handleTabClick">
      <el-tab-pane label="产品列表" name="product-list">
        <router-view v-if="activeTab === 'product-list'" />
      </el-tab-pane>

      <el-tab-pane label="汇总分析" name="summary-analysis">
        <router-view v-if="activeTab === 'summary-analysis'" />
      </el-tab-pane>

      <el-tab-pane label="单品分析" name="single-product" v-if="selectedProduct">
        <router-view v-if="activeTab === 'single-product'" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 当前激活的标签
const activeTab = ref('product-list')

// 选中的产品（用于单品分析）
const selectedProduct = computed(() => {
  return route.params.productId || localStorage.getItem('selectedQuantProduct')
})

// 处理标签切换
const handleTabClick = (tab) => {
  const tabName = tab.props.name

  if (tabName === 'product-list') {
    router.push('/quantitative-analysis/product-list')
  } else if (tabName === 'summary-analysis') {
    router.push('/quantitative-analysis/summary-analysis')
  } else if (tabName === 'single-product' && selectedProduct.value) {
    router.push(`/quantitative-analysis/single-product/${selectedProduct.value}`)
  }
}

// 监听路由变化，更新当前标签
watch(() => route.path, (newPath) => {
  if (newPath.includes('product-list')) {
    activeTab.value = 'product-list'
  } else if (newPath.includes('summary-analysis')) {
    activeTab.value = 'summary-analysis'
  } else if (newPath.includes('single-product')) {
    activeTab.value = 'single-product'
  }
}, { immediate: true })

onMounted(() => {
  // 根据当前路由设置激活的标签
  if (route.path.includes('summary-analysis')) {
    activeTab.value = 'summary-analysis'
  } else if (route.path.includes('single-product')) {
    activeTab.value = 'single-product'
  } else {
    activeTab.value = 'product-list'
  }
})
</script>

<style scoped>
.quantitative-analysis-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 8px 0 0 0;
  font-size: 14px;
  color: #909399;
}

:deep(.el-tabs) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
  overflow-y: auto;
}

:deep(.el-tab-pane) {
  height: 100%;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  height: 44px;
  line-height: 44px;
}

:deep(.el-tabs--card > .el-tabs__header) {
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 20px;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__nav) {
  border: none;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item) {
  border: 1px solid transparent;
  border-bottom: none;
  transition: all 0.3s;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item.is-active) {
  border-color: #e4e7ed;
  border-bottom: 1px solid #fff;
  color: #409EFF;
}

:deep(.el-tabs--card > .el-tabs__header .el-tabs__item:hover) {
  color: #409EFF;
}
</style>