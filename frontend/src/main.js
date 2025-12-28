import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/styles.css' // 你的全局样式（按需）
import { isDemoMode } from '@/utils/demo'
import { useAuthStore } from './stores/auth'

const bootstrap = async () => {
  if (isDemoMode) {
    const { worker } = await import('./mocks/browser')
    const baseUrl = String(import.meta.env.BASE_URL || '/').replace(/\/?$/, '/')
    await worker.start({
      serviceWorker: { url: `${baseUrl}mockServiceWorker.js` },
      onUnhandledRequest: 'bypass',
      quiet: true
    })
  }

  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)

  // 可选：首屏时把本地存储里的登录态恢复
  const auth = useAuthStore(pinia)
  auth.hydrate()

  app.mount('#app')
}

bootstrap()
