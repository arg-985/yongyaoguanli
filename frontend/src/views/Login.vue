<template>
  <div class="login-wrap">
    <div class="login-box">
      <!-- 左侧插画区 -->
      <div class="login-left">
        <div class="illu-wrap">
          <ThreePillRain />
          <div class="blob b1"></div>
          <div class="blob b2"></div>
          <div class="blob b3"></div>
          <div class="dog-card">
            <img src="/assets/dog-sprite.png" alt="小狗管家" />
            <div class="dog-say">汪～你今天吃药了吗？</div>
          </div>
          <span class="spark s1">✦</span>
          <span class="spark s2">✧</span>
          <span class="spark s3">✦</span>
          <span class="spark s4">✧</span>
        </div>
        <div class="brand">
          <div class="brand-name">家庭全科用药助手</div>
          <div class="brand-sub">智能提醒 · 医患协同 · 数据洞察</div>
        </div>
      </div>

      <!-- 右侧表单 -->
      <div class="login-right">
        <div class="form-head">
          <div class="head-title">欢迎回来 🐾</div>
          <div class="head-sub">登录你的账号，小狗管家在等你</div>
        </div>

        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" :rules="loginRules" ref="loginRef" label-width="0">
              <el-form-item prop="username">
                <el-input v-model="loginForm.username" placeholder="用户名" size="large">
                  <template #prefix><span class="input-emoji">👤</span></template>
                </el-input>
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" show-password>
                  <template #prefix><span class="input-emoji">🔒</span></template>
                </el-input>
              </el-form-item>
              <div class="form-links">
                <el-checkbox v-model="remember" label="记住我" />
                <a class="link" @click="activeTab = 'reset'">忘记密码？</a>
              </div>
              <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="doLogin">登录</el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="registerForm" :rules="registerRules" ref="regRef" label-width="0">
              <el-form-item prop="username">
                <el-input v-model="registerForm.username" placeholder="用户名" size="large">
                  <template #prefix><span class="input-emoji">👤</span></template>
                </el-input>
              </el-form-item>
              <el-form-item prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="密码（至少 8 位）" size="large" show-password>
                  <template #prefix><span class="input-emoji">🔒</span></template>
                </el-input>
              </el-form-item>
              <el-form-item prop="role">
                <div class="role-fixed">
                  🐶 注册身份：<b>患者</b>
                  <span class="role-tip">医生 / 管理员账号由医院管理员分配</span>
                </div>
              </el-form-item>
              <el-form-item prop="phone">
                <el-input v-model="registerForm.phone" placeholder="手机号（可选，用于找回密码）" size="large">
                  <template #prefix><span class="input-emoji">📱</span></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="doRegister">注册</el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="忘记密码" name="reset">
            <el-form :model="resetForm" :rules="resetRules" ref="resetRef" label-width="0">
              <el-form-item prop="phone">
                <el-input v-model="resetForm.phone" placeholder="注册时用的手机号" size="large">
                  <template #prefix><span class="input-emoji">📱</span></template>
                </el-input>
              </el-form-item>
              <el-form-item prop="code">
                <div class="code-row">
                  <el-input v-model="resetForm.code" placeholder="6 位验证码" size="large" maxlength="6">
                    <template #prefix><span class="input-emoji">🗝️</span></template>
                  </el-input>
                  <el-button size="large" :loading="codeSending" :disabled="codeCountdown > 0" @click="sendCode">
                    {{ codeCountdown > 0 ? `${codeCountdown}s` : '获取验证码' }}
                  </el-button>
                </div>
              </el-form-item>
              <div v-if="devCode" class="dev-hint">
                🧪 开发模式：验证码 <b>{{ devCode }}</b>（不真发短信）
              </div>
              <el-form-item prop="new_password">
                <el-input v-model="resetForm.new_password" type="password" placeholder="新密码（至少 6 位）" size="large" show-password>
                  <template #prefix><span class="input-emoji">🔑</span></template>
                </el-input>
              </el-form-item>
              <el-button type="primary" size="large" class="submit-btn" :loading="loading" @click="doReset">重置密码</el-button>
              <div class="back-to-login">
                想起来了？<a class="link" @click="activeTab = 'login'">回到登录</a>
              </div>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api/modules'
