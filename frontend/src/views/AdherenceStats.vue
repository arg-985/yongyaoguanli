<template>
  <div class="stats-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">📊 依从率统计</span>
        <h1>你的健康，看得见</h1>
        <p>数据越透明，越容易坚持</p>
      </div>
      <div class="filters">
        <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始" end-placeholder="结束" size="large" />
        <el-select v-if="auth.isAdmin" v-model="patient" filterable clearable placeholder="患者" size="large" style="width:160px">
          <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
        <el-button type="primary" :icon="Search" :loading="loading" size="large" @click="load">查询</el-button>
      </div>
    </div>

    <el-row :gutter="18" class="stat-row">
      <el-col :xs="12" :md="6" style="display:flex">
        <div class="candy-card tilt-blue" style="flex:1">
          <div class="stat-num">{{ stats.total }}</div>
          <div class="stat-label">总应服</div>
          <span class="stat-emoji">📋</span>
        </div>
      </el-col>
      <el-col :xs="12" :md="6" style="display:flex">
        <div class="candy-card tilt-mint" style="flex:1">
          <div class="stat-num" style="color:var(--mint-deep)">{{ stats.onTime }}</div>
          <div class="stat-label">按时</div>
          <span class="stat-emoji">✅</span>
        </div>
      </el-col>
      <el-col :xs="12" :md="6" style="display:flex">
        <div class="candy-card tilt-yellow" style="flex:1">
          <div class="stat-num" style="color:#D39B1B">{{ stats.late }}</div>
          <div class="stat-label">迟服</div>
          <span class="stat-emoji">⏰</span>
        </div>
      </el-col>
      <el-col :xs="12" :md="6" style="display:flex">
        <div class="candy-card tilt-pink" style="flex:1">
          <div class="stat-num" style="color:var(--pink-deep)">{{ stats.missed }}</div>
          <div class="stat-label">漏服</div>
          <span class="stat-emoji">❌</span>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="18" class="chart-row">
      <el-col :xs="24" :lg="8" style="display:flex">
        <div class="candy-card tilt-pink" style="flex:1">
          <div class="card-title">
            <span class="jelly pink">🍩</span>
            <div class="t-main">状态占比</div>
            <span class="t-sub">Chart.js 甜甜圈</span>
          </div>
          <ChartDonut :data="donutData" :center-text="stats.rate + '%'" />
        </div>
      </el-col>
      <el-col :xs="24" :lg="8" style="display:flex">
        <div class="candy-card tilt-mint" style="flex:1">
          <div class="card-title">
            <span class="jelly mint">🕸️</span>
            <div class="t-main">健康维度雷达</div>
            <span class="t-sub">D3.js 多维度评分</span>
          </div>
          <D3Radar :data="radarData" :size="320" />
        </div>
      </el-col>
      <el-col :xs="24" :lg="8" style="display:flex">
        <div class="candy-card tilt-sky" style="flex:1">
          <div class="card-title">
            <span class="jelly sky">📈</span>
            <div class="t-main">依从率趋势</div>
            <span class="t-sub">ECharts 折线</span>
          </div>
          <VChart :option="lineOption" autoresize style="height: 340px;" />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="18" class="chart-row">
      <el-col :xs="24" style="display:flex">
        <div class="candy-card tilt-blue" style="flex:1">
          <div class="card-title">
            <span class="jelly sky">🗓️</span>
            <div class="t-main">服药热力图</div>
            <span class="t-sub">D3.js · 近 18 周打卡一览，颜色越深越棒</span>
          </div>
          <D3Heatmap :data="heatData" :weeks="18" />
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="18" class="chart-row">
      <el-col :xs="24" :lg="12" style="display:flex">
        <div class="candy-card tilt-yellow" style="flex:1">
          <div class="card-title">
            <span class="jelly yellow">🗓️</span>
            <div class="t-main">漏服分布（按星期）</div>
            <span class="t-sub">哪几天最容易忘</span>
          </div>
          <VChart :option="barOption" autoresize style="height: 300px;" />
        </div>
      </el-col>
      <el-col :xs="24" :lg="12" style="display:flex">
        <div class="candy-card tilt-orange" style="flex:1">
          <div class="card-title">
            <span class="jelly orange">💊</span>
            <div class="t-main">药品完成率 TOP 5</div>
            <span class="t-sub">你最听话吃的是…</span>
          </div>
          <VChart :option="barHoriOption" autoresize style="height: 300px;" />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { recordApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import VChart from 'vue-echarts'
import D3Radar from '../components/D3Radar.vue'
import D3Heatmap from '../components/D3Heatmap.vue'
import ChartDonut from '../components/ChartDonut.vue'

const auth = useAuthStore()
const loading = ref(false)
const dateRange = ref([])
const patient = ref(null)
const patients = ref([])
const data = reactive({ daily: [], byWeekday: [], byMedication: [], summary: {} })
const heatData = ref([])

const stats = computed(() => {
  const s = data.summary || {}
  return {
    total: s.total || 0,
    onTime: s.on_time || 0,
    late: s.late || 0,
    missed: s.missed || 0,
    rate: s.adherence_rate != null ? Number(s.adherence_rate.toFixed(1)) : 0,
  }
})

const donutData = computed(() => [
  { label: '按时', value: stats.value.onTime },
  { label: '迟服', value: stats.value.late },
  { label: '漏服', value: stats.value.missed },
  { label: '跳过', value: data.summary?.skipped || 0 },
])

const radarData = computed(() => [
  { axis: '按时率', value: stats.value.rate },
  { axis: '完整性', value: stats.value.total ? Math.round((stats.value.onTime / stats.value.total) * 100) : 0 },
  { axis: '规律性', value: stats.value.total ? Math.round(((stats.value.onTime + stats.value.late * 0.5) / stats.value.total) * 100) : 0 },
  { axis: '无漏服', value: 100 - (stats.value.total ? Math.round((stats.value.missed / stats.value.total) * 100) : 0) },
  { axis: '连续性', value: Math.max(0, 100 - stats.value.missed * 8) },
  { axis: '准时性', value: stats.value.total ? Math.round((stats.value.onTime / stats.value.total) * 100) : 0 },
])

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,253,247,0.98)', borderColor: '#FFE6A8', textStyle: { color: '#4A3B32' } },
  legend: { data: ['依从率', '服药次数'], textStyle: { color: '#5A4739' } },
  grid: { top: 50, right: 50, bottom: 30, left: 50 },
  xAxis: { type: 'category', data: data.daily.map(d => d.date?.slice(5) || ''), axisLine: { lineStyle: { color: '#FFD9A8' } }, axisLabel: { color: '#8A7466' } },
  yAxis: [
    { type: 'value', min: 0, max: 100, name: '%', axisLabel: { formatter: '{value}%', color: '#8A7466' }, splitLine: { lineStyle: { color: '#FFF0D8' } } },
    { type: 'value', name: '次', axisLabel: { color: '#8A7466' }, splitLine: { show: false } }
  ],
  series: [
    { name: '依从率', type: 'line', smooth: true, symbolSize: 8, data: data.daily.map(d => d.adherence_rate != null ? Number(d.adherence_rate.toFixed(1)) : 0), itemStyle: { color: '#FF7FA0' }, lineStyle: { width: 3, color: '#FF7FA0' }, areaStyle: { color: 'rgba(255,127,160,.15)' } },
    { name: '服药次数', type: 'bar', yAxisIndex: 1, barWidth: 14, data: data.daily.map(d => d.total || 0), itemStyle: { color: '#FFD24A', borderRadius: [6, 6, 0, 0] } }
  ]
}))

