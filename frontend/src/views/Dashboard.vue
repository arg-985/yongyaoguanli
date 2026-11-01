<template>
  <div class="dash-page">
    <div class="page-hero dash-hero">
      <div class="hero-text">
        <span class="eyebrow">🐶 小狗管家 · 家庭全科用药助手</span>
        <h1>{{ greeting }}，<em>{{ auth.user?.username || '主人' }}</em></h1>
        <p>{{ todayLabel }} · 今天有 {{ pendingCount }} 项待服药，记得按时吃哦</p>
        <div class="hero-note">
          <div class="note-emoji">🐾</div>
          <div>
            <div class="note-title">小提示</div>
            <div class="note-sub">吃药前先在下面让药药看看，安心一点</div>
          </div>
        </div>
      </div>
      <div class="hero-3d">
        <ThreeCapsule />
        <div class="hero-3d-hint">✨ 鼠标移上去，药瓶会跟你互动</div>
      </div>
    </div>

    <el-row :gutter="18" class="dash-row" style="align-items:stretch">
      <el-col :xs="24" :lg="15" style="display:flex">
        <div class="candy-card tilt-pink consult-card" style="flex:1">
          <ClinicConsult />
        </div>
      </el-col>
      <el-col :xs="24" :lg="9" style="display:flex">
        <div class="candy-card tilt-yellow today-card" style="flex:1">
          <div class="card-title">
            <span class="jelly yellow">💊</span>
            <div>
              <div class="t-main">今日待服</div>
              <div class="t-sub">共 {{ todayReminders.length }} 项</div>
            </div>
          </div>
          <el-empty v-if="!loading && todayReminders.length === 0" description="今天没有待服药提醒" :image-size="70" />
          <div v-else class="reminder-list">
            <div v-for="r in todayReminders" :key="r.id" class="reminder-item">
              <div class="reminder-info">
                <div class="med-name">{{ r.medication_name || r.medication }}</div>
                <div class="med-sub">
                  🕗 {{ r.scheduled_time }}
                  <span v-if="r.dosage">· {{ r.dosage }}</span>
                </div>
              </div>
              <el-button
                v-if="r.status === 'PENDING'"
                type="primary"
                size="small"
                :loading="marking === r.id"
                @click="markTaken(r)"
              >标记已服</el-button>
              <el-button
                v-else-if="r.status === 'MISSED'"
                type="warning"
                plain
                size="small"
                :loading="marking === r.id"
                @click="markTaken(r)"
              >补记已服</el-button>
              <span v-else class="pill" :class="statusPill(r.status)">{{ statusLabel(r.status) }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="18" class="dash-row" style="align-items:stretch">
      <el-col :xs="24" :lg="12" style="display:flex">
        <div class="candy-card tilt-sky" style="flex:1">
          <div class="card-title">
            <span class="jelly sky">📈</span>
            <div>
              <div class="t-main">近 7 天依从率</div>
              <div class="t-sub">按时服药的比例</div>
            </div>
          </div>
          <div v-if="auth.isAdmin" class="admin-stats">
            <div class="stat-tile sky"><div class="num">{{ adminStats.users || 0 }}</div><div class="label">用户总数</div><span class="icon">👥</span></div>
            <div class="stat-tile mint"><div class="num">{{ adminStats.plans || 0 }}</div><div class="label">用药计划</div><span class="icon">🗓️</span></div>
            <div class="stat-tile orange"><div class="num">{{ adminStats.medications || 0 }}</div><div class="label">药物种类</div><span class="icon">💊</span></div>
          </div>
          <VChart v-else :option="adherenceChartOption" autoresize style="height: 250px;" />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12" style="display:flex">
        <div class="candy-card tilt-mint" style="flex:1">
          <div class="card-title">
            <span class="jelly mint">📋</span>
            <div>
              <div class="t-main">最近服药记录</div>
              <div class="t-sub">最近 5 条打卡</div>
            </div>
          </div>
          <el-table :data="recentRecords" size="small" class="dash-table" style="flex:1">
            <el-table-column prop="scheduled_time" label="时间" width="170" />
            <el-table-column prop="medication_name" label="药物" />
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <span class="pill" :class="row.status === 'TAKEN' ? 'mint' : row.status === 'MISSED' ? 'pink' : 'yellow'">
                  {{ statusLabel(row.status) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="activePlans.length" class="plan-strip">
            <span class="pill sky">活跃计划 {{ activePlans.length }} 个</span>
            <span class="plan-med">{{ activePlans[0].medication_name || activePlans[0].medication }}</span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { reminderApi, planApi, recordApi, userApi, medicationApi } from '../api/modules'
import ClinicConsult from '../components/ClinicConsult.vue'
import ThreeCapsule from '../components/ThreeCapsule.vue'

const auth = useAuthStore()

const loading = ref(false)
const todayReminders = ref([])
const activePlans = ref([])
const recentRecords = ref([])
const adherenceData = ref({ dates: [], rates: [] })
const adminStats = ref({})
const marking = ref(null)

const todayStr = () => new Date().toISOString().slice(0, 10)

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜猫子'
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const pendingCount = computed(() => todayReminders.value.filter(r => r.status === 'PENDING').length)

const todayLabel = computed(() => {
  const d = new Date()
  return `${d.getMonth() + 1} 月 ${d.getDate()} 日 星期${'日一二三四五六'[d.getDay()]}`
})

onMounted(async () => {
  loading.value = true
  try {
    const today = todayStr()
    const [remRes, planRes, recRes, admRes] = await Promise.allSettled([
      reminderApi.list({ date: today, page_size: 100 }),
      planApi.list({ status: 'active', page_size: 5 }),
      recordApi.list({ ordering: '-scheduled_time', page_size: 5 }),
      auth.isAdmin
        ? Promise.allSettled([
            userApi.list({ page_size: 1 }),
            planApi.list({ page_size: 1 }),
            medicationApi.list({ page_size: 1 }),
          ])
        : Promise.resolve(null),
    ])
    todayReminders.value = remRes.value?.results || remRes.value || []
    activePlans.value = planRes.value?.results || planRes.value || []
    recentRecords.value = recRes.value?.results || recRes.value || []
    if (admRes.value) {
      const [u, p, m] = admRes.value.map(r => r.value)
      adminStats.value = {
        users: u?.count ?? 0,
        plans: p?.count ?? 0,
        medications: m?.count ?? 0,
      }
    }

    if (!auth.isAdmin) {
      const stats = await recordApi.stats({ days: 7 })
      const arr = stats?.daily || []
      adherenceData.value = {
        dates: arr.map(x => x.date?.slice(5) || ''),
        rates: arr.map(x => x.adherence_rate != null ? Number(x.adherence_rate.toFixed(1)) : 0)
      }
    }
  } finally {
    loading.value = false
  }
})

const adherenceChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { top: 20, right: 20, bottom: 30, left: 40 },
  xAxis: {
    type: 'category',
    data: adherenceData.value.dates,
    axisLine: { lineStyle: { color: '#FFDDA8' } },
    axisLabel: { color: '#8A7466' }
  },
  yAxis: {
    type: 'value', min: 0, max: 100,
    axisLabel: { formatter: '{value}%', color: '#8A7466' },
    splitLine: { lineStyle: { color: '#FFF0D8' } }
  },
  series: [{
    type: 'line', smooth: true, data: adherenceData.value.rates,
    symbolSize: 7,
    itemStyle: { color: '#FF7FA0' },
    lineStyle: { width: 3, color: '#FF7FA0' },
    areaStyle: { color: 'rgba(255,127,160,.16)' }
  }]
}))

