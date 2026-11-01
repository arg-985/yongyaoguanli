<template>
  <div class="safety-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">🛡️ 用药安全</span>
        <h1>吃药前，<em>先扫一遍</em>才安心</h1>
        <p>自动检查重复成分、相互作用与特殊人群禁忌</p>
      </div>
      <div class="hero-actions">
        <el-select
          v-if="auth.isAdmin"
          v-model="patient"
          filterable
          clearable
          placeholder="选择患者"
          style="width:180px"
          @change="load"
        >
          <el-option
            v-for="p in patients"
            :key="p.id"
            :label="p.real_name || p.username"
            :value="p.id"
          />
        </el-select>
        <el-button :loading="loading" @click="load">🔄 重新检测</el-button>
      </div>
    </div>

    <div class="candy-card tilt-pink">
      <div v-loading="loading" class="content">
        <div v-if="auth.isAdmin && !patient" class="placeholder">
          <div class="empty-illustration">🔍</div>
          <div class="empty-text">先选一个患者，药药帮你查一查</div>
        </div>

        <div v-else-if="errorMsg" class="placeholder">
          <div class="empty-illustration">😵</div>
          <div class="empty-text">{{ errorMsg }}</div>
        </div>

        <div v-else-if="findings.length > 0">
          <div class="verdict" :class="verdict.cls">
            <span class="verdict-emoji">{{ verdict.cls === 'danger' ? '🚨' : '💡' }}</span>
            <div>
              <div class="verdict-title">{{ verdict.title }}</div>
              <div class="verdict-sub">{{ verdict.sub }}</div>
            </div>
            <span class="verdict-tape"></span>
          </div>

          <div v-if="graphReady" class="graph-card">
            <div class="graph-title">
              <span class="jelly pink">🕸️</span>
              <div>
                <div class="t-main">风险关系图谱</div>
                <div class="t-sub">D3.js 力导向 · 节点越大涉及风险越多，可以拖拽</div>
              </div>
              <div class="graph-legend">
                <span><i class="dot" style="background:#FF7FA0"></i>高风险</span>
                <span><i class="dot" style="background:#FFD24A"></i>需关注</span>
                <span><i class="dot" style="background:#6FC3E8"></i>提示</span>
              </div>
            </div>
            <D3Network :findings="findings" :height="380" />
          </div>

          <div class="findings">
            <div v-for="(f, i) in findings" :key="i" class="finding-card" :class="f.level">
              <div class="finding-head">
                <span class="finding-index">{{ String(i + 1).padStart(2, '0') }}</span>
                <span class="finding-title">{{ f.title }}</span>
                <span class="pill" :class="levelPill(f.level)">{{ levelLabel(f.level) }}</span>
              </div>
              <div class="finding-detail">{{ f.detail }}</div>
              <div v-if="f.medications?.length" class="finding-meds">
                <span class="meds-label">涉及药品</span>
                <span v-for="m in f.medications" :key="m.id" class="med-chip">{{ m.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-safe">
          <div class="empty-illustration">🌿</div>
          <div class="empty-title">当前用药组合很安全</div>
          <div class="empty-sub">未发现重复成分或潜在冲突，请继续保持规范用药<br />如出现不适，记得及时就医</div>
          <span class="pill mint" style="margin-top:14px">✓ 已通过安全检测</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { clinicApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import D3Network from '../components/D3Network.vue'

const auth = useAuthStore()
const loading = ref(false)
const findings = ref([])
const errorMsg = ref('')
const patient = ref(null)
const patients = ref([])

const highCount = computed(() => findings.value.filter(f => f.level === 'high').length)

// 至少两种药才画得成图
const graphReady = computed(() => {
  const ids = new Set()
  findings.value.forEach(f => (f.medications || []).forEach(m => m?.id != null && ids.add(m.id)))
  return ids.size >= 2
})

const verdict = computed(() => {
  if (highCount.value > 0) {
    return {
      cls: 'danger',
      title: `检测到 ${highCount.value} 项用药风险`,
      sub: '存在重复成分或潜在冲突，请尽快与医生或药师确认后再服用'
    }
  }
  return {
    cls: 'warning',
    title: `检测到 ${findings.value.length} 项需关注事项`,
    sub: '未发现严重冲突，请留意下方提示并按时复查'
  }
})

const levelPill = (level) => ({ high: 'pink', medium: 'yellow', info: 'sky' }[level] || 'sky')
const levelLabel = (level) => ({ high: '高风险', medium: '需关注', info: '提示' }[level] || level)

const load = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = patient.value ? { patient_id: patient.value } : {}
    const data = await clinicApi.interactions(params)
    findings.value = data.findings || []
  } catch (e) {
    findings.value = []
    errorMsg.value = e?.response?.data?.detail || '检测失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (auth.isAdmin) {
    try {
      const data = await userApi.list({ role: 'patient', page_size: 200 })
      patients.value = (data.results || data || []).filter(u => u.role === 'patient')
      // 自动选中第一位患者，避免管理员进来一片空白
      if (patients.value.length) patient.value = patients.value[0].id
    } catch (e) {
      patients.value = []
    }
  }
  load()
})
</script>

