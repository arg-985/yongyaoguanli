import { defineStore } from 'pinia'
import { authApi } from '../api/modules'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    refresh: localStorage.getItem('refresh') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    isPatient: (state) => state.user?.role === 'patient',
    isDoctor: (state) => state.user?.role === 'doctor',
  },
  actions: {
    setAuth({ token, refresh, user }) {
      this.token = token || ''
      this.refresh = refresh || ''
      if (user) this.user = user
      localStorage.setItem('token', this.token)
      if (this.refresh) localStorage.setItem('refresh', this.refresh)
      if (this.user) localStorage.setItem('user', JSON.stringify(this.user))
    },
    async fetchMe() {
      try {
        const data = await authApi.me()
        this.user = data
        localStorage.setItem('user', JSON.stringify(data))
        return data
      } catch (e) {
        this.logout()
        throw e
      }
    },
    logout() {
      this.token = ''
      this.refresh = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('refresh')
      localStorage.removeItem('user')
    },
  }
})
