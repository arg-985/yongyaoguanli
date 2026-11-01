<template>
  <div class="aa-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">👥 账号与角色</span>
        <h1>开户、<em>分配角色</em>、重置密码</h1>
        <p>基于 RBAC：不同角色登录后只能看到自己的页面与数据</p>
      </div>
      <el-button type="primary" size="large" round @click="openCreate">＋ 新增账号</el-button>
    </div>

    <div class="candy-card tilt-sky">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索用户名 / 姓名 / 手机号" clearable style="width:260px" />
        <el-select v-model="roleFilter" placeholder="角色筛选" clearable style="width:150px">
          <el-option label="全部角色" value="" />
          <el-option label="患者" value="patient" />
          <el-option label="医生" value="doctor" />
          <el-option label="管理员" value="admin" />
        </el-select>
        <span class="count-hint">共 {{ filtered.length }} 个账号</span>
      </div>

      <el-table :data="filtered" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column label="姓名" width="120">
          <template #default="{ row }">{{ row.real_name || '—' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="roleTag(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="科室 / 职称" min-width="160">
          <template #default="{ row }">
            <span v-if="row.role === 'doctor'">{{ row.department || '—' }} · {{ row.title || '—' }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              :disabled="row.id === auth.user?.id"
              size="small"
              @change="(val) => toggleActive(row, val)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="注册时间" width="170">
          <template #default="{ row }">{{ fmt(row.date_joined) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="resetPwd(row)">重置密码</el-button>
            <el-button link type="danger" :disabled="row.id === auth.user?.id" @click="removeUser(row)">注销</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !filtered.length" description="没有匹配的账号" :image-size="80" />
    </div>

    <el-dialog v-model="dialog" :title="editing ? '编辑账号' : '新增账号'" width="520px">
      <el-form :model="form" label-width="96px">
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" :disabled="!!editing" placeholder="登录用户名" />
        </el-form-item>
        <el-form-item :label="editing ? '重置密码' : '初始密码'">
          <el-input v-model="form.password" type="password" show-password :placeholder="editing ? '留空则不修改密码' : '至少 6 位'" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-radio-group v-model="form.role">
            <el-radio-button label="patient">患者</el-radio-button>
            <el-radio-button label="doctor">医生</el-radio-button>
            <el-radio-button label="admin">管理员</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="form.real_name" placeholder="如实填写" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="form.phone" placeholder="11 位手机号，用于找回密码" maxlength="11" />
        </el-form-item>
        <template v-if="form.role === 'doctor'">
          <el-form-item label="所属科室">
            <el-input v-model="form.department" placeholder="如：内科" />
          </el-form-item>
          <el-form-item label="职称">
            <el-input v-model="form.title" placeholder="如：主治医师" />
          </el-form-item>
        </template>
        <el-form-item v-if="form.role === 'patient'" label="过敏史">
          <el-input v-model="form.allergies" placeholder="如：青霉素过敏" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../../stores/auth'
import { userApi } from '../../api/modules'

const auth = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const users = ref([])
const keyword = ref('')
const roleFilter = ref('')
const dialog = ref(false)
const editing = ref(null)

const form = reactive({
  username: '', password: '', role: 'patient', real_name: '', phone: '',
  department: '', title: '', allergies: '',
})

const listOf = (res) => (Array.isArray(res) ? res : res.results || [])
const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 16) : '—')
const roleLabel = (r) => ({ patient: '患者', doctor: '医生', admin: '管理员' }[r] || r)
const roleTag = (r) => ({ patient: 'primary', doctor: 'success', admin: 'danger' }[r] || '')

const filtered = computed(() => {
  const kw = keyword.value.trim()
  return users.value.filter((u) => {
    if (roleFilter.value && u.role !== roleFilter.value) return false
    if (!kw) return true
    return (u.username || '').includes(kw) || (u.real_name || '').includes(kw) || (u.phone || '').includes(kw)
  })
})

const load = async () => {
  loading.value = true
  try {
    const res = await userApi.list({ page_size: 200 })
    users.value = listOf(res)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, {
    username: '', password: '', role: 'patient', real_name: '', phone: '',
    department: '', title: '', allergies: '',
  })
}

const openCreate = () => {
  editing.value = null
  resetForm()
  dialog.value = true
}

const openEdit = (row) => {
  editing.value = row
  Object.assign(form, {
    username: row.username,
    password: '',
    role: row.role,
    real_name: row.real_name || '',
    phone: row.phone || '',
    department: row.department || '',
    title: row.title || '',
    allergies: row.allergies || '',
  })
  dialog.value = true
}

const save = async () => {
  if (!form.username.trim()) { ElMessage.warning('请填写用户名'); return }
  if (!form.phone.trim()) { ElMessage.warning('请填写手机号'); return }
  if (!editing.value && form.password.length < 6) { ElMessage.warning('初始密码至少 6 位'); return }
  if (editing.value && form.password && form.password.length < 6) { ElMessage.warning('新密码至少 6 位'); return }

  const payload = {
    username: form.username.trim(),
    role: form.role,
    real_name: form.real_name,
    phone: form.phone.trim(),
    department: form.department,
    title: form.title,
    allergies: form.allergies,
  }
  if (form.password) payload.password = form.password

  saving.value = true
  try {
    if (editing.value) {
      await userApi.update(editing.value.id, payload)
      ElMessage.success('账号已更新')
    } else {
      await userApi.create(payload)
      ElMessage.success('账号已创建，请把初始密码告知本人')
    }
    dialog.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const toggleActive = async (row, val) => {
  await userApi.update(row.id, { is_active: val })
  row.is_active = val
  ElMessage.success(val ? '账号已启用' : '账号已停用')
}

const resetPwd = async (row) => {
  try {
    await ElMessageBox.confirm(`确认为 ${row.username} 重置密码？系统将生成临时密码。`, '重置密码', { type: 'warning' })
  } catch (e) { return }
  const res = await userApi.resetPassword(row.id)
  ElMessageBox.alert(
    `用户 ${row.username} 的临时密码：${res.temp_password}\n请通知本人登录后及时修改。`,
    '重置成功',
    { confirmButtonText: '知道了', type: 'success' }
  )
}

const removeUser = async (row) => {
  try {
    await ElMessageBox.confirm(`注销账号 ${row.username}？该操作不可恢复，操作会写入审计日志。`, '注销账号', { type: 'error' })
  } catch (e) { return }
  await userApi.remove(row.id)
  ElMessage.success('账号已注销')
  await load()
}

onMounted(load)
</script>

<style scoped>
.aa-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
.count-hint { font-size: 12px; color: var(--ink-faint); }
.muted { color: var(--ink-faint); }
</style>
