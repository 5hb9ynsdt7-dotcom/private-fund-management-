<template>
  <div class="nav-crawler-page">
    <!-- 页面标题 -->
    <el-page-header @back="() => $router.go(-1)">
      <template #content>
        <div class="page-title">
          <h2>净值抓取</h2>
          <p>功能开发中...</p>
        </div>
      </template>
    </el-page-header>

    <!-- 空状态显示 -->
    <el-empty
      description="该功能正在开发中，敬请期待"
      :image-size="200"
    >
      <template #image>
        <el-icon size="200" color="#e6e6e6">
          <Tools />
        </el-icon>
      </template>
    </el-empty>
  </div>
</template>

<script setup>
import { Tools } from '@element-plus/icons-vue'
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

.el-empty {
  margin-top: 100px;
}
</style>