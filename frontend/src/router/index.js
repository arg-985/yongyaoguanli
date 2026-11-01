import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export const homeFor = (role) => {
  if (role === 'doctor') return '/doctor/workbench'
  if (role === 'admin') return '/admin/home'
  if (role === 'patient') return '/dashboard'
  return '/login'
}

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/', redirect: () => homeFor(JSON.parse(localStorage.getItem('user') || 'null')?.role) },
  {
    path: '/',
    component: () => import('../layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // ---------------- 患者 ----------------
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '首页', roles: ['patient'] } },
      { path: 'plans', name: 'MedicationPlans', component: () => import('../views/MedicationPlans.vue'), meta: { title: '用药计划', roles: ['patient'] } },
      { path: 'records', name: 'Records', component: () => import('../views/Records.vue'), meta: { title: '服药记录', roles: ['patient'] } },
      { path: 'calendar', name: 'Calendar', component: () => import('../views/Calendar.vue'), meta: { title: '服药日历', roles: ['patient'] } },
      { path: 'stats', name: 'AdherenceStats', component: () => import('../views/AdherenceStats.vue'), meta: { title: '依从率统计', roles: ['patient'] } },
      { path: 'clinic/cabinet', name: 'HomeCabinet', component: () => import('../views/HomeCabinet.vue'), meta: { title: '家庭药箱', roles: ['patient'] } },
      { path: 'clinic/safety', name: 'DrugSafety', component: () => import('../views/DrugSafety.vue'), meta: { title: '用药安全', roles: ['patient'] } },
      { path: 'clinic/records', name: 'HealthRecords', component: () => import('../views/HealthRecords.vue'), meta: { title: '健康档案', roles: ['patient'] } },
      { path: 'patient/appointments', name: 'PatientAppointments', component: () => import('../views/PatientAppointments.vue'), meta: { title: '预约挂号', roles: ['patient'] } },
      { path: 'patient/records', name: 'PatientRecords', component: () => import('../views/PatientRecords.vue'), meta: { title: '我的就诊档案', roles: ['patient'] } },
      { path: 'patient/profile', name: 'PatientProfile', component: () => import('../views/PatientProfile.vue'), meta: { title: '个人中心', roles: ['patient'] } },

      // ---------------- 医生 ----------------
      { path: 'doctor/workbench', name: 'DoctorWorkbench', component: () => import('../views/doctor/DoctorWorkbench.vue'), meta: { title: '接诊工作台', roles: ['doctor'] } },
      { path: 'doctor/consult', name: 'DoctorConsult', component: () => import('../views/doctor/DoctorConsult.vue'), meta: { title: '患者接诊', roles: ['doctor'] } },
      { path: 'doctor/patients', name: 'DoctorPatients', component: () => import('../views/doctor/DoctorPatients.vue'), meta: { title: '我的患者', roles: ['doctor'] } },
      { path: 'doctor/prescriptions', name: 'DoctorPrescriptions', component: () => import('../views/doctor/DoctorPrescriptions.vue'), meta: { title: '我的处方', roles: ['doctor'] } },

      // ---------------- 管理员 ----------------
      { path: 'admin/home', name: 'AdminHome', component: () => import('../views/admin/AdminHome.vue'), meta: { title: '管理总览', roles: ['admin'] } },
      { path: 'admin/accounts', name: 'AdminAccounts', component: () => import('../views/admin/AdminAccounts.vue'), meta: { title: '账号与角色', roles: ['admin'] } },
      { path: 'admin/catalog', name: 'AdminCatalog', component: () => import('../views/admin/AdminCatalog.vue'), meta: { title: '基础数据', roles: ['admin'] } },
      { path: 'admin/system', name: 'AdminSystem', component: () => import('../views/admin/AdminSystem.vue'), meta: { title: '系统安全', roles: ['admin'] } },
      { path: 'admin/medications', name: 'AdminMeds', redirect: '/admin/catalog' },
      { path: 'admin/users', name: 'AdminUsers', redirect: '/admin/accounts' },
      { path: 'family', name: 'FamilyBinding', redirect: '/patient/profile' },
    ]
  },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  const role = auth.user?.role
  const validRole = ['patient', 'doctor', 'admin'].includes(role)
  if (to.name === 'Login') {
    if (auth.token && validRole) return next(homeFor(role))
    return next()
  }
  if (!auth.token || !validRole) return next('/login')
  if (to.name === 'Dashboard' && role !== 'patient') {
    return next(homeFor(role))
  }
  if (to.meta.roles && to.meta.roles.length > 0 && !to.meta.roles.includes(role)) {
    return next(homeFor(role))
  }
  next()
})

export default router
