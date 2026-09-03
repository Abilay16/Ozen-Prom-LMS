<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Дашборд</h1>

    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      <div class="card text-center">
        <div class="text-3xl font-bold text-brand-mid">{{ loading ? '—' : stats.users }}</div>
        <div class="text-sm text-gray-500 mt-1">Пользователей</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-brand-mid">{{ loading ? '—' : stats.batches }}</div>
        <div class="text-sm text-gray-500 mt-1">Потоков</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-green-600">{{ loading ? '—' : stats.passed }}</div>
        <div class="text-sm text-gray-500 mt-1">Сдали</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-yellow-500">{{ loading ? '—' : stats.inProgress }}</div>
        <div class="text-sm text-gray-500 mt-1">В процессе</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-red-500">{{ loading ? '—' : stats.failed }}</div>
        <div class="text-sm text-gray-500 mt-1">Не сдали</div>
      </div>
    </div>

    <div class="card">
      <h2 class="font-semibold mb-4">Быстрые действия</h2>
      <div class="flex flex-wrap gap-3">
        <RouterLink to="/admin/batches" class="btn-primary text-sm">+ Новый поток обучения</RouterLink>
        <RouterLink to="/admin/courses" class="btn-secondary text-sm">Управление курсами</RouterLink>
        <RouterLink to="/admin/exports" class="btn-secondary text-sm">Выгрузить отчёт</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const stats = ref({ users: 0, batches: 0, passed: 0, inProgress: 0, failed: 0 })
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/progress/stats')
    stats.value.users = data.users || 0
    stats.value.batches = data.batches || 0
    stats.value.passed = data.passed || 0
    stats.value.inProgress = data.in_progress || 0
    stats.value.failed = data.failed || 0
  } catch {
    toast.error('Не удалось загрузить статистику')
  } finally {
    loading.value = false
  }
})
</script>
