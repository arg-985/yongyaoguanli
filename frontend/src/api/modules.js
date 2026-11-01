import request from './request'

export const authApi = {
  login: (data) => request.post('/api/token/', data),
  register: (data) => request.post('/api/users/register/', data),
  refresh: (refresh) => request.post('/api/token/refresh/', { refresh }),
  me: () => request.get('/api/users/me/'),
  sendResetCode: (phone) => request.post('/api/users/reset-password/send-code/', { phone }),
  resetPassword: (data) => request.post('/api/users/reset-password/confirm/', data),
}

export const medicationApi = {
  list: (params) => request.get('/api/medications/', { params }),
  create: (data) => request.post('/api/medications/', data),
  update: (id, data) => request.put(`/api/medications/${id}/`, data),
  remove: (id) => request.delete(`/api/medications/${id}/`),
}

export const planApi = {
  list: (params) => request.get('/api/plans/plans/', { params }),
  create: (data) => request.post('/api/plans/plans/', data),
  update: (id, data) => request.put(`/api/plans/plans/${id}/`, data),
  remove: (id) => request.delete(`/api/plans/plans/${id}/`),
}

export const reminderApi = {
  list: (params) => request.get('/api/plans/reminders/', { params }),
}

export const recordApi = {
  list: (params) => request.get('/api/records/', { params }),
  markTaken: (data) => request.post('/api/records/mark-taken/', data),
  stats: (params) => request.get('/api/records/adherence-stats/', { params }),
}

export const userApi = {
  list: (params) => request.get('/api/users/', { params }),
  create: (data) => request.post('/api/users/', data),
  update: (id, data) => request.patch(`/api/users/${id}/`, data),
  remove: (id) => request.delete(`/api/users/${id}/`),
  resetPassword: (id) => request.post(`/api/users/${id}/reset-password/`),
  updateMe: (data) => request.patch('/api/users/me/', data),
}

export const workflowApi = {
  workbench: () => request.get('/api/clinic/workflow/workbench/'),
  backup: () => request.post('/api/clinic/workflow/backup/'),
  doctors: () => request.get('/api/clinic/workflow/doctors/'),

  departments: () => request.get('/api/clinic/workflow/departments/'),
  departmentCreate: (data) => request.post('/api/clinic/workflow/departments/', data),
  departmentUpdate: (id, data) => request.patch(`/api/clinic/workflow/departments/${id}/`, data),
  departmentRemove: (id) => request.delete(`/api/clinic/workflow/departments/${id}/`),

  schedules: (params) => request.get('/api/clinic/workflow/schedules/', { params }),
  scheduleCreate: (data) => request.post('/api/clinic/workflow/schedules/', data),
  scheduleUpdate: (id, data) => request.patch(`/api/clinic/workflow/schedules/${id}/`, data),
  scheduleRemove: (id) => request.delete(`/api/clinic/workflow/schedules/${id}/`),

  appointments: (params) => request.get('/api/clinic/workflow/appointments/', { params }),
  appointmentCreate: (data) => request.post('/api/clinic/workflow/appointments/', data),
  appointmentCancel: (id) => request.post(`/api/clinic/workflow/appointments/${id}/cancel/`),

  visits: (params) => request.get('/api/clinic/workflow/visits/', { params }),
  visitCreate: (data) => request.post('/api/clinic/workflow/visits/', data),
  visitUpdate: (id, data) => request.patch(`/api/clinic/workflow/visits/${id}/`, data),
  visitFinish: (id) => request.post(`/api/clinic/workflow/visits/${id}/finish/`),
  visitExamOrders: (id, data) => request.post(`/api/clinic/workflow/visits/${id}/exam-orders/`, data),
  visitNotes: (id, data) => request.post(`/api/clinic/workflow/visits/${id}/notes/`, data),
  visitPrescriptions: (id, data) => request.post(`/api/clinic/workflow/visits/${id}/prescriptions/`, data),
  visitFollowUp: (id, data) => request.post(`/api/clinic/workflow/visits/${id}/follow-up/`, data),

  examOrders: (params) => request.get('/api/clinic/workflow/exam-orders/', { params }),
  commNotes: (params) => request.get('/api/clinic/workflow/comm-notes/', { params }),
  commConfirm: (id) => request.post(`/api/clinic/workflow/comm-notes/${id}/confirm/`),
  prescriptions: (params) => request.get('/api/clinic/workflow/prescriptions/', { params }),
  followUps: (params) => request.get('/api/clinic/workflow/follow-ups/', { params }),

  payments: (params) => request.get('/api/clinic/workflow/payments/', { params }),
  pay: (id) => request.post(`/api/clinic/workflow/payments/${id}/pay/`),

  auditLogs: (params) => request.get('/api/clinic/workflow/audit-logs/', { params }),
  toggles: () => request.get('/api/clinic/workflow/toggles/'),
  toggleUpdate: (id, data) => request.patch(`/api/clinic/workflow/toggles/${id}/`, data),
}

export const clinicApi = {
  symptoms: () => request.get('/api/clinic/symptoms/'),
  consult: (data) => request.post('/api/clinic/consult/', data),
  interactions: (params) => request.get('/api/clinic/interactions/', { params }),
  cabinetList: (params) => request.get('/api/clinic/cabinet/', { params }),
  cabinetCreate: (data) => request.post('/api/clinic/cabinet/', data),
  cabinetUpdate: (id, data) => request.put(`/api/clinic/cabinet/${id}/`, data),
  cabinetRemove: (id) => request.delete(`/api/clinic/cabinet/${id}/`),
  cabinetAlerts: (params) => request.get('/api/clinic/cabinet/alerts/', { params }),
  feedbackList: (params) => request.get('/api/clinic/feedback/', { params }),
  feedbackCreate: (data) => request.post('/api/clinic/feedback/', data),
  feedbackRemove: (id) => request.delete(`/api/clinic/feedback/${id}/`),
  feedbackSummary: (params) => request.get('/api/clinic/feedback/summary/', { params }),
  casesList: (params) => request.get('/api/clinic/cases/', { params }),
  casesCreate: (data) => request.post('/api/clinic/cases/', data),
  casesRemove: (id) => request.delete(`/api/clinic/cases/${id}/`),
  llmStatus: () => request.get('/api/clinic/llm-status/'),
}
