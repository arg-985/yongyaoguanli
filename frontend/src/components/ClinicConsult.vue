<template>
  <div class="clinic-consult">
    <div class="assist-head">
      <div class="head-left">
        <span class="jelly pink">🩺</span>
        <div>
          <div class="t-main">药药帮你看一看</div>
          <div class="t-sub">选症状 · 说情况 · 出建议，还能顺便看看药箱里有没有</div>
        </div>
      </div>
      <span class="pill" :class="llm.enabled ? 'mint' : 'yellow'">
        {{ llm.enabled ? 'AI 增强' : '规则引擎' }}
      </span>
    </div>

    <div class="assist-body">
      <div class="form-side">
        <div v-if="auth.isAdmin" class="patient-row">
          <span class="field-label">患者</span>
          <el-select v-model="patient" filterable clearable placeholder="选择患者" style="flex:1">
            <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </div>

        <div class="symptom-grid">
          <div
            v-for="s in symptomOptions"
            :key="s.code"
            class="symptom-tile"
            :class="{ active: form.symptoms.includes(s.code) }"
            @click="toggleSymptom(s.code)"
          >
            <div class="emoji">{{ emojiMap[s.code] || '💊' }}</div>
            <div class="name">{{ s.name }}</div>
            <span class="sticker">PICK</span>
          </div>
        </div>

        <div class="mini-fields">
          <div class="field">
            <span class="field-label">持续</span>
            <el-input-number v-model="form.duration_days" :min="1" :max="365" size="small" controls-position="right" style="width:100px" />
            <span class="unit-text">天</span>
          </div>
          <div class="field">
            <span class="field-label">程度</span>
            <el-rate v-model="form.severity" :max="5" />
          </div>
        </div>

        <el-input
          v-model="form.free_text"
          type="textarea"
          :rows="2"
          placeholder="补充：正在吃的药 / 过敏史 / 昨晚开始的低烧…"
        />

        <el-button class="ask-btn" type="primary" :loading="loading" @click="onConsult">
          <span v-if="!loading">🪄 让药药分析</span>
          <span v-else>正在分析…</span>
        </el-button>
      </div>

      <div class="result-side">
        <div v-if="result" class="result-inner">
          <div v-if="warningItems.length" class="warn-list">
            <div v-for="(w, i) in warningItems" :key="i" class="warn-item" :class="w.level">
              <span class="warn-icon">{{ w.level === 'high' ? '⛔' : w.level === 'medium' ? '⚠️' : '💡' }}</span>
              <div>
                <div class="warn-title">{{ w.title }}</div>
                <div v-if="w.detail" class="warn-detail">{{ w.detail }}</div>
              </div>
            </div>
          </div>

          <div class="advice-bubble">
            <span class="bubble-mascot">🐶</span>
            <div class="advice-text">{{ result.advice }}</div>
          </div>

          <div class="sub-title">
            <span>推荐药品</span>
            <span class="pill yellow">{{ result.recommendations?.length || 0 }} 个</span>
            <span class="pill sky">{{ result.source === 'llm' ? 'AI 生成' : '规则匹配' }}</span>
          </div>

          <el-empty
            v-if="!result.recommendations || result.recommendations.length === 0"
            description="暂未匹配到合适的非处方药"
            :image-size="70"
          />
          <div v-else class="rec-grid">
            <div v-for="rec in result.recommendations" :key="rec.medication_id" class="rec-card">
              <div class="rec-top">
                <span class="rec-icon">💊</span>
                <div class="rec-name">{{ rec.name }}</div>
              </div>
              <div class="rec-tags">
                <span v-if="rec.expiry_status === 'expired'" class="pill pink">已过期勿用</span>
                <span v-else-if="rec.stock_available" class="pill mint">药箱有货</span>
                <span v-else-if="rec.expiry_status === 'soon'" class="pill yellow">临近过期</span>
                <span v-else class="pill sky">需购买</span>
              </div>
              <div class="rec-line"><b>用法</b>{{ rec.dosage || '-' }}</div>
              <div class="rec-reason">{{ rec.reason }}</div>
            </div>
          </div>
        </div>

        <div v-else class="result-empty">
          <div class="empty-face">( ╹▽╹ )</div>
          <div class="empty-title">药药在等你</div>
          <div class="empty-sub">勾选症状，点「让药药分析」<br />小狗管家会跑过来送建议</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { clinicApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const result = ref(null)
const symptomOptions = ref([])
const patients = ref([])
const patient = ref(null)
const llm = reactive({ enabled: false, model: '' })

const emojiMap = {
  cold: '🤧', fever: '🌡️', cough: '😷', sore_throat: '🍵', nasal: '👃',
  headache: '🤕', diarrhea: '🚽', stomach: '🍽️', allergy: '🌼', insomnia: '😴', pain: '🩹'
}

const form = reactive({ symptoms: [], duration_days: 3, severity: 2, free_text: '' })

const warningItems = computed(() =>
  (result.value?.warnings || []).map(w => {
    if (typeof w === 'string') return { level: 'info', title: w, detail: '' }
    return { level: w.level || 'info', title: w.title || '', detail: w.detail || '' }
  })
)

const toggleSymptom = (code) => {
  form.symptoms = form.symptoms.includes(code)
    ? form.symptoms.filter(c => c !== code)
    : [...form.symptoms, code]
}

const onConsult = async () => {
  if (auth.isAdmin && !patient.value) {
    ElMessage.warning('请先选择患者')
    return
  }
  if (!form.symptoms.length && !form.free_text.trim()) {
    ElMessage.warning('请至少选择一个症状或填写补充描述')
    return
  }
  loading.value = true
  try {
    const payload = {
      symptoms: form.symptoms,
      duration_days: form.duration_days,
      severity: form.severity,
      free_text: form.free_text.trim()
    }
    if (patient.value) payload.patient_id = patient.value
    result.value = await clinicApi.consult(payload)
    ElMessage.success('建议已生成，小狗管家跑起来啦')
    window.dispatchEvent(new CustomEvent('sprite:celebrate', {
      detail: {
        raw: result.value,
        title: '分析完成啦！',
        text: result.value.recommendations?.[0]?.name
          ? `推荐试试 ${result.value.recommendations[0].name}`
          : '暂时没有匹配到合适的药，看看建议吧'
      }
    }))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const [symptomData, llmData] = await Promise.all([
      clinicApi.symptoms(),
      clinicApi.llmStatus()
    ])
    symptomOptions.value = symptomData.results || symptomData || []
    llm.enabled = !!llmData?.enabled
    llm.model = llmData?.model || ''
  } catch (e) {
    symptomOptions.value = []
  }
  if (auth.isAdmin) {
    const data = await userApi.list({ role: 'patient', page_size: 200 })
    patients.value = data.results || data || []
  }
})
</script>