import { useAuthStore } from '../stores/auth'
import { homeFor } from '../router'
import ThreePillRain from '../components/ThreePillRain.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeTab = ref(route.query.tab || 'login')
const loading = ref(false)
const loginRef = ref()
const regRef = ref()
const resetRef = ref()
const remember = ref(false)
const codeSending = ref(false)
const codeCountdown = ref(0)
const devCode = ref('')

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', role: 'patient', phone: '' })
const resetForm = reactive({ phone: '', code: '', new_password: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择身份', trigger: 'change' }],
}
const resetRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入 6 位验证码', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码应为 6 位数字', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 位', trigger: 'blur' },
  ],
}

const doLogin = async () => {
  await loginRef.value.validate()
  loading.value = true
  try {
    const data = await authApi.login(loginForm)
    auth.setAuth({ token: data.access, refresh: data.refresh })
    await auth.fetchMe()
    ElMessage.success('登录成功，小狗管家欢迎你 🐶')
    router.push(homeFor(auth.user?.role))
  } finally {
    loading.value = false
  }
}

const doRegister = async () => {
  await regRef.value.validate()
  loading.value = true
  try {
    await authApi.register(registerForm)
    ElMessage.success('注册成功，去登录吧')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
  } finally {
    loading.value = false
  }
}

const sendCode = async () => {
  if (!/^1\d{10}$/.test(resetForm.phone)) {
    ElMessage.warning('请先输入正确的手机号')
    return
  }
  codeSending.value = true
  try {
    const res = await authApi.sendResetCode(resetForm.phone)
    ElMessage.success('验证码已发送')
    if (res.dev_code) devCode.value = res.dev_code
    codeCountdown.value = 60
    const timer = setInterval(() => {
      codeCountdown.value -= 1
      if (codeCountdown.value <= 0) clearInterval(timer)
    }, 1000)
  } finally {
    codeSending.value = false
  }
}

