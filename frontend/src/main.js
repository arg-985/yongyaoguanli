import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/theme.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import VChart from 'vue-echarts'
import * as echarts from 'echarts'

import App from './App.vue'
import router from './router'

const app = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.component('VChart', VChart)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.provide('echarts', echarts)
app.mount('#app')
