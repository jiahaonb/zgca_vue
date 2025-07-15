import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import ScriptCreation from './components/ScriptCreation.vue'
import ChatInterface from './components/ChatInterface.vue'
import SystemStatus from './components/SystemStatus.vue'

const routes = [
  { path: '/', redirect: '/script' },
  { path: '/script', component: ScriptCreation, name: 'ScriptCreation' },
  { path: '/chat', component: ChatInterface, name: 'ChatInterface' },
  { path: '/status', component: SystemStatus, name: 'SystemStatus' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router)
app.mount('#app') 