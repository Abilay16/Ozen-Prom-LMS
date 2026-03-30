import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

app.use(createPinia())

// Guard must be registered BEFORE app.use(router) so it runs on the initial navigation
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const role = localStorage.getItem('role')
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }
  if (to.meta.role && role !== to.meta.role) {
    if (role === 'admin') return next('/admin')
    if (role === 'learner') return next('/my')
    return next('/login')
  }
  next()
})

app.use(router)
app.mount('#app')
