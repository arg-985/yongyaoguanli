<template>
  <div class="consult-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">✍️ 患者接诊</span>
        <h1>核对身份，<em>问诊开单</em>，一步不落</h1>
        <p>叫号 → 核对就诊卡 → 问诊记录 → 沟通录音转文字 → 检查单 / 处方 / 复诊 → 归档</p>
      </div>
      <el-button round @click="reloadAll">↻ 刷新</el-button>
    </div>

    <div class="consult-grid">
      <!-- 左侧候诊列表 -->
      <div class="candy-card tilt-sky picker">
        <div class="card-head">
          <span class="t-main">🙋 我的候诊 / 接诊中</span>
          <span class="pill sky">{{ visits.length }} 人</span>
        </div>
        <el-empty v-if="!visits.length" description="暂无待接诊患者" :image-size="70" />
        <div v-else class="visit-list">
          <div
            v-for="v in visits"
            :key="v.id"
            class="visit-item"
            :class="{ active: current && current.id === v.id }"
            @click="selectVisit(v)"
          >
            <div class="v-avatar">{{ (v.patient_name || v.patient_username || '?')[0] }}</div>
            <div class="v-info">
              <div class="v-name">
                {{ v.patient_name || v.patient_username }}
                <span class="pill" :class="v.visit_type === 'FIRST' ? 'sky' : 'mint'">{{ v.visit_type_display }}</span>
              </div>
              <div class="v-sub">{{ v.patient_phone || '—' }} · {{ v.status_display }}</div>
            </div>
            <span class="v-arrow">›</span>
          </div>
        </div>
      </div>

      <!-- 右侧接诊面板 -->
      <div v-if="current" class="candy-card panel">
        <div class="panel-head">
          <div>
            <div class="p-name">
              {{ current.patient_name || current.patient_username }}
              <span class="pill" :class="current.visit_type === 'FIRST' ? 'sky' : 'mint'">{{ current.visit_type_display }}</span>
              <span v-if="current.is_archived" class="pill pink">已归档 · 只读</span>
              <span v-else class="pill yellow">{{ current.status_display }}</span>
            </div>
            <div class="p-sub">
              手机 {{ current.patient_phone || '—' }} ·
              过敏史
              <b :class="current.patient_allergies ? 'danger' : ''">{{ current.patient_allergies || '无记录' }}</b>
              · 接诊时间 {{ fmt(current.created_at) }}
            </div>
          </div>
          <el-button v-if="!current.is_archived" type="success" round @click="finishVisit">完成接诊并归档</el-button>
        </div>

        <!-- ① 身份核对 -->
        <div class="step">
          <div class="step-title"><span class="step-no">1</span>身份核对 · 初诊还是复诊</div>
          <div class="id-row">
            <el-radio-group v-model="idForm.visit_type" :disabled="current.is_archived">
              <el-radio-button label="FIRST">初诊</el-radio-button>
              <el-radio-button label="RETURN">复诊</el-radio-button>
            </el-radio-group>
            <el-input v-model="idForm.id_card_no" placeholder="就诊卡号 / 病历号" style="width:220px" :disabled="current.is_archived" />
            <el-checkbox v-model="idForm.identity_verified" :disabled="current.is_archived">已核对就诊卡 / 病历，身份一致</el-checkbox>
            <el-button type="primary" plain :disabled="current.is_archived" @click="saveIdentity">保存核对结果</el-button>
          </div>
        </div>

        <!-- ② 问诊与病历 -->
        <div class="step">
          <div class="step-title"><span class="step-no">2</span>问诊记录 · 电子病历（只能修改本人接诊记录）</div>
          <div class="form-grid">
            <el-input v-model="form.chief_complaint" type="textarea" :rows="2" placeholder="主诉：如“颈前不适、乏力 2 周”" :disabled="current.is_archived" />
            <el-input v-model="form.history" type="textarea" :rows="2" placeholder="现病史 / 既往史 / 用药史" :disabled="current.is_archived" />
            <el-input v-model="form.diagnosis" type="textarea" :rows="2" placeholder="初步诊断" :disabled="current.is_archived" />
            <el-input v-model="form.advice" type="textarea" :rows="2" placeholder="处置意见 / 注意事项" :disabled="current.is_archived" />
          </div>
          <div class="form-actions">
            <span class="hint">初步判断与下一步计划可写在「诊断」「处置意见」中，检查原因可在沟通记录里说明</span>
            <el-button type="primary" :disabled="current.is_archived" @click="saveRecord">保存病历</el-button>
          </div>
        </div>

        <!-- ③ 沟通录音转文字 -->
        <div class="step">
          <div class="step-title"><span class="step-no">3</span>医患沟通 · 录音转文字（医生确认后录入系统）</div>
          <div class="rec-bar">
            <el-button :type="recording ? 'danger' : 'primary'" round @click="recording ? stopRec() : startRec()">
              {{ recording ? '⏹ 停止录音' : '🎙 开始录音转写' }}
            </el-button>
            <span class="rec-status" :class="{ live: recording }">
              {{ recording ? '正在倾听，请向患者解释检查原因与用药方案…' : '支持 Chrome / Edge 浏览器语音识别，识别结果可在下方修改' }}
            </span>
            <el-button link @click="transcript = ''">清空</el-button>
          </div>
          <el-input
            v-model="transcript"
            type="textarea"
            :rows="4"
            placeholder="录音识别的文字会出现在这里，可先手动修改，确认准确无误后再点「确定录入」"
            :disabled="current.is_archived"
          />
          <div class="form-actions">
            <span class="hint">录入后进入系统沟通档案，患者可在自己的就诊档案中查看</span>
            <el-button type="success" :disabled="current.is_archived || !transcript.trim()" @click="confirmNote">
              确定录入系统
            </el-button>
          </div>
          <div v-if="notes.length" class="note-list">
            <div v-for="n in notes" :key="n.id" class="note-item">
              <div class="note-head">
                <span class="pill mint">已确认</span>
                <span class="note-time">{{ fmt(n.created_at) }}</span>
              </div>
              <div class="note-text">{{ n.transcript }}</div>
            </div>
          </div>
        </div>

        <!-- ④ 检查单 -->
        <div class="step">
          <div class="step-title"><span class="step-no">4</span>开具检查单</div>
          <div class="form-actions left">
            <el-button type="primary" plain :disabled="current.is_archived" @click="openExam">＋ 开具检查单</el-button>
            <span class="hint">开单时请向患者解释检查目的，开单会自动生成检查费待缴单</span>
          </div>
          <div v-if="exams.length" class="mini-table">
            <div v-for="e in exams" :key="e.id" class="mini-row">
              <span class="mini-name">🔬 {{ e.name }}</span>
              <span class="pill sky">{{ e.category_display }}</span>
              <span class="mini-price">¥{{ e.price }}</span>
              <span class="pill" :class="e.status === 'PENDING' ? 'yellow' : 'mint'">{{ e.status_display }}</span>
            </div>
          </div>
        </div>

        <!-- ⑤ 处方 -->
        <div class="step">
          <div class="step-title"><span class="step-no">5</span>开药 / 治疗建议</div>
          <div class="form-actions left">
            <el-button type="primary" plain :disabled="current.is_archived" @click="openRx">＋ 开具处方</el-button>
            <span class="hint">医生可开药、调整剂量，但不能改动药库库存与定价</span>
          </div>
          <div v-if="rxs.length" class="rx-list">
            <div v-for="r in rxs" :key="r.id" class="rx-item">
              <div class="rx-head">
                <span class="rx-title">处方 #{{ r.id }}</span>
                <span class="pill purple">{{ r.status === 'ISSUED' ? '已开具' : '已作废' }}</span>
                <span class="rx-amount">合计 ¥{{ r.total_amount }}</span>
                <span class="rx-time">{{ fmt(r.created_at) }}</span>
              </div>
              <div class="rx-items">
                <div v-for="it in r.items" :key="it.id" class="rx-line">
                  <b>{{ it.medication_name }}</b>
                  <span>{{ it.specification }}</span>
                  <span>{{ it.dosage }} · {{ it.frequency }} · {{ it.days }} 天</span>
                  <span>×{{ it.quantity }}</span>
                  <span>¥{{ it.unit_price }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ⑥ 复诊 -->
        <div class="step">
          <div class="step-title"><span class="step-no">6</span>预约复诊</div>
          <div class="form-actions left">
            <el-date-picker v-model="followForm.due_date" type="date" value-format="YYYY-MM-DD" placeholder="复诊日期" :disabled="current.is_archived" />
            <el-input v-model="followForm.note" placeholder="复诊说明，如“复查甲功后调整优甲乐剂量”" style="width:300px" :disabled="current.is_archived" />
            <el-button type="primary" plain :disabled="current.is_archived || !followForm.due_date" @click="saveFollowUp">安排复诊</el-button>
          </div>
          <div v-if="follows.length" class="mini-table">
            <div v-for="f in follows" :key="f.id" class="mini-row">
              <span class="mini-name">📅 {{ f.due_date }}</span>
              <span class="mini-note">{{ f.note || '复诊' }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="candy-card tilt-yellow empty-panel">
        <div class="empty-emoji">🩺</div>
        <div class="empty-title">请从左侧选择一位患者开始接诊</div>
        <div class="empty-sub">接诊顺序：核对身份 → 问诊记录 → 沟通录入 → 检查单 → 处方 → 复诊 → 归档</div>
      </div>
    </div>

    <!-- 检查单弹窗 -->
    <el-dialog v-model="examDialog" title="开具检查单" width="460px">
      <el-form label-width="88px">
        <el-form-item label="检查项目">
          <el-input v-model="examForm.name" placeholder="如：甲状腺功能三项 / 血常规" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="examForm.category" style="width:100%">
            <el-option label="检验" value="LAB" />
            <el-option label="影像" value="IMG" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="费用">
          <el-input-number v-model="examForm.price" :min="0" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="examDialog = false">取消</el-button>
        <el-button type="primary" @click="submitExam">确认开单</el-button>
      </template>
    </el-dialog>

    <!-- 处方弹窗 -->
    <el-dialog v-model="rxDialog" title="开具处方" width="760px">
      <div class="rx-form-head">
        <el-select v-model="rxItem.medication" filterable placeholder="选择药品（药库）" style="width:260px" @change="onPickMed">
          <el-option v-for="m in meds" :key="m.id" :label="`${m.name} ${m.specification || ''} ¥${m.price}`" :value="m.id" />
        </el-select>
        <el-input v-model="rxItem.dosage" placeholder="每次剂量，如 1 片" style="width:150px" />
        <el-select v-model="rxItem.frequency" placeholder="频次" style="width:130px">
          <el-option label="每日一次" value="每日一次" />
          <el-option label="每日两次" value="每日两次" />
          <el-option label="每日三次" value="每日三次" />
          <el-option label="每日四次" value="每日四次" />
        </el-select>
        <el-input-number v-model="rxItem.days" :min="1" :max="90" style="width:110px" />
        <el-input-number v-model="rxItem.quantity" :min="1" :precision="0" style="width:110px" />
        <el-button type="primary" plain @click="addRxItem">添加</el-button>
      </div>
      <el-table :data="rxItems" size="small" border style="margin-top:12px">
        <el-table-column prop="medication_name" label="药品" min-width="140" />
        <el-table-column prop="dosage" label="剂量" width="100" />
        <el-table-column prop="frequency" label="频次" width="100" />
        <el-table-column prop="days" label="天数" width="80" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="unit_price" label="单价" width="90" />
        <el-table-column label="" width="70">
          <template #default="{ $index }">
            <el-button link type="danger" @click="rxItems.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-input v-model="rxDiagnosis" placeholder="处方诊断（默认取病历诊断）" style="margin-top:10px" />
      <div class="rx-total">合计：<b>¥{{ rxTotal }}</b>（费用将生成待缴药费单）</div>
      <template #footer>
        <el-button @click="rxDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!rxItems.length" @click="submitRx">开具处方</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { medicationApi, workflowApi } from '../../api/modules'

const route = useRoute()
const router = useRouter()

const allVisits = ref([])
const examAll = ref([])
const noteAll = ref([])
const rxAll = ref([])
const followAll = ref([])
const meds = ref([])

const current = ref(null)
const form = reactive({ chief_complaint: '', history: '', diagnosis: '', advice: '' })
const idForm = reactive({ visit_type: 'FIRST', id_card_no: '', identity_verified: false })
const transcript = ref('')
const recording = ref(false)
let recognizer = null

const examDialog = ref(false)
const examForm = reactive({ name: '', category: 'LAB', price: 120 })

const rxDialog = ref(false)
const rxItems = ref([])
const rxItem = reactive({ medication: null, medication_name: '', dosage: '1 片', frequency: '每日两次', days: 7, quantity: 1, unit_price: 0 })
const rxDiagnosis = ref('')

const followForm = reactive({ due_date: '', note: '' })

const visits = computed(() =>
  allVisits.value.filter((v) => ['WAITING', 'IN_PROGRESS'].includes(v.status))
)
const exams = computed(() => examAll.value.filter((e) => current.value && e.visit === current.value.id))
const notes = computed(() => noteAll.value.filter((n) => current.value && n.visit === current.value.id && n.confirmed))
const rxs = computed(() => rxAll.value.filter((r) => current.value && r.visit === current.value.id))
const follows = computed(() => followAll.value.filter((f) => current.value && f.visit === current.value.id))
const rxTotal = computed(() =>
  rxItems.value.reduce((sum, it) => sum + Number(it.quantity) * Number(it.unit_price), 0).toFixed(2)
)

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 16) : '—')