/** 服药冲突提醒弹窗 */
const showConflictAlert = (warnings) => {
  const items = warnings.map(w => `
    <div style="margin-bottom:10px;padding:10px 12px;background:#FFF6F8;border:1px solid #FFD1D9;border-radius:10px;">
      <div style="font-weight:800;color:#A83B48;margin-bottom:4px;">${w.title}</div>
      <div style="font-size:12px;line-height:1.7;color:#5A4739;">${w.detail}</div>
    </div>`).join('')
  ElMessageBox.alert(
    `<div style="font-size:13px;color:#5A4739;margin-bottom:10px;">你刚记录服用的药，与正在服用的其他药物存在风险，请尽快与医生或药师确认：</div>${items}`,
    '⚠️ 用药冲突提醒',
    { dangerouslyUseHTMLString: true, confirmButtonText: '我知道了', type: 'warning' }
  )
}

const markTaken = async (r) => {
  marking.value = r.id
  try {
    const res = await recordApi.markTaken({ reminder_id: r.id, taken_time: new Date().toISOString() })
    r.status = res?.status || 'TAKEN'
    if (res?.warnings?.length) {
      showConflictAlert(res.warnings)
    } else {
      ElMessage.success('已标记为服药')
    }
  } finally {
    marking.value = null
  }
}

