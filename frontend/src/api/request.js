import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 默认走相对路径：开发时由 Vite 代理到 http://127.0.0.1:8001，
// 生产时由 vercel.json 的 /api 重写转发到后端，无需写死域名。
// 如需直连独立后端，可在 .env 中配置 VITE_API_BASE_URL（例如 https://xxx.onrender.com）。
const baseURL = import.meta.env.VITE_API_BASE_URL || ''

const request = axios.create({
  baseURL,
  timeout: 15000
})

request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    const msg = error.response?.data?.detail || error.message
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('refresh')
      localStorage.removeItem('user')
      ElMessage.warning('登录已过期，请重新登录')
      router.push('/login')
    } else if (status === 403) {
      ElMessage.error('无权限访问')
    } else {
      ElMessage.error(msg || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default request
