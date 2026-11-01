<template>
  <div class="pp-page">
    <div class="page-hero">
      <div class="hero-text">
        <span class="eyebrow">👤 个人中心</span>
        <h1>完善资料，<em>用药更安全</em></h1>
        <p>过敏史会展示给接诊医生，请如实填写；手机号可用于找回密码</p>
      </div>
    </div>

    <div class="pp-grid">
      <div class="candy-card tilt-sky">
        <div class="card-head">
          <span class="t-main">🧾 基本资料</span>
          <span class="pill sky">账号 {{ auth.user?.username }}</span>
        </div>
        <el-form :model="form" label-width="96px" class="profile-form">
          <el-form-item label="真实姓名">
            <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.phone" placeholder="11 位手机号" maxlength="11" />
          </el-form-item>
          <el-form-item label="性别">
            <el-radio-group v-model="form.gender">
              <el-radio label="male">男</el-radio>
              <el-radio label="female">女</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="出生日期">
            <el-date-picker v-model="form.birth_date" type="date" value-format="YYYY-MM-DD" placeholder="选择出生日期" style="width:100%" />
          </el-form-item>
          <el-form-item label="家庭住址">
            <el-input v-model="form.address" placeholder="省 / 市 / 区 / 详细地址" />
          </el-form-item>
          <el-form-item label="紧急联系人">
            <el-input v-model="form.emergency_contact" placeholder="联系人姓名" />
          </el-form-item>
          <el-form-item label="紧急电话">
            <el-input v-model="form.emergency_phone" placeholder="紧急联系电话" maxlength="20" />
          </el-form-item>
          <el-form-item label="过敏史">
            <el-input v-model="form.allergies" type="textarea" :rows="2" placeholder="如：青霉素过敏、磺胺类过敏；无过敏史可填“无”" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="saveProfile">保存资料</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="right-col">
        <div class="candy-card tilt-pink">
          <div class="card-head">
            <span class="t-main">🔒 修改密码</span>
          </div>
          <el-form :model="pwd" label-width="96px">
            <el-form-item label="新密码">
              <el-input v-model="pwd.password" type="password" show-password placeholder="至少 6 位" />
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input v-model="pwd.password2" type="password" show-password placeholder="再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="changing" @click="changePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div class="candy-card tilt-mint">
          <div class="card-head">
            <span class="t-main">ℹ️ 账号信息</span>
          </div>
          <div class="info-row"><span>角色</span><b>患者</b></div>
          <div class="info-row"><span>注册时间</span><b>{{ fmt(auth.user?.date_joined) }}</b></div>
          <div class="info-row"><span>账号状态</span><b>{{ auth.user?.is_active ? '正常' : '已停用' }}</b></div>
          <div class="tip">患者只能查看自己的资料与就诊档案，无法访问医生后台与医院经营数据。</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { userApi } from '../api/modules'

const auth = useAuthStore()

const saving = ref(false)
const changing = ref(false)
const form = reactive({
  real_name: '', phone: '', gender: '', birth_date: '', address: '',
  emergency_contact: '', emergency_phone: '', allergies: '',
})
const pwd = reactive({ password: '', password2: '' })

const fmt = (t) => (t ? String(t).replace('T', ' ').slice(0, 16) : '—')

const fill = () => {
  const u = auth.user || {}
  form.real_name = u.real_name || ''
  form.phone = u.phone || ''
  form.gender = u.gender || ''
  form.birth_date = u.birth_date || ''
  form.address = u.address || ''
  form.emergency_contact = u.emergency_contact || ''
  form.emergency_phone = u.emergency_phone || ''
  form.allergies = u.allergies || ''
}

const saveProfile = async () => {
  if (form.phone && !/^1\d{10}$/.test(form.phone)) {
    ElMessage.warning('手机号格式不正确')
    return
  }
  saving.value = true
  try {
    await userApi.updateMe({ ...form })
    await auth.fetchMe()
    fill()
    ElMessage.success('资料已保存')
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  if (pwd.password.length < 6) { ElMessage.warning('新密码至少 6 位'); return }
  if (pwd.password !== pwd.password2) { ElMessage.warning('两次输入的密码不一致'); return }
  changing.value = true
  try {
    await userApi.updateMe({ password: pwd.password })
    pwd.password = ''
    pwd.password2 = ''
    ElMessage.success('密码修改成功')
  } finally {
    changing.value = false
  }
}

onMounted(async () => {
  await auth.fetchMe().catch(() => {})
  fill()
})
</script>

<style scoped>
.pp-page { padding: 4px 2px 20px; display: flex; flex-direction: column; gap: 18px; }
.pp-grid { display: grid; grid-template-columns: 1.35fr 1fr; gap: 18px; align-items: start; }
.right-col { display: flex; flex-direction: column; gap: 18px; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.t-main { font-size: 15px; font-weight: 800; color: var(--ink); }
.profile-form { max-width: 520px; }
.info-row { display: flex; justify-content: space-between; font-size: 13px; color: var(--ink-soft); padding: 6px 0; border-bottom: 1px dashed #FFE9C9; }
.info-row b { color: var(--ink); }
.tip { margin-top: 12px; font-size: 11.5px; color: var(--ink-faint); line-height: 1.7; }
@media (max-width: 1000px) { .pp-grid { grid-template-columns: 1fr; } }
</style>
