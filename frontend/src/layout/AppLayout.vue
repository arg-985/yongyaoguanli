<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="aside">
      <AppSidebar />
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: homePath }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click" @command="onCommand">
            <span class="user-info">
              <el-avatar :size="34" class="avatar">{{ auth.user?.username?.[0]?.toUpperCase() || 'U' }}</el-avatar>
              <span class="username">{{ auth.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <AppMain />
    </el-container>
    <AiSprite />
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppSidebar from './AppSidebar.vue'
import AppMain from './AppMain.vue'
import AiSprite from '../components/AiSprite.vue'
import { ElMessageBox } from 'element-plus'
import { homeFor } from '../router'

const router = useRouter()
const auth = useAuthStore()
const homePath = computed(() => homeFor(auth.user?.role))

const onCommand = (cmd) => {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确认退出登录?', '提示', { type: 'warning' })
      .then(() => {
        auth.logout()
        router.push('/login')
      }).catch(() => {})
  } else if (cmd === 'profile') {
    router.push(auth.isPatient ? '/patient/profile' : homePath.value)
  }
}
</script>

<style scoped>
.app-layout { height: 100vh; }
.aside { background: #FFFDF7; overflow-y: auto; border-right: 2px solid #FFE2B8; }
.header {
  background: rgba(255, 253, 247, .9);
  backdrop-filter: blur(8px);
  border-bottom: 2px solid #FFE9C9;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 22px; height: 64px !important;
}
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.avatar { background: linear-gradient(150deg, #FFBE7A, #E8862B); font-weight: 800; }
.username { font-weight: 700; color: #4A3B32; }
</style>
