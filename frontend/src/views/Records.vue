<template>
  <el-card>
    <template #header>
      <div class="filters">
        <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" />
        <el-select v-model="status" placeholder="状态" clearable style="width:140px">
          <el-option label="全部" value="" />
          <el-option label="已服" value="TAKEN" />
          <el-option label="迟服" value="LATE" />
          <el-option label="漏服" value="MISSED" />
          <el-option label="跳过" value="SKIPPED" />
          <el-option label="待服" value="PENDING" />
        </el-select>
        <el-select v-if="auth.isAdmin" v-model="patient" filterable clearable placeholder="患者" style="width:180px">
          <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="load">查询</el-button>
        <el-button :icon="Refresh" @click="reset">重置</el-button>
      </div>
    </template>

    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="6"><div class="stat mini taken">已服 <b>{{ summary.taken }}</b></div></el-col>
      <el-col :span="6"><div class="stat mini late">迟服 <b>{{ summary.late }}</b></div></el-col>
      <el-col :span="6"><div class="stat mini missed">漏服 <b>{{ summary.missed }}</b></div></el-col>
      <el-col :span="6"><div class="stat large">依从率 <b>{{ summary.rate }}%</b></div></el-col>
    </el-row>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column label="计划时间" width="170">
        <template #default="{ row }">{{ format(row.scheduled_time) }}</template>
      </el-table-column>
      <el-table-column prop="medication_name" label="药物" min-width="140" />
      <el-table-column label="实际时间" width="170">
        <template #default="{ row }">{{ row.taken_time ? format(row.taken_time) : '-' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="迟服分钟" width="100">
        <template #default="{ row }">{{ row.delay_minutes ?? '-' }}</template>
      </el-table-column>
      <el-table-column prop="notes" label="备注" min-width="140" />
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      style="margin-top:16px; justify-content:flex-end; display:flex"
      @size-change="load" @current-change="load"
    />
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { recordApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const dateRange = ref([])
const status = ref('')
const patient = ref(null)
const patients = ref([])

const summary = reactive({ taken: 0, late: 0, missed: 0, rate: 0 })

const statusLabel = (s) => ({ TAKEN: '已服', LATE: '迟服', MISSED: '漏服', SKIPPED: '跳过', PENDING: '待服' }[s] || s)
const statusTagType = (s) => ({ TAKEN: 'success', LATE: 'warning', MISSED: 'danger', SKIPPED: 'info', PENDING: '' }[s] || '')

const format = (v) => v ? String(v).replace('T', ' ').slice(0, 16) : '-'

const load = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    if (status.value) params.status = status.value
    if (patient.value) params.patient_id = patient.value
    const data = await recordApi.list(params)
    list.value = data.results || data || []
    total.value = data.count || data.length || 0
    calcSummary(list.value)
  } finally {
    loading.value = false
  }
}

const calcSummary = (rows) => {
  summary.taken = rows.filter(r => r.status === 'TAKEN').length
  summary.late = rows.filter(r => r.status === 'LATE').length
  summary.missed = rows.filter(r => r.status === 'MISSED').length
  const total = rows.filter(r => ['TAKEN', 'LATE', 'MISSED'].includes(r.status)).length
  summary.rate = total ? Math.round((summary.taken / total) * 100) : 0
}

const reset = () => { dateRange.value = []; status.value = ''; patient.value = null; page.value = 1; load() }

onMounted(async () => {
  if (auth.isAdmin) {
    const data = await userApi.list({ role: 'patient', page_size: 200 })
    patients.value = data.results || data || []
  }
  load()
})
</script>

<style scoped>
.filters { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.stat { color: #fff; border-radius: 6px; padding: 14px 18px; }
.stat.mini b { float: right; font-size: 20px; }
.stat.mini.taken { background: #67c23a; }
.stat.mini.late { background: #e6a23c; }
.stat.mini.missed { background: #f56c6c; }
.stat.large { background: linear-gradient(135deg, #409eff, #66b1ff); text-align: center; }
.stat.large b { font-size: 26px; }
</style>
