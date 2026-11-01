<template>
  <div class="dp-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">🧾 我的患者</span>
        <h1>只看自己<em>接诊过</em>的患者档案</h1>
        <p>不能跨科室查看其他医生的患者；会诊需另行授权 · 已归档病历只读</p>
      </div>
      <el-input v-model="keyword" placeholder="搜索姓名 / 手机号" clearable style="width:220px" />
    </div>

    <div class="candy-card tilt-sky">
      <el-table :data="filteredPatients" v-loading="loading" stripe>
        <el-table-column label="患者" min-width="180">
          <template #default="{ row }">
            <div class="pt-cell">
              <div class="pt-avatar">{{ (row.name || '?')[0] }}</div>
              <div>
                <div class="pt-name">{{ row.name }}</div>
                <div class="pt-sub">{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column label="过敏史" min-width="150">
          <template #default="{ row }">
            <span class="pill" :class="row.allergies ? 'pink' : 'mint'">{{ row.allergies || '无记录' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="visitCount" label="接诊次数" width="100" />
        <el-table-column label="最近就诊" width="130">
          <template #default="{ row }">{{ row.lastDate }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openPatient(row)">查看档案</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !filteredPatients.length" description="还没有接诊过的患者" :image-size="80" />
    </div>

    <el-drawer v-model="drawer" size="620px" :title="`患者档案 · ${active?.name || ''}`">
      <div v-if="active" class="drawer-body">
        <div class="patient-card">
          <div class="pc-avatar">{{ (active.name || '?')[0] }}</div>
          <div>
            <div class="pc-name">{{ active.name }} <span class="pill sky">{{ active.visitCount }} 次就诊</span></div>
            <div class="pc-sub">手机 {{ active.phone || '—' }} · 过敏史 {{ active.allergies || '无记录' }}</div>
          </div>
        </div>

        <div v-for="v in active.visits" :key="v.id" class="visit-block">
          <div class="vb-head">
            <span class="vb-date">{{ fmt(v.created_at) }}</span>
            <span class="pill" :class="v.visit_type === 'FIRST' ? 'sky' : 'mint'">{{ v.visit_type_display }}</span>
            <span class="pill" :class="v.is_archived ? 'pink' : 'yellow'">{{ v.is_archived ? '已归档' : v.status_display }}</span>
            <span class="vb-doctor">{{ v.doctor_name }} 医生</span>
          </div>
          <div class="vb-body">
            <div class="kv"><span>主诉</span><p>{{ v.chief_complaint || '—' }}</p></div>
            <div class="kv"><span>现病史</span><p>{{ v.history || '—' }}</p></div>
            <div class="kv"><span>诊断</span><p>{{ v.diagnosis || '—' }}</p></div>
            <div class="kv"><span>处置意见</span><p>{{ v.advice || '—' }}</p></div>

            <div v-if="examsOf(v.id).length" class="sub-block">
              <div class="sub-title">🔬 检查单</div>
              <div v-for="e in examsOf(v.id)" :key="e.id" class="sub-row">
                <b>{{ e.name }}</b>
                <span class="pill sky">{{ e.category_display }}</span>
                <span class="pill" :class="e.status === 'PENDING' ? 'yellow' : 'mint'">{{ e.status_display }}</span>
                <span class="price">¥{{ e.price }}</span>
                <span v-if="e.result" class="result">结果：{{ e.result }}</span>
              </div>
            </div>

            <div v-if="rxsOf(v.id).length" class="sub-block">
              <div class="sub-title">💊 处方</div>
              <div v-for="r in rxsOf(v.id)" :key="r.id" class="sub-row rx">
                <div class="rx-head">处方 #{{ r.id }} · ¥{{ r.total_amount }} · {{ fmt(r.created_at) }}</div>
                <div v-for="it in r.items" :key="it.id" class="rx-item">
                  {{ it.medication_name }} {{ it.specification }} · {{ it.dosage }} · {{ it.frequency }} · {{ it.days }}天 ×{{ it.quantity }}
                </div>
              </div>
            </div>

            <div v-if="notesOf(v.id).length" class="sub-block">
              <div class="sub-title">💬 沟通记录</div>
              <div v-for="n in notesOf(v.id)" :key="n.id" class="note-item">{{ n.transcript }}</div>
            </div>

            <div v-if="followsOf(v.id).length" class="sub-block">
              <div class="sub-title">📅 复诊安排</div>
              <div v-for="f in followsOf(v.id)" :key="f.id" class="sub-row">
                <b>{{ f.due_date }}</b><span>{{ f.note || '复诊' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { workflowApi } from '../../api/modules'

const loading = ref(false)
const keyword = ref('')
const patients = ref([])
const visits = ref([])
const examAll = ref([])
const rxAll = ref([])
const noteAll = ref([])
const followAll = ref([])
const drawer = ref(false)
const active = ref(null)

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 16) : '—')

const examsOf = (vid) => examAll.value.filter((e) => e.visit === vid)
const rxsOf = (vid) => rxAll.value.filter((r) => r.visit === vid)
const notesOf = (vid) => noteAll.value.filter((n) => n.visit === vid && n.confirmed)
const followsOf = (vid) => followAll.value.filter((f) => f.visit === vid)

const filteredPatients = computed(() => {
  const kw = keyword.value.trim()
  if (!kw) return patients.value
  return patients.value.filter((p) => (p.name || '').includes(kw) || (p.phone || '').includes(kw) || (p.username || '').includes(kw))
})

const load = async () => {
  loading.value = true
  try {
    const [vs, eo, rx, cn, fu] = await Promise.all([
      workflowApi.visits({ page_size: 300 }),
      workflowApi.examOrders({ page_size: 300 }),
      workflowApi.prescriptions({ page_size: 300 }),
      workflowApi.commNotes({ page_size: 300 }),
      workflowApi.followUps({ page_size: 300 }),
    ])
    visits.value = listOf(vs)
    examAll.value = listOf(eo)
    rxAll.value = listOf(rx)
    noteAll.value = listOf(cn)
    followAll.value = listOf(fu)

    const map = new Map()
    visits.value.forEach((v) => {
      const key = v.patient
      if (!map.has(key)) {
        map.set(key, {
          id: key,
          name: v.patient_name || v.patient_username,
          username: v.patient_username,
          phone: v.patient_phone,
          allergies: v.patient_allergies,
          visitCount: 0,
          lastDate: '',
          visits: [],
        })
      }
      const p = map.get(key)
      p.visitCount += 1
      p.visits.push(v)
      if (v.created_at && (!p.lastDate || v.created_at > p.lastDate)) p.lastDate = v.created_at
    })
    patients.value = Array.from(map.values())
      .map((p) => ({ ...p, lastDate: fmt(p.lastDate).slice(0, 10) }))
      .sort((a, b) => (b.lastDate > a.lastDate ? 1 : -1))
  } finally {
    loading.value = false
  }
}

const openPatient = (row) => {
  active.value = row
  drawer.value = true
}

onMounted(load)
</script>

<style scoped>
.dp-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }

.pt-cell { display: flex; align-items: center; gap: 10px; }
.pt-avatar {
  width: 34px; height: 34px; border-radius: 50%; color: #fff; font-weight: 800;
  background: linear-gradient(150deg, #FFBE7A, #E8862B);
  display: flex; align-items: center; justify-content: center;
}
.pt-name { font-weight: 800; color: var(--ink); font-size: 13.5px; }
.pt-sub { font-size: 11px; color: var(--ink-faint); }

.drawer-body { display: flex; flex-direction: column; gap: 14px; }
.patient-card {
  display: flex; align-items: center; gap: 12px; padding: 14px;
  border-radius: 18px; background: #F9FDFF; border: 2px dashed #CDE9F7;
}
.pc-avatar {
  width: 46px; height: 46px; border-radius: 50%; color: #fff; font-size: 18px; font-weight: 900;
  background: linear-gradient(150deg, #FFBE7A, #E8862B);
  display: flex; align-items: center; justify-content: center;
}
.pc-name { font-size: 16px; font-weight: 900; color: var(--ink); display: flex; gap: 8px; align-items: center; }
.pc-sub { font-size: 12px; color: var(--ink-soft); margin-top: 4px; }

.visit-block { border: 2px solid #FFE9C9; border-radius: 18px; overflow: hidden; background: #FFFDF7; }
.vb-head { display: flex; align-items: center; gap: 8px; padding: 10px 14px; background: #FFF6E6; flex-wrap: wrap; }
.vb-date { font-weight: 800; color: var(--ink); font-size: 13px; }
.vb-doctor { font-size: 11.5px; color: var(--ink-faint); margin-left: auto; }
.vb-body { padding: 12px 14px 14px; }
.kv { display: grid; grid-template-columns: 84px 1fr; gap: 8px; font-size: 12.5px; margin-bottom: 6px; }
.kv span { color: var(--ink-faint); font-weight: 700; }
.kv p { color: var(--ink-soft); line-height: 1.6; margin: 0; white-space: pre-wrap; }

.sub-block { margin-top: 10px; padding-top: 8px; border-top: 1px dashed #FFE9C9; }
.sub-title { font-size: 12.5px; font-weight: 800; color: var(--ink); margin-bottom: 6px; }
.sub-row { display: flex; gap: 8px; align-items: center; font-size: 12px; color: var(--ink-soft); flex-wrap: wrap; padding: 3px 0; }
.sub-row.rx { display: block; }
.rx-head { font-weight: 700; color: var(--ink); }
.rx-item { font-size: 11.8px; color: var(--ink-soft); padding-left: 8px; }
.price { color: var(--orange-deep); font-weight: 800; }
.result { color: var(--mint-deep); }
.note-item { font-size: 12px; color: var(--ink-soft); background: #F7FFFB; border-radius: 10px; padding: 8px 10px; margin-bottom: 6px; white-space: pre-wrap; }
</style>
