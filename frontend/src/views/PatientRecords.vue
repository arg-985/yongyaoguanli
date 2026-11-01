<template>
  <div class="pr-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">📂 我的就诊档案</span>
        <h1>我的<em>挂号、病历、报告、处方</em></h1>
        <p>档案为只读，患者不能修改病历；医生确认录入的沟通内容也会展示在这里</p>
      </div>
      <span class="pill purple">🔒 只读档案</span>
    </div>

    <div class="candy-card tilt-sky">
      <el-tabs v-model="tab">
        <el-tab-pane name="appointments">
          <template #label><span class="tab-label">📅 挂号记录（{{ appointments.length }}）</span></template>
          <el-table :data="appointments" stripe>
            <el-table-column prop="visit_date" label="就诊日期" width="120" />
            <el-table-column prop="time_slot" label="时段" width="140" />
            <el-table-column prop="department_name" label="科室" width="110" />
            <el-table-column prop="doctor_name" label="医生" width="110" />
            <el-table-column label="挂号费" width="100">
              <template #default="{ row }">¥{{ row.fee }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'DONE' ? 'success' : row.status === 'CANCELLED' ? 'info' : 'warning'" size="small">
                  {{ row.status_display }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!appointments.length" description="还没有挂号记录" :image-size="80" />
        </el-tab-pane>

        <el-tab-pane name="visits">
          <template #label><span class="tab-label">🗂️ 电子病历（{{ visits.length }}）</span></template>
          <el-table :data="visits" stripe>
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="expand-box">
                  <div class="kv"><span>主诉</span><p>{{ row.chief_complaint || '—' }}</p></div>
                  <div class="kv"><span>现病史</span><p>{{ row.history || '—' }}</p></div>
                  <div class="kv"><span>诊断</span><p>{{ row.diagnosis || '—' }}</p></div>
                  <div class="kv"><span>处置意见</span><p>{{ row.advice || '—' }}</p></div>
                  <div v-if="notesOf(row.id).length" class="kv"><span>沟通记录</span>
                    <div>
                      <div v-for="n in notesOf(row.id)" :key="n.id" class="note">{{ n.transcript }}</div>
                    </div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="就诊时间" width="160">
              <template #default="{ row }">{{ fmt(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="doctor_name" label="医生" width="110" />
            <el-table-column prop="visit_type_display" label="类型" width="90" />
            <el-table-column prop="diagnosis" label="诊断" min-width="180">
              <template #default="{ row }">{{ row.diagnosis || '—' }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_archived ? 'success' : 'warning'" size="small">
                  {{ row.is_archived ? '已归档' : row.status_display }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!visits.length" description="还没有就诊记录" :image-size="80" />
        </el-tab-pane>

        <el-tab-pane name="exams">
          <template #label><span class="tab-label">🔬 检查报告（{{ exams.length }}）</span></template>
          <el-table :data="exams" stripe>
            <el-table-column prop="name" label="检查项目" min-width="180" />
            <el-table-column prop="category_display" label="类别" width="90" />
            <el-table-column prop="doctor_name" label="开单医生" width="110" />
            <el-table-column label="费用" width="100">
              <template #default="{ row }">¥{{ row.price }}</template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.status === 'REPORTED' ? 'success' : 'warning'" size="small">{{ row.status_display }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="报告结果" min-width="200">
              <template #default="{ row }">{{ row.result || '报告出具中…' }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!exams.length" description="还没有检查报告" :image-size="80" />
        </el-tab-pane>

        <el-tab-pane name="prescriptions">
          <template #label><span class="tab-label">💊 处方记录（{{ prescriptions.length }}）</span></template>
          <div v-for="r in prescriptions" :key="r.id" class="rx-card">
            <div class="rx-head">
              <b>处方 #{{ r.id }}</b>
              <span class="pill purple">{{ r.status === 'ISSUED' ? '已开具' : '已作废' }}</span>
              <span class="rx-doctor">{{ r.doctor_name }} 医生</span>
              <span class="rx-time">{{ fmt(r.created_at) }}</span>
              <span class="rx-amount">合计 ¥{{ r.total_amount }}</span>
            </div>
            <div class="rx-diag" v-if="r.diagnosis">诊断：{{ r.diagnosis }}</div>
            <div class="rx-items">
              <div v-for="it in r.items" :key="it.id" class="rx-line">
                <b>{{ it.medication_name }}</b>
                <span>{{ it.specification }}</span>
                <span>{{ it.dosage }} · {{ it.frequency }} · {{ it.days }} 天</span>
                <span>×{{ it.quantity }}</span>
                <span>单价 ¥{{ it.unit_price }}</span>
              </div>
            </div>
          </div>
          <el-empty v-if="!prescriptions.length" description="还没有处方记录" :image-size="80" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { workflowApi } from '../api/modules'

const tab = ref('appointments')
const appointments = ref([])
const visits = ref([])
const exams = ref([])
const prescriptions = ref([])
const notes = ref([])

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 16) : '—')
const notesOf = (vid) => notes.value.filter((n) => n.visit === vid && n.confirmed)

const load = async () => {
  const [ap, vs, eo, rx, cn] = await Promise.all([
    workflowApi.appointments({ page_size: 100 }),
    workflowApi.visits({ page_size: 100 }),
    workflowApi.examOrders({ page_size: 100 }),
    workflowApi.prescriptions({ page_size: 100 }),
    workflowApi.commNotes({ page_size: 100 }),
  ])
  appointments.value = listOf(ap)
  visits.value = listOf(vs)
  exams.value = listOf(eo)
  prescriptions.value = listOf(rx)
  notes.value = listOf(cn)
}

onMounted(load)
</script>

<style scoped>
.pr-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.tab-label { font-weight: 800; }
.expand-box { padding: 8px 22px; display: flex; flex-direction: column; gap: 6px; }
.kv { display: grid; grid-template-columns: 80px 1fr; gap: 8px; font-size: 12.5px; }
.kv span { color: var(--ink-faint); font-weight: 700; }
.kv p { margin: 0; color: var(--ink-soft); line-height: 1.6; white-space: pre-wrap; }
.note { font-size: 12px; color: var(--mint-deep); background: #F7FFFB; border-radius: 10px; padding: 6px 10px; margin-bottom: 4px; white-space: pre-wrap; }

.rx-card { border: 2px dashed #E4D8FF; background: #FBF8FF; border-radius: 16px; padding: 12px 14px; margin-bottom: 10px; }
.rx-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 13px; color: var(--ink); }
.rx-doctor, .rx-time { font-size: 11.5px; color: var(--ink-faint); }
.rx-amount { margin-left: auto; font-weight: 900; color: var(--orange-deep); }
.rx-diag { font-size: 12px; color: var(--ink-soft); margin: 6px 0; }
.rx-items { display: flex; flex-direction: column; gap: 4px; }
.rx-line { display: flex; gap: 14px; font-size: 12px; color: var(--ink-soft); flex-wrap: wrap; }
</style>
