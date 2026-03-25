import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// Navigation guard — runs AFTER pinia is active
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }
  if (to.meta.role && auth.role !== to.meta.role) {
    if (auth.role === 'admin') return next('/admin')
    if (auth.role === 'learner') return next('/my')
    return next('/login')
  }
  next()
})

app.use(router)
app.mount('#app')
