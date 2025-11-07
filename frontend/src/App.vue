<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 侧边导航 -->
      <el-aside width="240px" class="sidebar">
        <div class="sidebar-header">
          <div class="logo">
            <el-icon size="28" color="#409EFF"><TrendCharts /></el-icon>
            <span class="logo-text">私募基金管理</span>
          </div>
        </div>
        
        <el-menu
          :default-active="$route.path"
          router
          class="sidebar-menu"
          background-color="#001529"
          text-color="#8c8c8c"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/nav">
            <el-icon><DataLine /></el-icon>
            <span>净值管理</span>
          </el-menu-item>
          
          <el-menu-item index="/nav-crawler">
            <el-icon><Download /></el-icon>
            <span>净值抓取</span>
          </el-menu-item>
          
          <el-menu-item index="/strategy">
            <el-icon><Setting /></el-icon>
            <span>策略管理</span>
          </el-menu-item>
          
          <el-menu-item index="/position">
            <el-icon><PieChart /></el-icon>
            <span>持仓分析</span>
          </el-menu-item>
          
          <el-menu-item index="/trade">
            <el-icon><Histogram /></el-icon>
            <span>交易分析</span>
          </el-menu-item>
          
          <el-menu-item index="/project-holding">
            <el-icon><Management /></el-icon>
            <span>项目持仓</span>
          </el-menu-item>
          
          <el-menu-item index="/stage-performance">
            <el-icon><TrendCharts /></el-icon>
            <span>阶段涨幅</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="app-header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item>{{ $route.meta.title || '首页' }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-space>
              <el-tooltip content="系统设置">
                <el-button circle>
                  <el-icon><Tools /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="帮助">
                <el-button circle>
                  <el-icon><QuestionFilled /></el-icon>
                </el-button>
              </el-tooltip>
            </el-space>
          </div>
        </el-header>

        <!-- 主内容 -->
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
// 不需要导入任何内容，图标已在main.js中全局注册
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #001529;
  border-right: 1px solid #e6e6e6;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid #303030;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-menu {
  border: none;
  height: calc(100vh - 64px);
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left .el-breadcrumb {
  font-size: 16px;
  font-weight: 500;
}

.app-main {
  background-color: #f5f5f5;
  padding: 24px;
  overflow-y: auto;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 200px !important;
  }
  
  .logo-text {
    display: none;
  }
  
  .app-main {
    padding: 16px;
  }
}
</style>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}

/* Element Plus主题定制 */
:root {
  --el-color-primary: #409EFF;
  --el-color-success: #67C23A;
  --el-color-warning: #E6A23C;
  --el-color-danger: #F56C6C;
  --el-color-info: #909399;
}

/* 表格样式优化 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.el-table .el-table__header-wrapper {
  background-color: #fafafa;
}

/* 卡片样式 */
.el-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 按钮样式 */
.el-button {
  border-radius: 6px;
}

/* 表单样式 */
.el-form-item {
  margin-bottom: 22px;
}

/* 统一数字字体为Inter - 全局样式 */
/* 统计数字字体 */
.el-statistic__content,
.el-statistic__number {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif !important;
}

/* 表格中的金额、数字类字体统一 */
.money-text,
.shares-text,
.percent-text,
.nav-value,
.fee-text,
.dividend-text,
.profit-text,
.loss-text,
.date-cell {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif !important;
}

/* 表格汇总行数字字体 */
.el-table__footer .cell {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif !important;
}

/* 其他可能的数字显示元素 */
.el-table__cell .cell,
.el-table td .cell,
.el-table th .cell {
  font-family: inherit;
}

/* 表格中数字列统一字体 */
.el-table .el-table__cell:not(.el-table-column--selection) .cell {
  font-family: inherit;
}

/* 统计相关数字显示 */
.el-statistic,
.el-card .el-statistic {
  font-family: 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}
</style>