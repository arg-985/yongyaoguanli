<template>
  <div class="ac-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">🏥 基础数据</span>
        <h1>科室、<em>药品库</em>与排班表</h1>
        <p>药品价格与库存只由管理员维护，医生开方时只能读取</p>
      </div>
    </div>

    <div class="candy-card tilt-sky">
      <el-tabs v-model="tab">
        <!-- 科室 -->
        <el-tab-pane name="departments">
          <template #label><span class="tab-label">🏢 科室管理</span></template>
          <div class="toolbar">
            <span class="hint">控制科室是否开放挂号</span>
            <el-button type="primary" @click="openDept(null)">＋ 新建科室</el-button>
          </div>
          <el-table :data="departments" v-loading="loading" stripe>
            <el-table-column prop="name" label="科室名称" width="140" />
            <el-table-column prop="code" label="编码" width="110" />
            <el-table-column prop="description" label="简介" min-width="240">
              <template #default="{ row }">{{ row.description || '—' }}</template>
            </el-table-column>
            <el-table-column label="开放挂号" width="110">
              <template #default="{ row }">
                <el-switch :model-value="row.is_open" size="small" @change="(val) => toggleDept(row, val)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDept(row)">编辑</el-button>
                <el-button link type="danger" @click="removeDept(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 药品 -->
        <el-tab-pane name="medications">
          <template #label><span class="tab-label">💊 药品库</span></template>
          <div class="toolbar">
            <el-input v-model="medKeyword" placeholder="搜索药品名" clearable style="width:220px" />
            <span class="count-hint">共 {{ filteredMeds.length }} 种药品</span>
            <el-button type="primary" style="margin-left:auto" @click="openMed(null)">＋ 新增药品</el-button>
          </div>
          <el-table :data="filteredMeds" v-loading="loading" stripe>
            <el-table-column prop="name" label="药品名" min-width="150" />
            <el-table-column prop="specification" label="规格" min-width="130" />
            <el-table-column prop="unit" label="单位" width="80" />
            <el-table-column prop="category" label="分类" width="110">
              <template #default="{ row }">{{ row.category || '—' }}</template>
            </el-table-column>
            <el-table-column label="单价" width="100">
              <template #default="{ row }"><span class="price">¥{{ row.price }}</span></template>
            </el-table-column>
            <el-table-column label="库存" width="110">
              <template #default="{ row }">
                <el-tag :type="Number(row.stock) <= 10 ? 'danger' : 'success'" size="small">{{ row.stock }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="处方药" width="90">
              <template #default="{ row }">{{ row.is_otc ? 'OTC' : '处方药' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openMed(row)">编辑</el-button>
                <el-button link type="danger" @click="removeMed(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 排班 -->
        <el-tab-pane name="schedules">
          <template #label><span class="tab-label">📆 排班与号源</span></template>
          <div class="toolbar">
            <span class="hint">排班决定患者挂号的时段与号源数量</span>
            <el-button type="primary" style="margin-left:auto" @click="openSch(null)">＋ 添加排班</el-button>
          </div>
          <el-table :data="schedules" v-loading="loading" stripe>
            <el-table-column label="医生" width="150">
              <template #default="{ row }">{{ row.doctor_name || row.doctor_username }}</template>
            </el-table-column>
            <el-table-column label="星期" width="100">
              <template #default="{ row }">{{ weekdayText(row.weekday) }}</template>
            </el-table-column>
            <el-table-column label="时段" width="90">
              <template #default="{ row }">{{ periodText(row.period) }}</template>
            </el-table-column>
            <el-table-column prop="room" label="诊室" min-width="140" />
            <el-table-column prop="capacity" label="号源数" width="100" />
            <el-table-column label="操作" width="140">
              <template #default="{ row }">
                <el-button link type="primary" @click="openSch(row)">编辑</el-button>
                <el-button link type="danger" @click="removeSch(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 科室弹窗 -->
    <el-dialog v-model="deptDialog" :title="deptEditing ? '编辑科室' : '新建科室'" width="460px">
      <el-form label-width="84px">
        <el-form-item label="科室名称" required><el-input v-model="deptForm.name" placeholder="如：内科" /></el-form-item>
        <el-form-item label="科室编码"><el-input v-model="deptForm.code" placeholder="如：NK" /></el-form-item>
        <el-form-item label="科室简介"><el-input v-model="deptForm.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="开放挂号"><el-switch v-model="deptForm.is_open" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deptDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDept">保存</el-button>
      </template>
    </el-dialog>

    <!-- 药品弹窗 -->
    <el-dialog v-model="medDialog" :title="medEditing ? '编辑药品' : '新增药品'" width="540px">
      <el-form label-width="84px">
        <el-form-item label="药品名" required><el-input v-model="medForm.name" /></el-form-item>
        <el-form-item label="通用名"><el-input v-model="medForm.generic_name" /></el-form-item>
        <el-form-item label="规格"><el-input v-model="medForm.specification" placeholder="如：50μg×100片" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="medForm.unit" placeholder="盒 / 瓶 / 支" /></el-form-item>
        <el-form-item label="分类"><el-input v-model="medForm.category" placeholder="如：甲状腺激素" /></el-form-item>
        <el-form-item label="单价">
          <el-input-number v-model="medForm.price" :min="0" :precision="2" :step="0.5" />
        </el-form-item>
        <el-form-item label="库存">
          <el-input-number v-model="medForm.stock" :min="0" :precision="0" />
        </el-form-item>
        <el-form-item label="非处方药"><el-switch v-model="medForm.is_otc" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="medDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMed">保存</el-button>
      </template>
    </el-dialog>

    <!-- 排班弹窗 -->
    <el-dialog v-model="schDialog" :title="schEditing ? '编辑排班' : '添加排班'" width="480px">
      <el-form label-width="84px">
        <el-form-item label="医生" required>
          <el-select v-model="schForm.doctor" placeholder="选择医生" style="width:100%">
            <el-option
              v-for="d in doctors"
              :key="d.id"
              :label="`${d.real_name} · ${d.department || '未设置科室'}`"
              :value="d.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="星期" required>
          <el-select v-model="schForm.weekday" style="width:100%">
            <el-option v-for="(w, i) in weekdays" :key="i" :label="w" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="时段" required>
          <el-select v-model="schForm.period" style="width:100%">
            <el-option label="上午" value="AM" />
            <el-option label="下午" value="PM" />
            <el-option label="夜班" value="NIGHT" />
          </el-select>
        </el-form-item>
        <el-form-item label="诊室"><el-input v-model="schForm.room" placeholder="如：内科 3 诊室" /></el-form-item>
        <el-form-item label="号源数"><el-input-number v-model="schForm.capacity" :min="1" :max="100" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="schDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSch">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { medicationApi, workflowApi } from '../../api/modules'

const tab = ref('departments')
const loading = ref(false)
const departments = ref([])
const meds = ref([])
const schedules = ref([])
const doctors = ref([])
const medKeyword = ref('')

const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const deptDialog = ref(false)
const deptEditing = ref(null)
const deptForm = reactive({ name: '', code: '', description: '', is_open: true })

const medDialog = ref(false)
const medEditing = ref(null)
const medForm = reactive({ name: '', generic_name: '', specification: '', unit: '', category: '', price: 0, stock: 0, is_otc: true })

const schDialog = ref(false)
const schEditing = ref(null)
const schForm = reactive({ doctor: null, weekday: 0, period: 'AM', room: '', capacity: 20 })

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const weekdayText = (w) => weekdays[w] || '—'
const periodText = (p) => ({ AM: '上午', PM: '下午', NIGHT: '夜班' }[p] || p)

const filteredMeds = computed(() => {
  const kw = medKeyword.value.trim()
  if (!kw) return meds.value
  return meds.value.filter((m) => (m.name || '').includes(kw) || (m.generic_name || '').includes(kw))
})

const load = async () => {
  loading.value = true
  try {
    const [dept, med, sch, docs] = await Promise.all([
      workflowApi.departments(),
      medicationApi.list({ page_size: 200 }),
      workflowApi.schedules({}),
      workflowApi.doctors(),
    ])
    departments.value = listOf(dept)
    meds.value = listOf(med)
    schedules.value = listOf(sch)
    doctors.value = listOf(docs)
  } finally {
    loading.value = false
  }
}

// ---------- 科室 ----------
const openDept = (row) => {
  deptEditing.value = row
  Object.assign(deptForm, row
    ? { name: row.name, code: row.code || '', description: row.description || '', is_open: row.is_open }
    : { name: '', code: '', description: '', is_open: true })
  deptDialog.value = true
}
const saveDept = async () => {
  if (!deptForm.name.trim()) { ElMessage.warning('请填写科室名称'); return }
  if (deptEditing.value) await workflowApi.departmentUpdate(deptEditing.value.id, { ...deptForm })
  else await workflowApi.departmentCreate({ ...deptForm })
  deptDialog.value = false
  ElMessage.success('科室已保存')
  await load()
}
const toggleDept = async (row, val) => {
  await workflowApi.departmentUpdate(row.id, { is_open: val })
  row.is_open = val
  ElMessage.success(val ? `${row.name} 已开放挂号` : `${row.name} 已停止挂号`)
}
const removeDept = async (row) => {
  try { await ElMessageBox.confirm(`删除科室「${row.name}」？`, '删除科室', { type: 'warning' }) } catch (e) { return }
  await workflowApi.departmentRemove(row.id)
  ElMessage.success('科室已删除')
  await load()
}

// ---------- 药品 ----------
const openMed = (row) => {
  medEditing.value = row
  Object.assign(medForm, row
    ? {
        name: row.name, generic_name: row.generic_name || '', specification: row.specification || '',
        unit: row.unit || '', category: row.category || '', price: Number(row.price || 0),
        stock: Number(row.stock || 0), is_otc: !!row.is_otc,
      }
    : { name: '', generic_name: '', specification: '', unit: '盒', category: '', price: 0, stock: 0, is_otc: true })
  medDialog.value = true
}
const saveMed = async () => {
  if (!medForm.name.trim()) { ElMessage.warning('请填写药品名'); return }
  if (medEditing.value) await medicationApi.update(medEditing.value.id, { ...medForm })
  else await medicationApi.create({ ...medForm })
  medDialog.value = false
  ElMessage.success('药品已保存')
  await load()
}
const removeMed = async (row) => {
  try { await ElMessageBox.confirm(`删除药品「${row.name}」？关联用药计划会一并失效。`, '删除药品', { type: 'warning' }) } catch (e) { return }
  await medicationApi.remove(row.id)
  ElMessage.success('药品已删除')
  await load()
}

// ---------- 排班 ----------
const openSch = (row) => {
  schEditing.value = row
  Object.assign(schForm, row
    ? { doctor: row.doctor, weekday: row.weekday, period: row.period, room: row.room || '', capacity: row.capacity }
    : { doctor: null, weekday: 0, period: 'AM', room: '', capacity: 20 })
  schDialog.value = true
}
const saveSch = async () => {
  if (!schForm.doctor) { ElMessage.warning('请选择医生'); return }
  if (schEditing.value) await workflowApi.scheduleUpdate(schEditing.value.id, { ...schForm })
  else await workflowApi.scheduleCreate({ ...schForm })
  schDialog.value = false
  ElMessage.success('排班已保存')
  await load()
}
const removeSch = async (row) => {
  try { await ElMessageBox.confirm('删除该排班？', '删除排班', { type: 'warning' }) } catch (e) { return }
  await workflowApi.scheduleRemove(row.id)
  ElMessage.success('排班已删除')
  await load()
}

onMounted(load)
</script>

<style scoped>
.ac-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.tab-label { font-weight: 800; }
.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
.hint { font-size: 12px; color: var(--ink-faint); }
.count-hint { font-size: 12px; color: var(--ink-faint); }
.price { font-weight: 900; color: var(--orange-deep); }
</style>