const reloadAll = async () => {
  const [vs, eo, cn, rx, fu] = await Promise.all([
    workflowApi.visits({ page_size: 100 }),
    workflowApi.examOrders({ page_size: 200 }),
    workflowApi.commNotes({ page_size: 200 }),
    workflowApi.prescriptions({ page_size: 200 }),
    workflowApi.followUps({ page_size: 200 }),
  ])
  allVisits.value = listOf(vs)
  examAll.value = listOf(eo)
  noteAll.value = listOf(cn)
  rxAll.value = listOf(rx)
  followAll.value = listOf(fu)
}

const selectVisit = (v) => {
  current.value = v
  form.chief_complaint = v.chief_complaint || ''
  form.history = v.history || ''
  form.diagnosis = v.diagnosis || ''
  form.advice = v.advice || ''
  idForm.visit_type = v.visit_type || 'FIRST'
  idForm.id_card_no = v.id_card_no || ''
  idForm.identity_verified = !!v.identity_verified
  transcript.value = ''
  rxDiagnosis.value = v.diagnosis || ''
}

const applyVisit = (v) => {
  const idx = allVisits.value.findIndex((x) => x.id === v.id)
  if (idx >= 0) allVisits.value[idx] = v
  if (current.value && current.value.id === v.id) {
    const keep = current.value
    current.value = v
    form.chief_complaint = v.chief_complaint || ''
    form.history = v.history || ''
    form.diagnosis = v.diagnosis || ''
    form.advice = v.advice || ''
    idForm.visit_type = v.visit_type || keep.visit_type
    idForm.id_card_no = v.id_card_no || ''
    idForm.identity_verified = !!v.identity_verified
  }
}

