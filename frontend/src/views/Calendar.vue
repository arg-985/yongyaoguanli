<template>
  <el-card>
    <FullCalendar ref="calendarRef" :options="calendarOptions" />

    <el-dialog v-model="markDialogVisible" title="标记已服" width="400px">
      <div style="margin-bottom: 12px;">
        <b>{{ pendingEvent?.title }}</b>
        <div style="color:#909399; font-size:13px">{{ pendingEvent?.startStr }}</div>
      </div>
      <el-form :model="markForm" label-width="80px">
        <el-form-item label="备注">
          <el-input v-model="markForm.notes" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="markDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="confirmMark">确认已服</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, shallowRef, reactive, onMounted } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { ElMessage } from 'element-plus'
import { reminderApi, recordApi } from '../api/modules'

const calendarRef = ref(null)
const events = shallowRef([])
const markDialogVisible = ref(false)
const submitting = ref(false)
const pendingEvent = ref(null)
// 必须用 reactive，否则 el-input 受控绑定无法回显输入
const markForm = reactive({ notes: '' })

const calendarOptions = {
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  headerToolbar: {
    left: 'today prev,next',
    center: 'title',
    right: 'dayGridMonth dayGridWeek timeGridDay'
  },
  locale: 'zh-cn',
  events: (fetchInfo, successCallback) => successCallback(events.value),
  eventClick: (info) => {
    if (info.event.extendedProps.status === 'PENDING') {
      pendingEvent.value = info.event
      markForm.notes = ''
      markDialogVisible.value = true
    }
  },
}

const statusColor = {
  PENDING: '#e6a23c',
  TAKEN: '#67c23a',
  LATE: '#f0c040',
  MISSED: '#f56c6c',
  SKIPPED: '#909399',
}

const load = async () => {
  try {
    const today = new Date()
    const start = new Date(today.getFullYear(), today.getMonth() - 1, 1).toISOString().slice(0, 10)
    const end = new Date(today.getFullYear(), today.getMonth() + 2, 0).toISOString().slice(0, 10)
    const data = await reminderApi.list({ start_date: start, end_date: end, page_size: 1000 })
    const rows = data.results || data || []
    events.value = rows.map(r => ({
      id: r.id,
      title: r.medication_name || r.medication || '服药提醒',
      start: r.scheduled_time,
      status: r.status,
      backgroundColor: statusColor[r.status] || '#409eff',
      borderColor: statusColor[r.status] || '#409eff',
    }))
    // 数据加载后强制刷新日历事件
    calendarRef.value?.getApi()?.refetchEvents()
  } catch (e) { /* ignore */ }
}

const confirmMark = async () => {
  submitting.value = true
  try {
    await recordApi.markTaken({
      reminder_id: pendingEvent.value.id,
      taken_time: new Date().toISOString(),
      notes: markForm.notes,
    })
    ElMessage.success('已标记')
    markDialogVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
