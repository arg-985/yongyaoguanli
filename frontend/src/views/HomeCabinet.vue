<template>
  <div class="cabinet-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">🧴 家庭药箱</span>
        <h1>家里的药，<em>都在这儿</em></h1>
        <p>记录数量、有效期与存放位置，过期前药药会提醒你</p>
      </div>
      <el-button type="primary" size="large" @click="openDialog()">
        <span class="btn-emoji">＋</span> 放进新药
      </el-button>
    </div>

    <div class="stat-grid" style="margin-bottom:18px">
      <div class="stat-tile sky">
        <div class="num">{{ stats.total }}</div>
        <div class="label">药箱里的药品</div>
        <span class="icon">🧴</span>
      </div>
      <div class="stat-tile orange">
        <div class="num">{{ stats.expiring }}</div>
        <div class="label">30 天内要到期</div>
        <span class="icon">⏰</span>
      </div>
      <div class="stat-tile pink">
        <div class="num">{{ stats.expired }}</div>
        <div class="label">已经过期</div>
        <span class="icon">🗑️</span>
      </div>
    </div>

    <el-row :gutter="18" style="margin-bottom:18px;align-items:stretch">
      <el-col :xs="24" :md="8" style="display:flex">
        <div class="candy-card tilt-mint" style="flex:1">
          <div class="card-title">
            <span class="jelly mint">🍩</span>
            <div>
              <div class="t-main">效期分布</div>
              <div class="t-sub">Chart.js 环形图</div>
            </div>
          </div>
          <ChartExpiry :data="expiryChartData" :center-text="String(stats.total)" />
        </div>
      </el-col>
      <el-col :xs="24" :md="16" style="display:flex">
        <div class="candy-card tilt-orange" style="flex:1">
          <div class="card-title">
            <span class="jelly orange">⏰</span>
            <div>
              <div class="t-main">到期提醒</div>
              <div class="t-sub">这些药要先用 / 先处理</div>
            </div>
          </div>
          <el-empty v-if="!alertItems.length" description="药箱很健康，没有临期或过期药品" :image-size="60" />
          <div v-else class="alert-list">
            <div v-for="a in alertItems" :key="a.key" class="alert-item" :class="a.kind">
              <span class="alert-emoji">{{ a.kind === 'expired' ? '🗑️' : '⏰' }}</span>
              <div class="alert-info">
                <div class="alert-name">{{ a.name }}</div>
                <div class="alert-sub">有效期至 {{ a.expiry_date || '-' }}</div>
              </div>
              <span class="pill" :class="a.kind === 'expired' ? 'pink' : 'yellow'">
                {{ a.kind === 'expired' ? '已过期' : `剩 ${a.days_left} 天` }}
              </span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="candy-card tilt-sky">
      <div class="card-top">
        <div class="card-title">
          <span class="jelly sky">📦</span>
          <div>
            <div class="t-main">药箱清单</div>
            <div class="t-sub">按有效期排序，先过期的先用掉</div>
          </div>
        </div>
        <el-select
          v-if="auth.isAdmin"
          v-model="patient"
          filterable
          clearable
          placeholder="选择患者"
          style="width:200px"
          @change="onFilter"
        >
          <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
        </el-select>
      </div>

      <el-table :data="list" v-loading="loading" class="cabinet-table">
        <el-table-column prop="name" label="药品名称" min-width="180">
          <template #default="{ row }">
            <div class="drug-cell">
              <span class="drug-dot">{{ row.expiry_status === 'expired' ? '🗑️' : row.expiry_status === 'soon' ? '⏰' : '💊' }}</span>
              <span class="drug-name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="120">
          <template #default="{ row }">
            <span class="qty">{{ Number(row.quantity) }} {{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="180">
          <template #default="{ row }">
            <div class="expiry-cell">
              <span>{{ row.expiry_date || '-' }}</span>
              <span v-if="row.expiry_status === 'expired'" class="pill pink">已过期</span>
              <span v-else-if="row.expiry_status === 'soon'" class="pill yellow">剩 {{ row.days_left }} 天</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="opened_at" label="开封日期" width="130">
          <template #default="{ row }">{{ row.opened_at || '-' }}</template>
        </el-table-column>
        <el-table-column prop="location" label="存放位置" min-width="130">
          <template #default="{ row }">{{ row.location || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
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
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        class="pager"
        @size-change="load" @current-change="load"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑药品' : '放进新药'" width="520px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item v-if="auth.isAdmin" label="患者" prop="patient_id">
          <el-select v-model="form.patient_id" filterable placeholder="选择患者" style="width:100%">
            <el-option v-for="u in patients" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如 布洛芬缓释胶囊" />
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="0" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-select v-model="form.unit" filterable allow-create default-first-option style="width:100%">
            <el-option v-for="u in unitOptions" :key="u" :label="u" :value="u" />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期至">
          <el-date-picker v-model="form.expiry_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="开封日期">
          <el-date-picker v-model="form.opened_at" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="存放位置">
          <el-input v-model="form.location" placeholder="如 客厅抽屉 / 冰箱冷藏" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { clinicApi, userApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import ChartExpiry from '../components/ChartExpiry.vue'

const auth = useAuthStore()
const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const patient = ref(null)
const patients = ref([])
const dialogVisible = ref(false)
const formRef = ref()
const unitOptions = ['盒', '片', '瓶', '支', '袋', '包']
const stats = reactive({ total: 0, expiring: 0, expired: 0 })
const alertItems = ref([])

const expiryChartData = computed(() => [
  { label: '正常', value: Math.max(0, stats.total - stats.expiring - stats.expired) },
  { label: '30天内到期', value: stats.expiring },
  { label: '已过期', value: stats.expired },
])

const emptyForm = () => ({
  id: null, patient_id: null, name: '', quantity: 1, unit: '盒',
  expiry_date: '', opened_at: '', location: '', notes: ''
})
const form = reactive(emptyForm())

const rules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  name: [{ required: true, message: '请填写药品名称', trigger: 'blur' }],
  quantity: [{ required: true, message: '请填写数量', trigger: 'blur' }],
}

const patientParams = () => (patient.value ? { patient_id: patient.value } : {})

const load = async () => {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value, ...patientParams() }
    const [data, alerts] = await Promise.all([
      clinicApi.cabinetList(params),
      clinicApi.cabinetAlerts(patientParams())
    ])
    list.value = data.results || data || []
    total.value = data.count ?? list.value.length
    stats.total = total.value
    stats.expiring = alerts.expiring?.length || 0
    stats.expired = alerts.expired?.length || 0
    alertItems.value = [
      ...(alerts.expiring || []).map(x => ({ ...x, kind: 'soon', key: 's' + x.id })),
      ...(alerts.expired || []).map(x => ({ ...x, kind: 'expired', key: 'e' + x.id })),
    ].slice(0, 8)
  } finally {
    loading.value = false
  }
}

