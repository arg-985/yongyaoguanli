<template>
  <div class="not-found">
    <div class="code">404</div>
    <div class="msg">抱歉,您访问的页面不存在</div>
    <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
  </div>
</template>

<script setup>
</script>

<style scoped>
.not-found { text-align: center; padding: 80px 0; }
.code { font-size: 120px; font-weight: 800; color: #409eff; letter-spacing: 4px; }
.msg { font-size: 18px; color: #909399; margin-bottom: 24px; }
</style>
