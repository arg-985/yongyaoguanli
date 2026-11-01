<template>
  <div class="sprite-root" :class="{ running }">
    <!-- AI 完成后的提示气泡 -->
    <transition name="pop">
      <div v-if="toast" class="sprite-toast">
        <div class="toast-title">{{ toast.title }}</div>
        <div class="toast-text">{{ toast.text }}</div>
        <button class="toast-close" @click="toast = null">×</button>
      </div>
    </transition>

    <!-- 鼠标碰一下打招呼 -->
    <transition name="pop">
      <div v-if="greeting && !open" class="greet-bubble">你好主人！🐾</div>
    </transition>

    <!-- 对话面板 -->
    <transition name="pop">
      <div v-if="open" class="sprite-panel">
        <div class="panel-head">
          <div class="panel-title">
            <span class="tiny-mascot">🐶</span>
            <div>
              <div class="name">小狗管家 · 药药</div>
              <div class="sub">点我对话，或者去首页选症状</div>
            </div>
          </div>
          <span class="pill" :class="llm.enabled ? 'mint' : 'yellow'">
            {{ llm.enabled ? 'AI 增强' : '规则引擎' }}
          </span>
        </div>

        <div class="panel-body">
          <div v-if="auth.isAdmin" class="patient-row">
            <span class="row-label">为谁咨询</span>
            <el-select v-model="patientId" size="small" placeholder="选择患者" style="flex:1">
              <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
            </el-select>
          </div>

          <div class="quick-title">点一下症状</div>
          <div class="quick-grid">
            <button
              v-for="s in symptomOptions"
              :key="s.code"
              class="quick-chip"
              :class="{ on: picked.includes(s.code) }"
              @click="toggle(s.code)"
            >
              {{ s.name }}
            </button>
          </div>

          <div class="ask-row">
            <el-input
              v-model="text"
              size="small"
              placeholder="也可以直接说，比如「嗓子疼还发烧」"
              @keyup.enter="ask"
            />
            <el-button type="primary" size="small" :loading="loading" @click="ask">问它</el-button>
          </div>

          <div v-if="answer" class="answer-box">
            <div class="answer-head">
              <span class="pill pink">{{ answer.source === 'llm' ? 'AI 建议' : '规则建议' }}</span>
            </div>
            <div class="answer-text">{{ answer.advice }}</div>
            <div v-if="recs.length" class="answer-recs">
              <div v-for="r in recs" :key="r.medication_id" class="rec-item">
                <span class="rec-name">{{ r.name }}</span>
                <span class="rec-dose">{{ r.dosage || r.specification || '' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 小狗本体：真实图片 + 自由漂浮 -->
    <button
      class="sprite-btn"
      :class="{ open }"
      title="小狗管家"
      @mouseenter="onHover"
      @click="togglePanel"
    >
      <img src="/assets/dog-sprite.png" alt="小狗管家" class="sprite-img" draggable="false" />
      <span class="sparkle s1">✦</span>
      <span class="sparkle s2">✧</span>
      <span class="sparkle s3">✦</span>
      <span v-if="loading" class="thinking"><i></i><i></i><i></i></span>
    </button>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { clinicApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const open = ref(false)
const loading = ref(false)
const running = ref(false)
const answer = ref(null)
const toast = ref(null)
const greeting = ref(false)
const text = ref('')
const picked = ref([])
const symptomOptions = ref([])
const patients = ref([])
const patientId = ref(null)
const llm = reactive({ enabled: false, model: '' })

let runTimer = null
let toastTimer = null
let greetTimer = null

const recs = computed(() => (answer.value?.recommendations || []).slice(0, 2))

const toggle = (code) => {
  picked.value = picked.value.includes(code)
    ? picked.value.filter(c => c !== code)
    : [...picked.value, code]
}

const togglePanel = () => {
  open.value = !open.value
  greeting.value = false
  if (open.value) toast.value = null
}

/** 鼠标碰一下：小狗说「你好主人」 */
const onHover = () => {
  if (open.value) return
  greeting.value = true
  clearTimeout(greetTimer)
  greetTimer = setTimeout(() => { greeting.value = false }, 2400)
}

/** 跑动庆祝 */
const run = () => {
  running.value = false
  setTimeout(() => {
    running.value = true
    clearTimeout(runTimer)
    runTimer = setTimeout(() => { running.value = false }, 4500)
  }, 20)
}

const showToast = (title, body) => {
  toast.value = { title, text: body }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = null }, 14000)
}

const ask = async () => {
  if (auth.isAdmin && !patientId.value) {
    ElMessage.warning('请先选择要咨询的患者')
    return
  }
  if (!picked.value.length && !text.value.trim()) {
    ElMessage.warning('选个症状，或者跟我说说哪里不舒服')
    return
  }
  loading.value = true
  try {
    const payload = {
      symptoms: picked.value,
      duration_days: 3,
      severity: 2,
      free_text: text.value.trim()
    }
    if (patientId.value) payload.patient_id = patientId.value
    const res = await clinicApi.consult(payload)
    answer.value = res
    text.value = ''
    open.value = false
    run()
    showToast('分析完成啦！', (res.recommendations?.[0]?.name
      ? `推荐试试 ${res.recommendations[0].name}`
      : '暂时没有匹配到合适的药，看看建议吧'))
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '小狗暂时开小差了，稍后再试')
  } finally {
    loading.value = false
  }
}

