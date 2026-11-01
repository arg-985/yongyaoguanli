<template>
  <div class="pa-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">📝 预约挂号</span>
        <h1>在线挂号，<em>缴费</em>一目了然</h1>
        <p>只能查看与取消自己的预约，其他患者信息均不可见</p>
      </div>
      <el-button type="primary" size="large" round :disabled="!bookingOpen" @click="openBooking">在线预约挂号</el-button>
    </div>

    <el-alert
      v-if="!bookingOpen"
      type="warning"
      :closable="false"
      show-icon
      title="网上预约挂号功能已被管理员关闭，请到院现场挂号"
      style="margin-bottom:4px"
    />

    <div class="candy-card tilt-pink">
      <div class="card-head">
        <span class="t-main">📅 我的预约</span>
        <span class="pill pink">{{ appointments.length }} 条记录</span>
      </div>
      <el-table :data="appointments" v-loading="loading" stripe>
        <el-table-column label="就诊日期" width="120">
          <template #default="{ row }">{{ row.visit_date }}</template>
        </el-table-column>
        <el-table-column prop="time_slot" label="时段" width="140" />
        <el-table-column prop="department_name" label="科室" width="110" />
        <el-table-column prop="doctor_name" label="医生" width="110" />
        <el-table-column label="挂号费" width="100">
          <template #default="{ row }">¥{{ row.fee }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'BOOKED'" link type="danger" @click="cancel(row)">取消预约</el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !appointments.length" description="还没有预约记录" :image-size="80" />
    </div>

    <div class="candy-card tilt-sky">
      <div class="card-head">
        <span class="t-main">💰 我的费用</span>
        <span class="pill yellow">待缴 {{ unpaid.length }} 笔 · 合计 ¥{{ unpaidTotal }}</span>
      </div>
      <el-table :data="payments" v-loading="loading" stripe>
        <el-table-column prop="kind_display" label="类型" width="100" />
        <el-table-column prop="title" label="费用说明" min-width="220" />
        <el-table-column label="金额" width="110">
          <template #default="{ row }"><span class="amount">¥{{ row.amount }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'PAID' ? 'success' : 'warning'" size="small">{{ row.status_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ fmt(row.paid_at || row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'UNPAID'" link type="primary" @click="pay(row)">缴费</el-button>
            <span v-else class="muted">已缴</span>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !payments.length" description="没有待缴费单据" :image-size="80" />
    </div>

    <el-dialog v-model="bookingDialog" title="在线预约挂号" width="520px" top="6vh" class="booking-dialog">
      <el-form label-width="84px" class="book-form" style="max-height:56vh;overflow-y:auto;padding-right:6px">
        <el-form-item label="科室">
          <el-radio-group v-model="form.department" @change="onDepartment">
            <el-radio-button v-for="d in openDepartments" :key="d.id" :label="d.id">{{ d.name }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="就诊日期">
          <div style="width:100%">
            <el-date-picker v-model="form.visit_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" style="width:100%" :disabled-date="disabledDate" @change="onDate" />
            <div class="date-quick">
              <el-button v-for="q in quickDates" :key="q.value" size="small" round :type="form.visit_date === q.value ? 'primary' : 'default'" @click="pickDate(q.value)">{{ q.label }}</el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="医生">
          <el-radio-group v-model="form.doctor" @change="onDoctor">
            <el-radio v-for="doc in departmentDoctors" :key="doc.id" :label="doc.id">
              {{ doc.real_name }} {{ doc.title ? '· ' + doc.title : '' }}
            </el-radio>
          </el-radio-group>
          <span v-if="form.department && !departmentDoctors.length" class="form-hint">该科室暂无医生</span>
        </el-form-item>
        <el-form-item label="就诊时段">
          <el-radio-group v-model="form.time_slot">
            <el-radio-button v-for="s in doctorSchedules" :key="s.id" :label="slotLabel(s)">{{ slotLabel(s) }}</el-radio-button>
            <el-radio-button v-if="form.doctor && !doctorSchedules.length" label="普通号 全天">普通号 全天</el-radio-button>
          </el-radio-group>
          <span v-if="form.doctor && form.visit_date && !doctorSchedules.length" class="form-hint">该医生当天无排班，可挂普通号</span>
        </el-form-item>
      </el-form>
      <div class="book-tip">挂号费 ¥10，预约成功后自动生成挂号费待缴单</div>
      <template #footer>
        <el-button @click="bookingDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!canBook" @click="submitBooking">确认挂号</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workflowApi } from '../api/modules'

