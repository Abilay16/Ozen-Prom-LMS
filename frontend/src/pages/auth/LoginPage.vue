<template>
  <div class="min-h-screen bg-gradient-to-br from-brand-dark to-primary-700 flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white">Озен-Пром</h1>
        <p class="text-blue-200 mt-1">Учебный центр по охране труда</p>
      </div>

      <div class="card">
        <h2 class="text-xl font-semibold text-gray-800 mb-6">Вход в систему</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Логин</label>
            <input
              v-model="form.login"
              type="text"
              class="input-field"
              placeholder="Введите логин"
              autocomplete="username"
              required
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
            <input
              v-model="form.password"
              type="password"
              class="input-field"
              placeholder="Введите пароль"
              autocomplete="current-password"
              required
            />
          </div>

          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {{ error }}
          </div>

          <button type="submit" :disabled="loading" class="btn-primary w-full mt-2">
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>
        </form>

        <div class="mt-4 text-center">
          <RouterLink to="/" class="text-sm text-gray-500 hover:text-brand-mid">← На главную</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ login: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const data = await auth.login(form.value.login, form.value.password)
    if (data.role === 'admin') {
      router.push('/admin/dashboard')
    } else {
      router.push('/my/courses')
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Неверный логин или пароль'
  } finally {
    loading.value = false
  }
}
</script>