/** 首页生成建议后：庆祝 */
const onCelebrate = (e) => {
  const detail = e.detail || {}
  if (detail.raw) answer.value = detail.raw
  open.value = false
  run()
  showToast(
    detail.title || '建议生成好啦！',
    detail.text || (detail.raw?.recommendations?.[0]?.name
      ? `推荐试试 ${detail.raw.recommendations[0].name}`
      : '点我看看完整建议～')
  )
}

onMounted(async () => {
  window.addEventListener('sprite:celebrate', onCelebrate)
  try {
    const [symptomData, llmData] = await Promise.all([
      clinicApi.symptoms(),
      clinicApi.llmStatus()
    ])
    symptomOptions.value = (symptomData.results || symptomData || []).slice(0, 8)
    llm.enabled = !!llmData?.enabled
    llm.model = llmData?.model || ''
  } catch (e) {
    symptomOptions.value = []
  }
  if (auth.isAdmin) {
    try {
      const data = await userApi.list({ role: 'patient', page_size: 200 })
      patients.value = data.results || data || []
      patientId.value = patients.value[0]?.id ?? null
    } catch (e) {
      patients.value = []
    }
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('sprite:celebrate', onCelebrate)
  clearTimeout(runTimer)
  clearTimeout(toastTimer)
  clearTimeout(greetTimer)
})
</script>

<style scoped>
.sprite-root {
  position: fixed;
  right: 32px;
  bottom: 28px;
  z-index: 2100;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 14px;
}

/* 打招呼气泡 */
.greet-bubble {
  position: relative;
  background: #FFFDF7;
  border: 2px solid #FFE6A8;
  border-radius: 18px;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 800;
  color: var(--pink-deep);
  box-shadow: 0 6px 16px rgba(201, 155, 92, .22);
  white-space: nowrap;
}
.greet-bubble::after {
  content: '';
  position: absolute;
  right: 30px;
  bottom: -9px;
  width: 16px;
  height: 16px;
  background: #FFFDF7;
  border-right: 2px solid #FFE6A8;
  border-bottom: 2px solid #FFE6A8;
  transform: rotate(45deg);
  border-bottom-right-radius: 4px;
}

/* ---------- 小狗本体 ---------- */
.sprite-btn {
  position: relative;
  width: 120px;
  height: 120px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  outline: none;
  filter: drop-shadow(0 12px 20px rgba(214, 160, 90, .35));
  /* 自由漂浮：复合动画实现随意漂 */
  animation: float-free 7s ease-in-out infinite;
}
.sprite-btn.open { animation-play-state: paused; }
.sprite-btn:active .sprite-img { transform: scale(.94); }

.sprite-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 50%;
  transition: transform .2s ease;
  pointer-events: none;
  user-select: none;
}
.sprite-btn.open .sprite-img { transform: scale(1.05); }

