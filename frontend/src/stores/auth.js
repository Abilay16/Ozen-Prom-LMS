import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const role = ref(localStorage.getItem('role') || null)
  const userId = ref(localStorage.getItem('user_id') || null)
  const fullName = ref(localStorage.getItem('full_name') || null)
  const isCommission = ref(localStorage.getItem('is_commission') === '1')

  const isAuthenticated = computed(() => !!accessToken.value)

  async function login(login, password) {
    const { data } = await api.post('/auth/login', { login, password })
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    role.value = data.role
    userId.value = data.user_id
    fullName.value = data.full_name
    isCommission.value = !!data.is_commission

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('role', data.role)
    localStorage.setItem('user_id', data.user_id)
    localStorage.setItem('full_name', data.full_name)
    localStorage.setItem('is_commission', data.is_commission ? '1' : '0')

    return data
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    role.value = null
    userId.value = null
    fullName.value = null
    localStorage.clear()
  }

  async function refresh() {
    try {
      const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken.value })
      accessToken.value = data.access_token
      localStorage.setItem('access_token', data.access_token)
      return data.access_token
    } catch {
      logout()
      return null
    }
  }

  return { accessToken, refreshToken, role, userId, fullName, isCommission, isAuthenticated, login, logout, refresh }
})