<style scoped>
.assist-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.head-left { display: flex; align-items: center; gap: 12px; flex: 1; }
.t-main { font-size: 16px; font-weight: 800; color: var(--ink); }
.t-sub { font-size: 11px; color: var(--ink-faint); }

.assist-body { display: grid; grid-template-columns: minmax(300px, 400px) 1fr; gap: 20px; }
.form-side { display: flex; flex-direction: column; gap: 12px; }
.patient-row { display: flex; align-items: center; gap: 10px; }
.field-label { font-size: 12px; font-weight: 700; color: var(--ink-soft); white-space: nowrap; }

.symptom-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; }
.symptom-tile { padding: 10px 4px 9px; border-radius: 14px; border: 2px solid #FFE6A8; background: #FFFCF0; box-shadow: 0 3px 0 #FFE3A1; cursor: pointer; text-align: center; position: relative; transition: transform .15s ease; }
.symptom-tile:hover { transform: translateY(-2px); }
.symptom-tile.active { border-color: var(--pink); background: #FFF3F6; box-shadow: 0 3px 0 var(--pink-deep); }
.symptom-tile .emoji { font-size: 20px; line-height: 1.2; }
.symptom-tile .name { font-size: 11px; font-weight: 700; color: var(--ink); margin-top: 3px; }
.symptom-tile .sticker { position: absolute; right: 3px; bottom: 2px; font-size: 7px; font-weight: 800; color: #fff; background: var(--sky); border-radius: 4px; padding: 0 3px; transform: rotate(-6deg); }

.mini-fields { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.field { display: flex; align-items: center; gap: 6px; }
.unit-text { font-size: 12px; color: var(--ink-faint); }

.ask-btn { width: 100%; height: 42px; font-size: 14px; font-weight: 800; border-radius: 999px; }

.result-side { background: #F9FCF8; border: 2px dashed #D6EFE2; border-radius: 20px; padding: 16px; min-height: 260px; display: flex; flex-direction: column; }
.result-empty { margin: auto; text-align: center; }
.empty-face { font-size: 22px; font-weight: 800; color: var(--pink-deep); background: #FFF0F4; border: 2px solid #FFD3DF; border-radius: 50%; width: 78px; height: 78px; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px; box-shadow: 0 5px 0 #FFE4EB; }
.empty-title { font-size: 14px; font-weight: 800; color: var(--ink); }
.empty-sub { font-size: 12px; color: var(--ink-faint); line-height: 1.7; margin-top: 4px; }

.warn-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.warn-item { display: flex; gap: 8px; padding: 8px 12px; border-radius: 12px; border: 2px dashed; }
.warn-item.high { background: #FFF1F2; border-color: #FFC2CB; }
.warn-item.medium { background: #FFF7E5; border-color: #FFDC9E; }
.warn-item.info { background: #F1F8FD; border-color: #C6E5F5; }
.warn-icon { font-size: 15px; }
.warn-title { font-size: 12.5px; font-weight: 800; color: #A83B48; }
.warn-item.medium .warn-title { color: #A97716; }
.warn-item.info .warn-title { color: #3C7D9E; }
.warn-detail { font-size: 11.5px; color: var(--ink-soft); line-height: 1.6; }

.advice-bubble { display: flex; gap: 10px; background: linear-gradient(135deg, #FFFBF0, #FFF4E2); border: 2px solid #FFE6B8; border-radius: 16px; padding: 12px 14px; margin-bottom: 14px; }
.bubble-mascot { font-size: 22px; line-height: 1.2; }
.advice-text { font-size: 12.5px; line-height: 1.8; color: #5A4739; white-space: pre-line; }

.sub-title { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 800; color: var(--ink); margin-bottom: 10px; }

.rec-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.rec-card { background: #FFFCF4; border: 2px solid #FFEBD0; border-radius: 14px; padding: 10px 12px; box-shadow: 0 3px 0 #FFF0D8; }
.rec-top { display: flex; align-items: center; gap: 6px; }
.rec-icon { width: 24px; height: 24px; border-radius: 8px; font-size: 12px; display: flex; align-items: center; justify-content: center; background: linear-gradient(160deg, #FFBE7A, #E8862B); }
.rec-name { font-size: 12.5px; font-weight: 800; color: var(--ink); }
.rec-tags { display: flex; gap: 5px; margin: 7px 0 5px; flex-wrap: wrap; }
.rec-line { font-size: 11.5px; color: var(--ink-soft); line-height: 1.6; }
.rec-line b { color: #B49B84; margin-right: 6px; font-size: 10.5px; }
.rec-reason { font-size: 11px; color: #A99584; line-height: 1.55; margin-top: 7px; padding-top: 7px; border-top: 1px dashed #FFE3BF; }

@media (max-width: 1100px) {
  .assist-body { grid-template-columns: 1fr; }
}
</style>