/* 自由漂浮：走一个不规则的 8 字轨迹 */
@keyframes float-free {
  0%   { transform: translate(0, 0) rotate(-3deg); }
  25%  { transform: translate(-10px, -14px) rotate(2deg); }
  38%  { transform: translate(6px, -22px) rotate(-1deg); }
  52%  { transform: translate(14px, -6px) rotate(4deg); }
  65%  { transform: translate(4px, 8px) rotate(-2deg); }
  78%  { transform: translate(-12px, 6px) rotate(3deg); }
  90%  { transform: translate(-4px, -6px) rotate(-1deg); }
  100% { transform: translate(0, 0) rotate(-3deg); }
}

/* 跑动庆祝（AI 出结果后触发）：向右跑一圈再回来 */
.sprite-root.running .sprite-btn {
  animation: dash-around 4.5s cubic-bezier(.42, 0, .58, 1) both;
}
.sprite-root.running .sprite-img { animation: wiggle .22s ease-in-out infinite alternate; }
.sprite-root.running::before {
  content: '';
  position: absolute;
  right: 70px;
  bottom: 14px;
  width: 120px;
  height: 6px;
  border-radius: 999px;
  background: repeating-linear-gradient(90deg, #FFD24A 0 10px, transparent 10px 20px);
  opacity: .8;
  animation: trail-dash .3s linear infinite;
}
.sprite-root.running::after {
  content: '💨';
  position: absolute;
  right: 136px;
  bottom: 20px;
  font-size: 20px;
  opacity: .8;
  animation: puff .4s ease-in-out infinite alternate;
}

@keyframes dash-around {
  0%   { transform: translate(0, 0) rotate(0deg); }
  15%  { transform: translate(40px, -28px) rotate(-12deg); }
  35%  { transform: translate(180px, -8px) rotate(10deg); }
  55%  { transform: translate(60px, -36px) rotate(-8deg); }
  75%  { transform: translate(-20px, -12px) rotate(6deg); }
  100% { transform: translate(0, 0) rotate(0deg); }
}
@keyframes wiggle { from { transform: rotate(-4deg); } to { transform: rotate(4deg); } }
@keyframes trail-dash { from { transform: translateX(0); } to { transform: translateX(-20px); } }
@keyframes puff { from { opacity: .6; transform: scale(.9); } to { opacity: 1; transform: scale(1.15); } }

.sparkle {
  position: absolute;
  font-size: 14px;
  color: #FFD24A;
  animation: twinkle 2.2s ease-in-out infinite;
  pointer-events: none;
}
.sparkle.s1 { top: -4px; left: 2px; }
.sparkle.s2 { top: 12px; right: -2px; color: #FF9DB4; animation-delay: .6s; }
.sparkle.s3 { bottom: 0; left: -6px; color: #8FE3C4; animation-delay: 1.1s; }
@keyframes twinkle { 0%,100% { opacity: .35; transform: scale(.8); } 50% { opacity: 1; transform: scale(1.15); } }

.thinking {
  position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 4px; background: #fff; border-radius: 999px; padding: 5px 10px;
  box-shadow: 0 4px 10px rgba(201,155,92,.25);
}
.thinking i { width: 5px; height: 5px; border-radius: 50%; background: var(--pink); animation: dot 1s ease-in-out infinite; }
.thinking i:nth-child(2) { animation-delay: .15s; }
.thinking i:nth-child(3) { animation-delay: .3s; }
@keyframes dot { 0%,100% { transform: translateY(0); opacity: .5; } 50% { transform: translateY(-4px); opacity: 1; } }

/* ---------- 完成后气泡 ---------- */
.sprite-toast {
  position: relative;
  width: 260px;
  background: #FFFDF7;
  border: 2px solid #FFD3DF;
  border-radius: 20px;
  padding: 14px 16px 14px;
  box-shadow: 0 12px 26px rgba(201, 155, 92, .22);
}
.sprite-toast::after {
  content: '';
  position: absolute;
  right: 26px;
  bottom: -10px;
  width: 16px; height: 16px;
  background: #FFFDF7;
  border-right: 2px solid #FFD3DF;
  border-bottom: 2px solid #FFD3DF;
  transform: rotate(45deg);
  border-bottom-right-radius: 4px;
}
.toast-title { font-size: 14px; font-weight: 800; color: var(--pink-deep); margin-bottom: 4px; }
.toast-text { font-size: 13px; line-height: 1.6; color: var(--ink-soft); }
.toast-close {
  position: absolute; right: 8px; top: 6px; border: none; background: transparent;
  color: #C9B49F; font-size: 16px; cursor: pointer; line-height: 1;
}

/* ---------- 对话面板 ---------- */
.sprite-panel {
  width: 340px;
  max-height: 72vh;
  overflow-y: auto;
  background: #FFFDF7;
  border: 2px solid #FFE2B8;
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(201, 155, 92, .26);
}
.panel-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px 12px;
  background: linear-gradient(135deg, #FFF3D6, #FFE8EF);
  border-bottom: 2px dashed #FFE2B8;
  border-radius: 22px 22px 0 0;
}
.panel-title { display: flex; align-items: center; gap: 10px; }
.tiny-mascot {
  width: 34px; height: 34px; border-radius: 12px; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(160deg, #FF9DB4, #E85C80);
  box-shadow: inset 0 -4px 0 rgba(0,0,0,.1);
}
.panel-title .name { font-size: 14px; font-weight: 800; color: var(--ink); }
.panel-title .sub { font-size: 11px; color: var(--ink-faint); }

.panel-body { padding: 14px 16px 16px; }
.patient-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.row-label { font-size: 12px; color: var(--ink-soft); font-weight: 700; white-space: nowrap; }

.quick-title { font-size: 12px; font-weight: 800; color: var(--ink-soft); margin-bottom: 8px; }
.quick-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }
.quick-chip {
  border: 2px solid #FFE6A8;
  background: #FFFCF0;
  border-radius: 12px;
  padding: 8px 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--ink);
  cursor: pointer;
  box-shadow: 0 3px 0 #FFE3A1;
  transition: transform .15s ease, background .15s ease;
}
.quick-chip:hover { transform: translateY(-2px); }
.quick-chip.on { background: #FFF1F5; border-color: var(--pink); color: var(--pink-deep); box-shadow: 0 3px 0 var(--pink-deep); }

.ask-row { display: flex; gap: 8px; align-items: center; }

.answer-box { margin-top: 14px; background: #F7FBF8; border: 2px dashed #CBEBDD; border-radius: 16px; padding: 12px 14px; }
.answer-head { margin-bottom: 8px; }
.answer-text { font-size: 13px; line-height: 1.75; color: #4A5C52; white-space: pre-line; }
.answer-recs { margin-top: 10px; display: flex; flex-direction: column; gap: 6px; }
.rec-item {
  display: flex; justify-content: space-between; gap: 8px; align-items: baseline;
  background: #fff; border-radius: 10px; padding: 6px 10px; border: 1px solid #E2F1EA;
}
.rec-name { font-size: 12px; font-weight: 800; color: var(--mint-deep); }
.rec-dose { font-size: 11px; color: var(--ink-faint); }

.pop-enter-active, .pop-leave-active { transition: transform .22s ease, opacity .22s ease; transform-origin: bottom right; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: translateY(12px) scale(.94); }

@media (max-width: 640px) {
  .sprite-btn { width: 100px; height: 100px; }
  .sprite-root { right: 16px; bottom: 16px; }
  .sprite-panel { width: calc(100vw - 32px); }
}
</style>
