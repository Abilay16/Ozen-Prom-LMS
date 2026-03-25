<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Прогресс обучения</h1>

    <!-- Filters -->
    <div class="flex gap-3 flex-wrap mb-4">
      <select v-model="filters.organization_id" @change="load" class="input-field max-w-xs">
        <option value="">Все организации</option>
        <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
      </select>
      <select v-model="filters.batch_id" @change="load" class="input-field max-w-xs">
        <option value="">Все потоки</option>
        <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <select v-model="filters.status" @change="load" class="input-field max-w-xs">
        <option value="">Все статусы</option>
        <option value="assigned">Назначен</option>
        <option value="in_progress">В процессе</option>
        <option value="passed">Сдан</option>
        <option value="failed">Не сдан</option>
      </select>
    </div>

    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">ФИО</th>
            <th class="text-left px-4 py-3 hidden md:table-cell">Организация</th>
            <th class="text-left px-4 py-3">Дисциплина / Курс</th>
            <th class="text-left px-4 py-3">Статус</th>
            <th class="text-left px-4 py-3 hidden lg:table-cell">Лучший балл</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3">{{ row.user?.full_name }}</td>
            <td class="px-4 py-3 hidden md:table-cell text-gray-500">{{ row.user?.organization?.short_name }}</td>
            <td class="px-4 py-3">
              <div class="font-medium">{{ row.discipline?.name }}</div>
              <div class="text-xs text-gray-400">{{ row.course?.name }}</div>
            </td>
            <td class="px-4 py-3">
              <span :class="statusBadge(row.status)">{{ statusLabel(row.status) }}</span>
            </td>
            <td class="px-4 py-3 hidden lg:table-cell">{{ row.best_score != null ? row.best_score + '%' : '—' }}</td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="5" class="px-4 py-8 text-center text-gray-400">Нет данных</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const rows = ref([])
const organizations = ref([])
const batches = ref([])
const filters = ref({ organization_id: '', batch_id: '', status: '' })

onMounted(async () => {
  const [o, b] = await Promise.all([api.get('/admin/organizations'), api.get('/admin/batches')])
  organizations.value = o.data
  batches.value = b.data
  await load()
})

async function load() {
  const params = Object.fromEntries(Object.entries(filters.value).filter(([, v]) => v))
  const { data } = await api.get('/admin/progress', { params })
  rows.value = data
}

function statusLabel(s) {
  return { assigned: 'Назначен', in_progress: 'В процессе', passed: 'Сдан', failed: 'Не сдан' }[s] || s
}

function statusBadge(s) {
  return { assigned: 'badge-assigned', in_progress: 'badge-progress', passed: 'badge-passed', failed: 'badge-failed' }[s] || 'badge-assigned'
}
</script>