const onFilter = () => { page.value = 1; load() }

onMounted(async () => {
  if (auth.isAdmin) {
    const data = await userApi.list({ role: 'patient', page_size: 200 })
    patients.value = data.results || data || []
  }
  load()
})

const openDialog = (row) => {
  Object.assign(form, emptyForm())
  if (auth.isAdmin) form.patient_id = patient.value || null
  if (row) {
    Object.assign(form, {
      id: row.id,
      name: row.name,
      quantity: Number(row.quantity),
      unit: row.unit,
      expiry_date: row.expiry_date || '',
      opened_at: row.opened_at || '',
      location: row.location || '',
      notes: row.notes || ''
    })
  }
  dialogVisible.value = true
}

const onSubmit = async () => {
  await formRef.value.validate()
  submitting.value = true
  try {
    const payload = {
      name: form.name,
      quantity: form.quantity,
      unit: form.unit,
      expiry_date: form.expiry_date || null,
      opened_at: form.opened_at || null,
      location: form.location,
      notes: form.notes
    }
    if (auth.isAdmin) payload.patient_id = form.patient_id
    if (form.id) {
      await clinicApi.cabinetUpdate(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await clinicApi.cabinetCreate(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

const onRemove = async (id) => {
  await clinicApi.cabinetRemove(id)
  ElMessage.success('已删除')
  load()
}
</script>

<style scoped>
.cabinet-page { max-width: 1400px; }
.btn-emoji { margin-right: 4px; font-weight: 800; }

.card-top { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
.card-title { display: flex; align-items: center; gap: 12px; }
.card-title .t-main { font-size: 16px; font-weight: 800; color: var(--ink); }
.card-title .t-sub { font-size: 11px; color: var(--ink-faint); }

.drug-cell { display: flex; align-items: center; gap: 8px; }
.drug-dot { font-size: 16px; }
.drug-name { font-weight: 700; color: var(--ink); }
.qty { font-weight: 700; color: #E8862B; }
.expiry-cell { display: flex; flex-direction: column; gap: 4px; }
.expiry-cell .pill { align-self: flex-start; }

.alert-list { display: flex; flex-direction: column; gap: 8px; max-height: 210px; overflow-y: auto; }
.alert-item {
  display: flex; align-items: center; gap: 10px;
  background: #FFFDF7; border: 2px solid #FFEBD0; border-radius: 14px;
  padding: 8px 12px;
}
.alert-item.expired { border-color: #FFD1D9; background: #FFFBFB; }
.alert-emoji { font-size: 18px; }
.alert-info { flex: 1; min-width: 0; }
.alert-name { font-size: 13px; font-weight: 800; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.alert-sub { font-size: 11px; color: var(--ink-faint); margin-top: 2px; }

.pager { margin-top: 16px; justify-content: flex-end; display: flex; }

@media (max-width: 900px) {
  .stat-grid { grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .stat-tile .num { font-size: 24px; }
}
</style>
