<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Дашборд</h1>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="card text-center">
        <div class="text-3xl font-bold text-brand-mid">{{ stats.users }}</div>
        <div class="text-sm text-gray-500 mt-1">Пользователей</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-brand-mid">{{ stats.batches }}</div>
        <div class="text-sm text-gray-500 mt-1">Потоков</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-green-600">{{ stats.passed }}</div>
        <div class="text-sm text-gray-500 mt-1">Сдали</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-yellow-500">{{ stats.inProgress }}</div>
        <div class="text-sm text-gray-500 mt-1">В процессе</div>
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

const stats = ref({ users: 0, batches: 0, passed: 0, inProgress: 0 })

onMounted(async () => {
  try {
    const [usersRes, batchesRes, progressRes] = await Promise.all([
      api.get('/admin/users?limit=1'),
      api.get('/admin/batches'),
      api.get('/admin/progress?limit=500'),
    ])
    stats.value.batches = batchesRes.data.length || 0
    const progress = progressRes.data || []
    stats.value.passed = progress.filter(a => a.status === 'passed').length
    stats.value.inProgress = progress.filter(a => a.status === 'in_progress').length
  } catch {}
})
</script>
