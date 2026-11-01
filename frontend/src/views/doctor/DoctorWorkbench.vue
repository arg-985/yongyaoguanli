<template>
  <div class="doctor-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">🩺 医生工作台</span>
        <h1>{{ greeting }}，{{ auth.user?.real_name || auth.user?.username }} <em>医生</em></h1>
        <p>{{ auth.user?.department || '临床科室' }} · {{ auth.user?.title || '医师' }} · 今天已接诊 {{ data.today_visits }} 位患者</p>
      </div>
      <el-button type="primary" size="large" round @click="$router.push('/doctor/consult')">开始接诊 →</el-button>
    </div>

    <div class="kpi-row">
      <div class="kpi-tile pink">
        <div class="kpi-num">{{ data.today_visits }}</div>
        <div class="kpi-label">今日接诊</div>
      </div>
      <div class="kpi-tile yellow">
        <div class="kpi-num">{{ waiting.length }}</div>
        <div class="kpi-label">候诊人数</div>
      </div>
      <div class="kpi-tile sky">
        <div class="kpi-num">{{ data.pending_exams }}</div>
        <div class="kpi-label">待出报告</div>
      </div>
      <div class="kpi-tile mint">
        <div class="kpi-num">{{ data.pending_followups }}</div>
        <div class="kpi-label">7 日内复诊</div>
      </div>
    </div>

    <div class="dash-row">
      <div class="candy-card tilt-sky">
        <div class="card-head">
          <div class="t-main">📆 我的排班（今天）</div>
          <span class="pill sky">周{{ weekdayText }}</span>
        </div>
        <el-empty v-if="!schedules.length" description="今天没有排班，休息一下吧" :image-size="70" />
        <div v-else class="schedule-list">
          <div v-for="s in schedules" :key="s.id" class="schedule-item">
            <div class="sch-period">{{ periodText(s.period) }}</div>
            <div class="sch-info">
              <div class="sch-room">🏥 {{ s.room || '未安排诊室' }}</div>
              <div class="sch-cap">号源 {{ s.capacity }} 个</div>
            </div>
            <span class="pill yellow">出诊中</span>
          </div>
        </div>
      </div>

      <div class="candy-card tilt-pink">
        <div class="card-head">
          <div class="t-main">🙋 候诊队列</div>
          <span class="pill pink">{{ waiting.length }} 人等待</span>
        </div>
        <el-empty v-if="!waiting.length" description="暂时没有候诊患者" :image-size="70" />
        <div v-else class="queue-list">
          <div v-for="v in waiting" :key="v.id" class="queue-item">
            <div class="q-avatar">{{ (v.patient_name || v.patient_username || '?')[0] }}</div>
            <div class="q-info">
              <div class="q-name">
                {{ v.patient_name || v.patient_username }}
                <span class="pill" :class="v.visit_type === 'FIRST' ? 'sky' : 'mint'">{{ v.visit_type_display }}</span>
              </div>
              <div class="q-sub">{{ v.patient_phone || '未留手机号' }} · {{ v.status_display }}</div>
            </div>
            <el-button size="small" :type="v.status === 'IN_PROGRESS' ? 'warning' : 'primary'" round @click="callIn(v)">
              {{ v.status === 'IN_PROGRESS' ? '继续接诊' : '叫号' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <div class="candy-card tilt-mint todo-card">
      <div class="card-head">
        <div class="t-main">✅ 待办提醒</div>
      </div>
      <div class="todo-list">
        <div class="todo-item">
          <span class="todo-icon">🔬</span>
          <span>有 <b>{{ data.pending_exams }}</b> 份检查单等待报告，出结果后请及时复核</span>
        </div>
        <div class="todo-item">
          <span class="todo-icon">📅</span>
          <span>7 日内有 <b>{{ data.pending_followups }}</b> 位患者需要复诊</span>
        </div>
        <div class="todo-item">
          <span class="todo-icon">✍️</span>
          <span>接诊请先核对就诊卡/病历，再填写病历并归档；已归档病历不可直接修改</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { workflowApi } from '../../api/modules'

const auth = useAuthStore()
const router = useRouter()

const data = ref({ schedules: [], waiting: [], pending_exams: 0, pending_followups: 0, today_visits: 0 })
const loading = ref(false)

const schedules = computed(() => data.value.schedules || [])
const waiting = computed(() => data.value.waiting || [])

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 11) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const weekdayText = computed(() => ['一', '二', '三', '四', '五', '六', '日'][new Date().getDay() === 0 ? 6 : new Date().getDay() - 1])
const periodText = (p) => ({ AM: '上午', PM: '下午', NIGHT: '夜班' }[p] || p)

const load = async () => {
  loading.value = true
  try {
    data.value = await workflowApi.workbench()
  } finally {
    loading.value = false
  }
}

const callIn = async (v) => {
  if (v.status === 'WAITING') {
    await workflowApi.visitUpdate(v.id, { status: 'IN_PROGRESS' })
    ElMessage.success(`已叫号：${v.patient_name || v.patient_username}`)
  }
  router.push({ path: '/doctor/consult', query: { visit: v.id } })
}

onMounted(load)
</script>

<style scoped>
.doctor-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.kpi-tile {
  border-radius: 22px;
  padding: 18px 20px;
  border: 2px solid #FFE2B8;
  background: #FFFDF7;
  box-shadow: var(--shadow-soft);
}
.kpi-tile.pink { border-color: #FFD3DF; background: linear-gradient(160deg, #FFF6F9, #FFE4EB); }
.kpi-tile.yellow { border-color: #FFE6A8; background: linear-gradient(160deg, #FFFDF2, #FFF3CC); }
.kpi-tile.sky { border-color: #CDE9F7; background: linear-gradient(160deg, #F6FCFF, #E1F2FC); }
.kpi-tile.mint { border-color: #C9EDDF; background: linear-gradient(160deg, #F7FFFB, #DFF6EC); }
.kpi-num { font-size: 30px; font-weight: 900; color: var(--ink); line-height: 1.2; }
.kpi-label { font-size: 12px; font-weight: 700; color: var(--ink-soft); margin-top: 4px; }

.dash-row { display: grid; grid-template-columns: 1fr 1.25fr; gap: 18px; align-items: start; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.t-main { font-size: 16px; font-weight: 800; color: var(--ink); }

.schedule-list { display: flex; flex-direction: column; gap: 10px; }
.schedule-item {
  display: flex; align-items: center; gap: 14px;
  background: #F9FDFF; border: 2px dashed #CDE9F7; border-radius: 16px; padding: 12px 14px;
}
.sch-period { font-size: 15px; font-weight: 900; color: var(--sky-deep); min-width: 44px; }
.sch-info { flex: 1; }
.sch-room { font-size: 13.5px; font-weight: 700; color: var(--ink); }
.sch-cap { font-size: 11.5px; color: var(--ink-faint); margin-top: 2px; }

.queue-list { display: flex; flex-direction: column; gap: 10px; }
.queue-item {
  display: flex; align-items: center; gap: 12px;
  background: #FFFAFB; border: 2px dashed #FFD3DF; border-radius: 16px; padding: 10px 14px;
}
.q-avatar {
  width: 38px; height: 38px; border-radius: 50%;
  background: linear-gradient(150deg, #FFBE7A, #E8862B);
  color: #fff; font-weight: 900; display: flex; align-items: center; justify-content: center;
}
.q-info { flex: 1; }
.q-name { font-size: 14px; font-weight: 800; color: var(--ink); display: flex; align-items: center; gap: 6px; }
.q-sub { font-size: 11.5px; color: var(--ink-faint); margin-top: 2px; }

.todo-card { padding: 20px 24px; }
.todo-list { display: flex; flex-direction: column; gap: 10px; }
.todo-item { display: flex; gap: 10px; font-size: 13px; color: var(--ink-soft); line-height: 1.6; }
.todo-icon { font-size: 16px; }

@media (max-width: 980px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .dash-row { grid-template-columns: 1fr; }
}
</style>
