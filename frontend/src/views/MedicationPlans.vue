<template>
  <el-card>
    <template #header>
      <div class="header-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索药物名称"
          clearable
          style="width: 260px"
          :prefix-icon="Search"
          @clear="load"
          @keyup.enter="load"
        />
        <el-button type="primary" :icon="Plus" @click="openDialog()">新建计划</el-button>
      </div>
    </template>

    <el-table :data="list" border stripe v-loading="loading">
      <el-table-column prop="medication_name" label="药物" min-width="140">
        <template #default="{ row }">{{ row.medication_name || row.medication }}</template>
      </el-table-column>
      <el-table-column prop="specification" label="规格" width="120" />
      <el-table-column prop="dosage_per_time" label="每次剂量" width="100" />
      <el-table-column label="频率" width="100">
        <template #default="{ row }">{{ freqLabel(row.frequency) }}</template>
      </el-table-column>
      <el-table-column label="时间点" min-width="160">
        <template #default="{ row }">
          <span v-if="Array.isArray(row.time_points)">{{ row.time_points.join(', ') }}</span>
          <span v-else>{{ row.time_points || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始日期" width="120" />
      <el-table-column prop="end_date" label="结束日期" width="120" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openDialog(row)">编辑</el-button>
          <el-popconfirm title="确认删除?" @confirm="onRemove(row.id)">
            <template #reference>
              <el-button link type="danger" size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
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

  <!-- 新建/编辑对话框 -->
  <el-dialog v-model="dialogVisible" :title="form.id ? '编辑用药计划' : '新建用药计划'" width="560px">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item v-if="auth.isAdmin" label="患者" prop="patient">
        <el-select v-model="form.patient" filterable style="width:100%">
          <el-option v-for="u in patientOptions" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="药物" prop="medication">
        <el-select v-model="form.medication" filterable placeholder="选择药物" style="width:100%">
          <el-option v-for="m in medicationOptions" :key="m.id" :label="`${m.name} (${m.specification || '-'})`" :value="m.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="每次剂量" prop="dosage_per_time">
        <el-input v-model="form.dosage_per_time" placeholder="如 1 片 / 5 mg" />
      </el-form-item>
      <el-form-item label="频率" prop="frequency">
        <el-select v-model="form.frequency" style="width:100%">
          <el-option label="每日一次 DAILY" value="DAILY" />
          <el-option label="每日两次 BID" value="BID" />
          <el-option label="每日三次 TID" value="TID" />
          <el-option label="每日四次 QID" value="QID" />
          <el-option label="自定义 CUSTOM" value="CUSTOM" />
        </el-select>
      </el-form-item>
      <el-form-item label="时间点" prop="time_points">
        <div v-if="form.frequency === 'CUSTOM'" class="dynamic-times">
          <el-tag
            v-for="(t, i) in customTimes"
            :key="i"
            closable
            @close="customTimes.splice(i, 1)"
            style="margin:4px"
          >{{ t }}</el-tag>
          <el-input
            v-if="customTimes.length < 10"
            v-model="newTimePoint"
            placeholder="HH:MM"
            size="small"
            style="width:100px"
            @keyup.enter="addTimePoint"
          >
            <template #append><el-button @click="addTimePoint">+</el-button></template>
          </el-input>
        </div>
        <span v-else>{{ defaultTimePoints }}</span>
      </el-form-item>
      <el-form-item label="开始日期">
        <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
      </el-form-item>
      <el-form-item label="结束日期">
        <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
      </el-form-item>
      <el-form-item label="状态">
        <el-switch v-model="form.status" active-value="active" inactive-value="inactive" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.notes" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { planApi, medicationApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const dialogVisible = ref(false)
const formRef = ref()
const medicationOptions = ref([])
const patientOptions = ref([])
const customTimes = ref([])
const newTimePoint = ref('')

const emptyForm = () => ({
  id: null, patient: null, medication: null, dosage_per_time: '',
  frequency: 'DAILY', time_points: [], start_date: '', end_date: '',
  status: 'active', notes: ''
})
const form = reactive(emptyForm())

const rules = {
  medication: [{ required: true, message: '请选择药物', trigger: 'change' }],
  frequency: [{ required: true, message: '请选择频率', trigger: 'change' }],
}

const freqLabel = (f) => ({ DAILY: '每日一次', BID: '每日两次', TID: '每日三次', QID: '每日四次', CUSTOM: '自定义' }[f] || f)

const defaultTimePoints = computed(() => {
  const m = { DAILY: '08:00', BID: '08:00, 20:00', TID: '08:00, 12:00, 20:00', QID: '06:00, 10:00, 14:00, 20:00' }
  return m[form.frequency] || '-'
})

const load = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.search = keyword.value
    const data = await planApi.list(params)
    list.value = data.results || data || []
    total.value = data.count || data.length || 0
  } finally {
    loading.value = false
  }
}

const loadMedications = async () => {
  const data = await medicationApi.list({ page_size: 200 })
  medicationOptions.value = data.results || data || []
}

const loadPatients = async () => {
  const data = await userApi.list({ role: 'patient', page_size: 200 })
  patientOptions.value = data.results || data || []
}

onMounted(async () => {
  await Promise.all([load(), loadMedications(), ...(auth.isAdmin ? [loadPatients()] : [])])
})

const openDialog = (row) => {
  Object.assign(form, emptyForm())
  customTimes.value = []
  if (row) {
    Object.assign(form, row)
    form.medication = typeof row.medication === 'object' ? row.medication?.id : row.medication
    customTimes.value = Array.isArray(row.time_points) ? [...row.time_points] : []
  }
  dialogVisible.value = true
}

const addTimePoint = () => {
  const v = newTimePoint.value.trim()
  if (v && customTimes.value.length < 10 && customTimes.value.every(t => t !== v)) {
    customTimes.value.push(v)
  }
  newTimePoint.value = ''
}

const onSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    const payload = { ...form }
    if (form.frequency === 'CUSTOM') {
      payload.time_points = customTimes.value
    } else {
      payload.time_points = []
    }
    if (!payload.end_date) delete payload.end_date
    if (form.id) {
      await planApi.update(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await planApi.create(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

const onRemove = async (id) => {
  await planApi.remove(id)
  ElMessage.success('已删除')
  load()
}
</script>

<style scoped>
.header-bar { display: flex; justify-content: space-between; align-items: center; }
.dynamic-times { display: flex; align-items: center; flex-wrap: wrap; }
</style>