const saveIdentity = async () => {
  const v = await workflowApi.visitUpdate(current.value.id, { ...idForm })
  applyVisit(v)
  ElMessage.success(idForm.identity_verified ? '身份核对完成，已标记为已核对' : '核对信息已保存')
}

const saveRecord = async () => {
  const v = await workflowApi.visitUpdate(current.value.id, { ...form })
  applyVisit(v)
  ElMessage.success('电子病历已保存')
}

// ---------- 录音转文字 ----------
const startRec = () => {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SR) {
    ElMessage.warning('当前浏览器不支持语音识别，请使用 Chrome / Edge，或直接手动输入文字')
    return
  }
  recognizer = new SR()
  recognizer.lang = 'zh-CN'
  recognizer.continuous = true
  recognizer.interimResults = true
  recognizer.onresult = (e) => {
    let text = ''
    for (let i = e.resultIndex; i < e.results.length; i += 1) {
      if (e.results[i].isFinal) text += e.results[i][0].transcript
    }
    if (text) transcript.value += (transcript.value ? '\n' : '') + text
  }
  recognizer.onerror = (e) => {
    ElMessage.warning(`语音识别出错：${e.error}`)
    recording.value = false
  }
  recognizer.onend = () => { recording.value = false }
  recognizer.start()
  recording.value = true
}

