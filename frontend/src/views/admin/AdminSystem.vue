<template>
  <div class="as-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">🔐 系统安全</span>
        <h1>日志、<em>备份</em>与业务开关</h1>
        <p>所有敏感操作都会写入审计日志；数据库可随时备份</p>
      </div>
    </div>

    <div class="candy-card tilt-sky">
      <el-tabs v-model="tab">
        <!-- 业务开关 -->
        <el-tab-pane name="toggles">
          <template #label><span class="tab-label">🎛️ 业务开关</span></template>
          <div class="toggle-list">
            <div v-for="t in toggles" :key="t.id" class="toggle-item">
              <div class="toggle-info">
                <div class="toggle-name">{{ t.name }}</div>
                <div class="toggle-key">开关标识：{{ t.key }}</div>
              </div>
              <el-switch
                :model-value="t.enabled"
                active-text="开启"
                inactive-text="关闭"
                @change="(val) => toggleFeature(t, val)"
              />
            </div>
            <el-empty v-if="!toggles.length" description="暂无可配置的业务开关" :image-size="80" />
          </div>
          <div class="hint-box">
            关闭「网上预约挂号」后，患者端的在线挂号入口会立即失效；开启「发热门诊快速通道」用于传染病高发期的分流。
          </div>
        </el-tab-pane>

        <!-- 审计日志 -->
        <el-tab-pane name="logs">
          <template #label><span class="tab-label">🧾 审计日志（{{ logs.length }}）</span></template>
          <div class="toolbar">
            <el-input v-model="logKeyword" placeholder="搜索操作人 / 动作 / 对象" clearable style="width:260px" />
            <el-select v-model="logRole" placeholder="角色" clearable style="width:130px">
              <el-option label="全部角色" value="" />
              <el-option label="患者" value="patient" />
              <el-option label="医生" value="doctor" />
              <el-option label="管理员" value="admin" />
            </el-select>
            <el-button @click="loadLogs">刷新</el-button>
          </div>
          <el-table :data="filteredLogs" v-loading="logLoading" stripe max-height="520">
            <el-table-column prop="created_at" label="时间" width="160">
              <template #default="{ row }">{{ fmt(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="username" label="操作人" width="130" />
            <el-table-column label="角色" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="roleTag(row.role)">{{ roleLabel(row.role) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="action" label="动作" width="150" />
            <el-table-column prop="target" label="对象" min-width="160" />
            <el-table-column prop="detail" label="详情" min-width="220">
              <template #default="{ row }">{{ row.detail || '—' }}</template>
            </el-table-column>
            <el-table-column prop="ip" label="IP" width="120" />
          </el-table>
          <el-empty v-if="!logLoading && !filteredLogs.length" description="暂无审计日志" :image-size="80" />
        </el-tab-pane>

        <!-- 数据备份 -->
        <el-tab-pane name="backup">
          <template #label><span class="tab-label">💾 数据备份</span></template>
          <div class="backup-box">
            <div class="backup-emoji">🗄️</div>
            <div class="backup-title">一键备份数据库</div>
            <div class="backup-desc">
              备份文件保存在服务器 backend/backups/ 目录，文件名带时间戳，便于回滚。<br />
              建议在系统升级、批量导入数据前执行一次备份。
            </div>
            <el-button type="primary" size="large" round :loading="backing" @click="doBackup">立即备份</el-button>
            <div v-if="lastBackup" class="backup-result">
              ✅ 最近一次备份：<b>{{ lastBackup.file }}</b> · {{ (lastBackup.size / 1024).toFixed(0) }} KB ·
              {{ fmt(lastBackup.created_at) }}
            </div>
          </div>

          <div class="security-list">
            <div class="sec-item">🛡️ 患者无法访问医生后台与医院经营数据（总收入 / 科室利润）</div>
            <div class="sec-item">🛡️ 医生不能管理账号、药库定价与库存，也不能修改已归档病历</div>
            <div class="sec-item">🛡️ 管理员的开户、删号、重置密码、开关配置全部记录审计日志</div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { workflowApi } from '../../api/modules'

const tab = ref('toggles')
const toggles = ref([])
const logs = ref([])
const logLoading = ref(false)
const logKeyword = ref('')
const logRole = ref('')
const backing = ref(false)
const lastBackup = ref(null)

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 19) : '—')
const roleLabel = (r) => ({ patient: '患者', doctor: '医生', admin: '管理员', '': '系统' }[r] || r || '系统')
const roleTag = (r) => ({ patient: 'primary', doctor: 'success', admin: 'danger' }[r] || 'info')

const filteredLogs = computed(() => {
  const kw = logKeyword.value.trim()
  return logs.value.filter((l) => {
    if (logRole.value && l.role !== logRole.value) return false
    if (!kw) return true
    return [l.username, l.action, l.target, l.detail].some((v) => (v || '').includes(kw))
  })
})

const loadToggles = async () => {
  toggles.value = listOf(await workflowApi.toggles())
}

const loadLogs = async () => {
  logLoading.value = true
  try {
    logs.value = listOf(await workflowApi.auditLogs({ page_size: 200 }))
  } finally {
    logLoading.value = false
  }
}

const toggleFeature = async (t, val) => {
  await workflowApi.toggleUpdate(t.id, { enabled: val })
  t.enabled = val
  ElMessage.success(`${t.name} 已${val ? '开启' : '关闭'}`)
  await loadLogs()
}

const doBackup = async () => {
  backing.value = true
  try {
    lastBackup.value = await workflowApi.backup()
    ElMessage.success('数据库备份完成')
    await loadLogs()
  } finally {
    backing.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadToggles(), loadLogs()])
})
</script>

<style scoped>
.as-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.tab-label { font-weight: 800; }
.toggle-list { display: flex; flex-direction: column; gap: 10px; }
.toggle-item {
  display: flex; justify-content: space-between; align-items: center; gap: 16px;
  background: #F6FCFF; border: 2px dashed #CDE9F7; border-radius: 16px; padding: 14px 16px;
}
.toggle-name { font-size: 14px; font-weight: 800; color: var(--ink); }
.toggle-key { font-size: 11px; color: var(--ink-faint); margin-top: 3px; }
.hint-box { margin-top: 14px; font-size: 11.5px; color: var(--ink-faint); line-height: 1.8; }

.toolbar { display: flex; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }

.backup-box { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 24px 0 8px; }
.backup-emoji { font-size: 46px; }
.backup-title { font-size: 17px; font-weight: 900; color: var(--ink); margin-top: 8px; }
.backup-desc { font-size: 12px; color: var(--ink-soft); line-height: 1.8; margin: 10px 0 18px; }
.backup-result {
  margin-top: 16px; font-size: 12px; color: var(--mint-deep);
  background: #F7FFFB; border: 2px dashed #C9EDDF; border-radius: 12px; padding: 10px 14px;
}
.security-list { margin-top: 20px; display: flex; flex-direction: column; gap: 8px; }
.sec-item { font-size: 12px; color: var(--ink-soft); background: #FFFDF7; border: 1px solid #FFE9C9; border-radius: 12px; padding: 10px 12px; }
</style>