const doReset = async () => {
  await resetRef.value.validate()
  loading.value = true
  try {
    await authApi.resetPassword({
      phone: resetForm.phone,
      code: resetForm.code,
      new_password: resetForm.new_password
    })
    ElMessage.success('密码重置成功，请重新登录')
    activeTab.value = 'login'
    devCode.value = ''
    resetForm.phone = ''
    resetForm.code = ''
    resetForm.new_password = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ---------- 糖果风登录页（与系统整体背景统一） ---------- */
.login-wrap {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background-color: #FFFBF2;
  background-image:
    radial-gradient(circle at 12% 8%, #FFF1C9 0 22%, transparent 23%),
    radial-gradient(circle at 88% 4%, #FFE6EE 0 18%, transparent 19%),
    radial-gradient(circle at 78% 82%, #E6F7FF 0 18%, transparent 19%);
  padding: 20px;
}

.login-box {
  display: flex; width: 900px; height: 540px;
  background: #FFFDF7;
  border-radius: 32px;
  overflow: hidden;
  border: 3px solid #FFE2B8;
  box-shadow: 0 20px 50px rgba(201, 155, 92, .22);
}

/* ---------- 左侧插画 ---------- */
.login-left {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, #FFE8C9 0%, #FFD3DF 100%);
  padding: 36px 32px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.illu-wrap {
  position: absolute; inset: 0; overflow: hidden;
}
.blob {
  position: absolute; border-radius: 50%;
  filter: blur(4px);
}
.blob.b1 { width: 220px; height: 220px; background: #FFC9B0; top: -40px; left: -40px; opacity: .7; }
.blob.b2 { width: 160px; height: 160px; background: #FFE07A; bottom: 80px; right: -20px; opacity: .6; }
.blob.b3 { width: 100px; height: 100px; background: #CDE9F7; top: 120px; right: 60px; opacity: .6; }

.dog-card {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -55%);
  width: 220px; height: 220px;
  border-radius: 50%;
  background: rgba(255, 253, 247, .9);
  border: 3px solid #FFE6A8;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  box-shadow: 0 10px 24px rgba(232, 134, 43, .18);
}
.dog-card img { width: 160px; height: 160px; object-fit: contain; animation: bob 2.4s ease-in-out infinite; }
.dog-say {
  position: absolute; top: -22px; left: 50%; transform: translateX(-50%);
  background: #FFFDF7; border: 2px solid #FFE6A8; border-radius: 14px;
  padding: 5px 12px; font-size: 12px; font-weight: 800; color: var(--pink-deep);
  white-space: nowrap;
  animation: bob 2.4s ease-in-out infinite .5s;
}
.dog-say::after {
  content: ''; position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%);
  width: 14px; height: 14px; background: #FFFDF7; border-right: 2px solid #FFE6A8; border-bottom: 2px solid #FFE6A8;
  transform: translateX(-50%) rotate(45deg); border-bottom-right-radius: 3px;
}

@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
@keyframes bob-mirror {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(-8px); }
}
.dog-say { animation: bob-mirror 2.4s ease-in-out infinite .5s; }

.spark {
  position: absolute; font-size: 16px; color: #FFD24A; animation: twinkle 2s ease-in-out infinite;
}
.spark.s1 { top: 60px; left: 30px; }
.spark.s2 { top: 120px; right: 40px; color: #FF9DB4; animation-delay: .5s; }
.spark.s3 { bottom: 140px; left: 50px; color: #8FE3C4; animation-delay: 1s; }
.spark.s4 { bottom: 80px; right: 30px; }
@keyframes twinkle { 0%,100% { opacity: .4; transform: scale(.8); } 50% { opacity: 1; transform: scale(1.15); } }

.brand { position: relative; z-index: 2; }
.brand-name { font-size: 24px; font-weight: 800; color: #4A3B32; letter-spacing: 1px; }
.brand-sub { font-size: 12px; color: #8A7466; margin-top: 6px; }

/* ---------- 右侧表单 ---------- */
.login-right {
  flex: 1; padding: 44px 44px;
  display: flex; flex-direction: column; justify-content: center;
}
.form-head { margin-bottom: 20px; }
.head-title { font-size: 24px; font-weight: 800; color: var(--ink); }
.head-sub { font-size: 12.5px; color: var(--ink-faint); margin-top: 4px; }

.login-tabs :deep(.el-tabs__item) { font-size: 14px; font-weight: 700; color: var(--ink-soft); }
.login-tabs :deep(.el-tabs__item.is-active) { color: var(--pink-deep); }
.login-tabs :deep(.el-tabs__active-bar) { background-color: var(--pink) !important; height: 4px !important; border-radius: 4px; }

.input-emoji { font-size: 16px; margin-right: 4px; }

.form-links { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 13px; }
.link { color: var(--pink-deep); font-weight: 700; cursor: pointer; text-decoration: none; }
.link:hover { text-decoration: underline; }

.submit-btn {
  width: 100%; height: 48px; font-size: 15px; font-weight: 800;
  border-radius: 999px; letter-spacing: 2px;
}

.code-row { display: flex; gap: 8px; }
.code-row .el-button { border-radius: 999px; }

.role-fixed {
  width: 100%;
  padding: 10px 14px;
  border-radius: 12px;
  background: #F4FAF6;
  border: 2px dashed #CBEBDD;
  font-size: 13px;
  color: #4A7A66;
}
.role-tip { display: block; font-size: 11px; color: #93B6A7; margin-top: 3px; }

.dev-hint {
  background: #FFF8DC; border: 2px dashed #FFD24A; border-radius: 12px;
  padding: 8px 12px; font-size: 12px; color: #A97D0A; margin: -4px 0 14px;
}

.back-to-login { text-align: center; font-size: 12.5px; color: var(--ink-faint); margin-top: 12px; }

@media (max-width: 780px) {
  .login-box { width: 100%; height: auto; flex-direction: column; }
  .login-left { padding: 30px; min-height: 260px; }
  .dog-card { width: 160px; height: 160px; }
  .dog-card img { width: 110px; height: 110px; }
  .login-right { padding: 26px 24px; }
}
</style>