const barOption = computed(() => {
  const names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const arr = new Array(7).fill(0)
  for (const x of data.byWeekday || []) {
    if (x.weekday >= 1 && x.weekday <= 7) arr[x.weekday - 1] = x.count || x.missed || 0
  }
  return {
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,253,247,0.98)', borderColor: '#FFE6A8', textStyle: { color: '#4A3B32' } },
    grid: { top: 30, right: 20, bottom: 30, left: 40 },
    xAxis: { type: 'category', data: names, axisLine: { lineStyle: { color: '#FFD9A8' } }, axisLabel: { color: '#8A7466' } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#FFF0D8' } }, axisLabel: { color: '#8A7466' } },
    series: [{ type: 'bar', barWidth: 24, data: arr, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#FF9DB4' }, { offset: 1, color: '#FF7FA0' }] }, borderRadius: [10, 10, 0, 0] } }]
  }
})

const barHoriOption = computed(() => {
  const meds = (data.byMedication || []).slice(0, 5)
  const labels = meds.map(m => m.medication_name || m.name || '未知')
  const values = meds.map(m => m.completed || m.count || 0)
  return {
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,253,247,0.98)', borderColor: '#FFE6A8', textStyle: { color: '#4A3B32' } },
    grid: { top: 20, right: 40, bottom: 30, left: 100 },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#FFF0D8' } }, axisLabel: { color: '#8A7466' } },
    yAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: '#FFD9A8' } }, axisLabel: { color: '#5A4739', fontWeight: 700 } },
    series: [{ type: 'bar', barWidth: 18, data: values, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#FFE07A' }, { offset: 1, color: '#FF9F6B' }] }, borderRadius: [0, 10, 10, 0] } }]
  }
})

const load = async () => {
  loading.value = true
  try {
    const params = {}
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    } else {
      params.days = 30
    }
    if (patient.value) params.patient_id = patient.value
    const res = await recordApi.stats(params)
    Object.assign(data, { daily: res.daily || [], byWeekday: res.by_weekday || [], byMedication: res.by_medication || [], summary: res || {} })
    // 热力图固定看近 18 周
    const heatParams = { days: 126 }
    if (patient.value) heatParams.patient_id = patient.value
    const heat = await recordApi.stats(heatParams)
    heatData.value = (heat.daily || []).map(d => ({
      date: d.date,
      rate: d.adherence_rate != null ? Number(d.adherence_rate.toFixed(1)) : 0,
      total: d.total || 0
    }))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (auth.isAdmin) {
    const d = await userApi.list({ role: 'patient', page_size: 200 })
    patients.value = d.results || d || []
  }
  load()
})
</script>

<style scoped>
.stats-page { max-width: 1500px; }
.stat-row { margin-bottom: 18px; }
.chart-row { margin-bottom: 18px; }

.stat-num { font-size: 30px; font-weight: 800; color: var(--ink); line-height: 1; }
.stat-label { font-size: 12px; color: var(--ink-faint); margin-top: 6px; font-weight: 700; }
.stat-emoji { font-size: 20px; }

.card-title { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.t-main { font-size: 15px; font-weight: 800; color: var(--ink); }
.t-sub { font-size: 11px; color: var(--ink-faint); margin-left: 4px; }
</style>