const stopRec = () => {
  try { recognizer && recognizer.stop() } catch (e) { /* ignore */ }
  recording.value = false
}

const confirmNote = async () => {
  await workflowApi.visitNotes(current.value.id, { transcript: transcript.value.trim(), confirmed: true })
  await reloadAll()
  transcript.value = ''
  ElMessage.success('沟通内容已确认并录入系统')
}

// ---------- 检查单 ----------
const openExam = () => {
  examForm.name = ''
  examForm.category = 'LAB'
  examForm.price = 120
  examDialog.value = true
}
const submitExam = async () => {
  if (!examForm.name.trim()) { ElMessage.warning('请填写检查项目'); return }
  await workflowApi.visitExamOrders(current.value.id, { ...examForm })
  examDialog.value = false
  await reloadAll()
  ElMessage.success('检查单已开具，检查费已加入患者待缴费')
}

// ---------- 处方 ----------
const openRx = async () => {
  rxItems.value = []
  rxDiagnosis.value = current.value.diagnosis || ''
  rxDialog.value = true
  if (!meds.value.length) {
    const res = await medicationApi.list({ page_size: 200 })
    meds.value = listOf(res)
  }
}
const onPickMed = (id) => {
  const m = meds.value.find((x) => x.id === id)
  if (m) {
    rxItem.medication_name = m.name
    rxItem.unit_price = Number(m.price || 0)
  }
}
const addRxItem = () => {
  if (!rxItem.medication) { ElMessage.warning('请选择药品'); return }
  rxItems.value.push({
    medication: rxItem.medication,
    medication_name: rxItem.medication_name,
    dosage: rxItem.dosage,
    frequency: rxItem.frequency,
    days: rxItem.days,
    quantity: rxItem.quantity,
    unit_price: rxItem.unit_price,
  })
}
const submitRx = async () => {
  await workflowApi.visitPrescriptions(current.value.id, {
    diagnosis: rxDiagnosis.value,
    items: rxItems.value,
  })
  rxDialog.value = false
  await reloadAll()
  ElMessage.success('处方已开具，药品已同步到患者用药计划')
}