const loading = ref(false)
const appointments = ref([])
const payments = ref([])
const departments = ref([])
const doctors = ref([])
const schedules = ref([])
const toggles = ref([])

const bookingDialog = ref(false)
const form = reactive({ department: null, doctor: null, time_slot: '', visit_date: '' })

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 16) : '—')
const statusTag = (s) => ({ BOOKED: 'success', CANCELLED: 'info', DONE: 'primary' }[s] || '')

const bookingOpen = computed(() => {
  const t = toggles.value.find((x) => x.key === 'online_appointment')
  return t ? t.enabled : true
})
const openDepartments = computed(() => departments.value.filter((d) => d.is_open))
const departmentDoctors = computed(() => doctors.value.filter((d) => !form.department || d.department === (departments.value.find((x) => x.id === form.department)?.name || '')))
const selectedWeekday = computed(() => {
  if (!form.visit_date) return null
  const d = new Date(`${form.visit_date}T00:00:00`)
  return Number.isNaN(d.getTime()) ? null : d.getDay()
})
const doctorSchedules = computed(() =>
  schedules.value.filter((s) => s.doctor === form.doctor && (selectedWeekday.value === null || s.weekday === selectedWeekday.value))
)
const unpaid = computed(() => payments.value.filter((p) => p.status === 'UNPAID'))
const unpaidTotal = computed(() => unpaid.value.reduce((s, p) => s + Number(p.amount || 0), 0).toFixed(2))
const canBook = computed(() => form.doctor && form.time_slot && form.visit_date)

const toDateStr = (d) => {
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}
const quickDates = computed(() => {
  const names = ['今天', '明天', '后天']
  return names.map((label, i) => {
    const d = new Date()
    d.setDate(d.getDate() + i)
    return { label, value: toDateStr(d) }
  })
})

const slotLabel = (s) => ({ AM: '上午', PM: '下午', NIGHT: '夜班' }[s.period] || s.period) + (s.room ? ` · ${s.room}` : '')

const disabledDate = (d) => d < new Date(new Date().toDateString())

const load = async () => {
  loading.value = true
  try {
    const [ap, pay] = await Promise.all([
      workflowApi.appointments({ page_size: 100 }),
      workflowApi.payments({ page_size: 100 }),
    ])
    appointments.value = listOf(ap)
    payments.value = listOf(pay)
  } finally {
    loading.value = false
  }
}

const loadBase = async () => {
  const [dept, docs, sch, tg] = await Promise.all([
    workflowApi.departments(),
    workflowApi.doctors(),
    workflowApi.schedules({}),
    workflowApi.toggles(),
  ])
  departments.value = listOf(dept)
  doctors.value = listOf(docs)
  schedules.value = listOf(sch)
  toggles.value = listOf(tg)
}

const openBooking = () => {
  form.department = openDepartments.value[0]?.id ?? null
  form.doctor = null
  form.time_slot = ''
  form.visit_date = quickDates.value[0].value
  bookingDialog.value = true
}

const pickDate = (v) => {
  form.visit_date = v
  onDate()
}

const onDepartment = () => { form.doctor = null; form.time_slot = '' }
const onDoctor = () => { form.time_slot = '' }
const onDate = () => {
  const still = doctorSchedules.value.some((s) => slotLabel(s) === form.time_slot)
  if (!still) form.time_slot = ''
}

const submitBooking = async () => {
  await workflowApi.appointmentCreate({ ...form })
  bookingDialog.value = false
  ElMessage.success('挂号成功，请及时缴纳挂号费')
  await load()
}

const cancel = async (row) => {
  try {
    await ElMessageBox.confirm(`确认取消 ${row.visit_date} ${row.time_slot} 的预约？`, '取消预约', { type: 'warning' })
  } catch (e) { return }
  await workflowApi.appointmentCancel(row.id)
  ElMessage.success('预约已取消')
  await load()
}

const pay = async (row) => {
  await workflowApi.pay(row.id)
  ElMessage.success(`已支付 ${row.title} ¥${row.amount}`)
  await load()
}

onMounted(async () => {
  await Promise.all([load(), loadBase()])
})
</script>

<style scoped>
.pa-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.t-main { font-size: 15px; font-weight: 800; color: var(--ink); }
.amount { font-weight: 900; color: var(--orange-deep); }
.muted { color: var(--ink-faint); font-size: 12px; }
.book-tip { font-size: 12px; color: var(--ink-faint); padding: 4px 0 0 84px; }
.form-hint { font-size: 12px; color: var(--ink-faint); margin-left: 8px; }
.date-quick { display: flex; gap: 8px; margin-top: 8px; }
</style>
