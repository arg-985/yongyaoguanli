<template>
  <div class="sidebar">
    <div class="logo">
      <span class="logo-mark">{{ roleMeta.mark }}</span>
      <div class="logo-text">
        <span class="logo-name">用药小管家</span>
        <span class="logo-sub">{{ roleMeta.sub }}</span>
      </div>
    </div>

    <el-menu
      :default-active="$route.path"
      background-color="transparent"
      text-color="#7A6555"
      active-text-color="#4A3B32"
      router
    >
      <template v-if="auth.isPatient">
        <el-menu-item index="/dashboard">
          <span class="menu-emoji">🏠</span><span>首页</span>
        </el-menu-item>

        <div class="menu-group-title">就诊服务</div>
        <el-menu-item index="/patient/appointments">
          <span class="menu-emoji">📝</span><span>预约挂号</span>
        </el-menu-item>
        <el-menu-item index="/patient/records">
          <span class="menu-emoji">📂</span><span>我的就诊档案</span>
        </el-menu-item>

        <div class="menu-group-title">用药管理</div>
        <el-menu-item index="/plans">
          <span class="menu-emoji">🗓️</span><span>用药计划</span>
        </el-menu-item>
        <el-menu-item index="/calendar">
          <span class="menu-emoji">📅</span><span>服药日历</span>
        </el-menu-item>
        <el-menu-item index="/records">
          <span class="menu-emoji">📋</span><span>服药记录</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <span class="menu-emoji">📈</span><span>依从率统计</span>
        </el-menu-item>

        <div class="menu-group-title">健康工具</div>
        <el-menu-item index="/clinic/cabinet">
          <span class="menu-emoji">🧴</span><span>家庭药箱</span>
        </el-menu-item>
        <el-menu-item index="/clinic/safety">
          <span class="menu-emoji">🛡️</span><span>用药安全</span>
        </el-menu-item>
        <el-menu-item index="/clinic/records">
          <span class="menu-emoji">📁</span><span>健康档案</span>
        </el-menu-item>
        <el-menu-item index="/patient/profile">
          <span class="menu-emoji">👤</span><span>个人中心</span>
        </el-menu-item>
      </template>

      <template v-else-if="auth.isDoctor">
        <el-menu-item index="/doctor/workbench">
          <span class="menu-emoji">🩺</span><span>接诊工作台</span>
        </el-menu-item>
        <el-menu-item index="/doctor/consult">
          <span class="menu-emoji">✍️</span><span>患者接诊</span>
        </el-menu-item>
        <el-menu-item index="/doctor/patients">
          <span class="menu-emoji">🧾</span><span>我的患者</span>
        </el-menu-item>
        <el-menu-item index="/doctor/prescriptions">
          <span class="menu-emoji">💊</span><span>我的处方</span>
        </el-menu-item>
      </template>

      <template v-else-if="auth.isAdmin">
        <el-menu-item index="/admin/home">
          <span class="menu-emoji">📊</span><span>管理总览</span>
        </el-menu-item>
        <div class="menu-group-title">账号与权限</div>
        <el-menu-item index="/admin/accounts">
          <span class="menu-emoji">👥</span><span>账号与角色</span>
        </el-menu-item>
        <div class="menu-group-title">基础数据</div>
        <el-menu-item index="/admin/catalog">
          <span class="menu-emoji">🏥</span><span>科室 / 药品 / 排班</span>
        </el-menu-item>
        <div class="menu-group-title">系统</div>
        <el-menu-item index="/admin/system">
          <span class="menu-emoji">🔐</span><span>系统安全</span>
        </el-menu-item>
      </template>
    </el-menu>

    <div class="sidebar-foot">
      <span>{{ roleMeta.foot }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const roleMeta = computed(() => {
  if (auth.isDoctor) {
    return { mark: '🩺', sub: '医生工作站', foot: `🌿 ${auth.user?.department || ''} ${auth.user?.real_name || ''}`.trim() }
  }
  if (auth.isAdmin) {
    return { mark: '🛡️', sub: '医院管理端', foot: '🔐 权限与数据安全' }
  }
  return { mark: '💊', sub: '患者自助端', foot: '🌿 今天也要按时吃药哦' }
})
</script>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #FFFDF7;
  border-right: 2px solid var(--cream-line, #FFE2B8);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 18px 14px;
}
.logo-mark {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(160deg, #FF9DB4, #E85C80);
  box-shadow: inset 0 -5px 0 rgba(0, 0, 0, .12), 0 6px 14px rgba(232, 92, 128, .3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.logo-text { display: flex; flex-direction: column; line-height: 1.25; }
.logo-name { font-size: 15px; font-weight: 800; color: #4A3B32; letter-spacing: .5px; }
.logo-sub { font-size: 10px; color: #B7A797; letter-spacing: .5px; }

.el-menu { border-right: none; padding: 4px 10px 10px; flex: 1; overflow-y: auto; }

.menu-group-title {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 2px;
  color: #C9B49F;
  padding: 14px 12px 6px;
}

.el-menu-item {
  height: 42px;
  line-height: 42px;
  border-radius: 14px;
  margin: 3px 0;
  font-weight: 600;
  font-size: 14px;
}
.el-menu-item:hover { background: #FFF3DC !important; }
.el-menu-item.is-active {
  background: linear-gradient(135deg, #FFE4EB, #FFD6E2) !important;
  color: #E85C80 !important;
  box-shadow: inset 0 -3px 0 rgba(232, 92, 128, .12);
}
.menu-emoji { margin-right: 10px; font-size: 16px; }

.sidebar-foot {
  margin: 10px 14px 16px;
  padding: 10px 12px;
  border-radius: 16px;
  background: #F4FAF6;
  border: 2px dashed #CBEBDD;
  font-size: 11px;
  color: #6A9A85;
  text-align: center;
}
</style>