<style scoped>
.safety-page { max-width: 1400px; }
.hero-actions { display: flex; gap: 10px; align-items: center; }

.content { min-height: 300px; }

.verdict {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 22px;
  border-radius: 20px;
  margin-bottom: 22px;
  border: 2px dashed;
  overflow: hidden;
}
.verdict.danger { background: #FFF0F2; border-color: #FFC2CB; }
.verdict.warning { background: #FFF8E1; border-color: #FFDC9E; }
.verdict-emoji { font-size: 30px; }
.verdict-title { font-size: 17px; font-weight: 800; color: #A83B48; }
.verdict.warning .verdict-title { color: #A97716; }
.verdict-sub { font-size: 12.5px; color: var(--ink-soft); margin-top: 4px; line-height: 1.6; }
.verdict-tape {
  position: absolute; right: 22px; top: -12px;
  width: 76px; height: 26px;
  background: repeating-linear-gradient(45deg, #FFD24A, #FFD24A 8px, #FFE58A 8px, #FFE58A 16px);
  opacity: .75;
  transform: rotate(6deg);
}

.findings { display: flex; flex-direction: column; gap: 12px; }
.finding-card {
  background: #FFFDF7;
  border: 2px solid #FFEBD0;
  border-radius: 18px;
  padding: 14px 18px;
  box-shadow: 0 4px 0 #FFF1DC;
}
.finding-card.high { border-color: #FFD1D9; background: #FFFBFB; }
.finding-card.medium { border-color: #FFE2AE; background: #FFFDF4; }
.finding-head { display: flex; align-items: center; gap: 10px; }
.finding-index {
  font-size: 12px; font-weight: 800; color: #fff;
  background: linear-gradient(160deg, #FFC078, #F0913B);
  border-radius: 8px; padding: 2px 8px;
}
.finding-title { font-size: 14px; font-weight: 800; color: var(--ink); flex: 1; }
.finding-detail { font-size: 12.5px; color: var(--ink-soft); line-height: 1.8; margin-top: 8px; }
.finding-meds { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.meds-label { font-size: 11px; color: var(--ink-faint); font-weight: 700; margin-right: 2px; }
.med-chip {
  font-size: 11.5px; font-weight: 700; color: #7A5CC0;
  background: var(--purple-soft); border-radius: 999px; padding: 2px 10px;
}

.graph-card {
  background: #FFFDF7;
  border: 2px solid #FFEBD0;
  border-radius: 18px;
  padding: 14px 18px;
  margin-bottom: 22px;
  box-shadow: 0 4px 0 #FFF1DC;
}
.graph-title { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }
.graph-title .t-main { font-size: 15px; font-weight: 800; color: var(--ink); }
.graph-title .t-sub { font-size: 11px; color: var(--ink-faint); }
.graph-legend { margin-left: auto; display: flex; gap: 12px; font-size: 11px; color: var(--ink-soft); font-weight: 700; }
.graph-legend .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 4px; }

.placeholder, .empty-safe { text-align: center; padding: 46px 0 40px; }
.empty-illustration { font-size: 46px; line-height: 1.2; }
.empty-text { font-size: 14px; color: var(--ink-soft); margin-top: 10px; }
.empty-title { font-size: 17px; font-weight: 800; color: var(--ink); margin-top: 12px; }
.empty-sub { font-size: 12.5px; color: var(--ink-faint); line-height: 1.9; margin-top: 8px; }
</style>
