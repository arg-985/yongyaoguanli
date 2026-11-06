import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 开发环境走相对路径（Vite 代理到本地 8001），生产环境直连 PythonAnywhere 后端。
// 注意：baseURL 末尾不要加 /api，modules.js 里的路径本身带 /api 前缀。
// 也可在 Vercel / .env.production 中覆盖：VITE_API_BASE_URL=https://arg1234.pythonanywhere.com
const API_BASE_PROD = 'https://arg1234.pythonanywhere.com'
const API_BASE_DEV = ''
const baseURL = import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.PROD ? API_BASE_PROD : API_BASE_DEV)

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
