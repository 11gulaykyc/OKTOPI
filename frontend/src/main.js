import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { setAuthFailureHandler } from './services/api'
import { useAuthStore } from './stores/auth'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Token yenilenemezse kullanıcıyı giriş sayfasına yönlendir.
setAuthFailureHandler(() => {
  useAuthStore().logout()
  const current = router.currentRoute.value
  if (current.meta.requiresAuth) router.push({ name: 'login', query: { next: current.fullPath } })
})

app.mount('#app')