const statusLabel = (s) => ({ PENDING: '待服', TAKEN: '已服', LATE: '迟服', MISSED: '漏服', SKIPPED: '跳过' }[s] || s)
const statusPill = (s) => ({ TAKEN: 'mint', LATE: 'yellow', MISSED: 'pink', SKIPPED: 'sky' }[s] || 'yellow')
</script>

<style scoped>
.dash-page { max-width: 1500px; }
.dash-row { margin-top: 18px; align-items: stretch !important; }
/* 强制同一行的卡片等高对齐：行拉伸列、列变 flex、卡片撑满 */
.dash-row > .el-col { display: flex !important; }
.dash-row .candy-card { flex: 1 1 auto; display: flex; flex-direction: column; }

/* 今日待服卡片高度自适应（可改这里的高度） */
.today-card { display: flex; flex-direction: column; }
.today-card :deep(.reminder-list) { flex: 1; overflow-y: auto; max-height: 520px; }

.hero-note {
  display: flex; align-items: center; gap: 10px;
  background: #FFFDF7; border: 2px solid #FFE6A8; border-radius: 20px;
  padding: 10px 16px; box-shadow: 0 6px 0 #FFEFC9;
  margin-top: 14px;
}
.note-emoji {
  width: 38px; height: 38px; border-radius: 12px; font-size: 19px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(160deg, #FFE07A, #E9B520);
  box-shadow: inset 0 -4px 0 rgba(0,0,0,.1);
}
.note-title { font-size: 13px; font-weight: 800; color: var(--ink); }
.note-sub { font-size: 11px; color: var(--ink-faint); }

.hero-3d {
  width: 300px;
  min-width: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.hero-3d-hint {
  font-size: 11px;
  color: var(--ink-faint);
  margin-top: 4px;
  text-align: center;
}
@media (max-width: 900px) {
  .hero-3d { display: none; }
}

.card-title { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.t-main { font-size: 15px; font-weight: 800; color: var(--ink); }
.t-sub { font-size: 11px; color: var(--ink-faint); }

.today-card { height: 100%; display: flex; flex-direction: column; }
.today-card :deep(.reminder-list) { flex: 1; overflow-y: auto; }
.reminder-list .reminder-item { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 10px 0; border-bottom: 1px dashed #FFE3BF; }
.reminder-list .reminder-item:last-child { border-bottom: none; }
.med-name { font-weight: 800; color: var(--ink); font-size: 13px; }
.med-sub { color: var(--ink-faint); font-size: 11.5px; margin-top: 3px; }

.admin-stats { display: flex; flex-direction: column; gap: 10px; }
.admin-stats .stat-tile { padding: 12px 16px; }
.admin-stats .num { font-size: 22px; }

.plan-strip { display: flex; align-items: center; gap: 8px; margin-top: 12px; font-size: 12px; }
.plan-med { color: var(--ink-soft); font-weight: 700; }

.dash-table { border-radius: 14px; }

@media (max-width: 1200px) {
  .consult-card { margin-bottom: 18px; }
}
</style>