// ---------- 复诊 ----------
const saveFollowUp = async () => {
  await workflowApi.visitFollowUp(current.value.id, { ...followForm })
  followForm.due_date = ''
  followForm.note = ''
  await reloadAll()
  ElMessage.success('复诊已安排，患者可在就诊档案中看到')
}

// ---------- 归档 ----------
const finishVisit = async () => {
  try {
    await ElMessageBox.confirm('完成接诊后病历将归档，直接修改会被拒绝（需提交修改申请留痕），确认完成？', '完成接诊', { type: 'warning' })
  } catch (e) { return }
  const v = await workflowApi.visitFinish(current.value.id)
  applyVisit(v)
  ElMessage.success('接诊已完成，病历已归档')
}

const pickFromQuery = () => {
  const id = Number(route.query.visit)
  if (!id) return
  const v = allVisits.value.find((x) => x.id === id)
  if (v) selectVisit(v)
}

watch(() => route.query.visit, () => pickFromQuery())

onMounted(async () => {
  await reloadAll()
  if (route.query.visit) pickFromQuery()
  else if (visits.value.length) selectVisit(visits.value[0])
})
</script>

<style scoped>
.consult-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.consult-grid { display: grid; grid-template-columns: 320px 1fr; gap: 18px; align-items: start; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.t-main { font-size: 15px; font-weight: 800; color: var(--ink); }

.picker { padding: 18px 18px 20px; position: sticky; top: 10px; }
.visit-list { display: flex; flex-direction: column; gap: 8px; }
.visit-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 14px; border: 2px dashed #CDE9F7; background: #F9FDFF; cursor: pointer;
  transition: all .15s;
}
.visit-item:hover { background: #EFF9FF; }
.visit-item.active { border-style: solid; border-color: #6FC4EF; background: #E1F2FC; }
.v-avatar {
  width: 34px; height: 34px; border-radius: 50%; color: #fff; font-weight: 800;
  background: linear-gradient(150deg, #FFBE7A, #E8862B);
  display: flex; align-items: center; justify-content: center;
}
.v-info { flex: 1; min-width: 0; }
.v-name { font-size: 13.5px; font-weight: 800; color: var(--ink); display: flex; gap: 6px; align-items: center; }
.v-sub { font-size: 11px; color: var(--ink-faint); margin-top: 2px; }
.v-arrow { color: var(--ink-faint); font-weight: 800; }

.panel { padding: 22px 24px 26px; }
.panel-head {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;
  padding-bottom: 14px; border-bottom: 2px dashed var(--cream-line); margin-bottom: 6px;
}
.p-name { font-size: 18px; font-weight: 900; color: var(--ink); display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.p-sub { font-size: 12px; color: var(--ink-soft); margin-top: 6px; }
.danger { color: var(--pink-deep); }

.step { padding: 16px 0; border-bottom: 1px dashed #FFE9C9; }
.step:last-child { border-bottom: none; }
.step-title { font-size: 14px; font-weight: 800; color: var(--ink); margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.step-no {
  width: 22px; height: 22px; border-radius: 50%; background: linear-gradient(150deg, #FFBE7A, #E8862B);
  color: #fff; font-size: 12px; font-weight: 900; display: flex; align-items: center; justify-content: center;
}
.id-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-actions { display: flex; justify-content: flex-end; align-items: center; gap: 12px; margin-top: 10px; }
.form-actions.left { justify-content: flex-start; flex-wrap: wrap; }
.hint { font-size: 11.5px; color: var(--ink-faint); }

.rec-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.rec-status { font-size: 12px; color: var(--ink-faint); }
.rec-status.live { color: var(--pink-deep); font-weight: 700; }

.note-list { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.note-item { background: #F7FFFB; border: 2px dashed #C9EDDF; border-radius: 14px; padding: 10px 12px; }
.note-head { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.note-time { font-size: 11px; color: var(--ink-faint); }
.note-text { font-size: 12.5px; color: var(--ink-soft); line-height: 1.6; white-space: pre-wrap; }

.mini-table { margin-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.mini-row {
  display: flex; align-items: center; gap: 10px; font-size: 12.5px;
  background: #FFFDF7; border: 1px solid #FFE9C9; border-radius: 12px; padding: 8px 12px;
}
.mini-name { font-weight: 800; color: var(--ink); }
.mini-price { color: var(--orange-deep); font-weight: 800; }
.mini-note { color: var(--ink-soft); }

.rx-list { margin-top: 10px; display: flex; flex-direction: column; gap: 10px; }
.rx-item { background: #FBF8FF; border: 2px dashed #E4D8FF; border-radius: 16px; padding: 12px 14px; }
.rx-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
.rx-title { font-weight: 900; color: var(--ink); }
.rx-amount { font-weight: 900; color: var(--orange-deep); }
.rx-time { font-size: 11px; color: var(--ink-faint); }
.rx-items { display: flex; flex-direction: column; gap: 4px; }
.rx-line { display: flex; gap: 14px; font-size: 12px; color: var(--ink-soft); flex-wrap: wrap; }

.rx-form-head { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.rx-total { text-align: right; font-size: 13px; color: var(--ink-soft); margin-top: 10px; }

.empty-panel { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 360px; text-align: center; }
.empty-emoji { font-size: 54px; }
.empty-title { font-size: 16px; font-weight: 800; color: var(--ink); margin-top: 12px; }
.empty-sub { font-size: 12px; color: var(--ink-faint); margin-top: 8px; max-width: 420px; line-height: 1.7; }

@media (max-width: 1100px) {
  .consult-grid { grid-template-columns: 1fr; }
  .picker { position: static; }
  .form-grid { grid-template-columns: 1fr; }
}
</style>
