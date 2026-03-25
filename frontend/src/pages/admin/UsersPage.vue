<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Пользователи</h1>
    </div>
    <div class="card">
      <div class="flex gap-4 mb-4">
        <input v-model="search" type="text" placeholder="Поиск по ФИО..." class="input-field max-w-xs" />
      </div>
      <div v-if="loading" class="text-gray-400 py-8 text-center">Загрузка...</div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 text-left">
            <th class="py-3 font-semibold text-gray-600">ФИО</th>
            <th class="py-3 font-semibold text-gray-600">Логин</th>
            <th class="py-3 font-semibold text-gray-600">Должность</th>
            <th class="py-3 font-semibold text-gray-600">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-gray-100 hover:bg-gray-50">
            <td class="py-3">{{ u.full_name }}</td>
            <td class="py-3 font-mono text-gray-500">{{ u.login }}</td>
            <td class="py-3 text-gray-500">{{ u.position_raw || '—' }}</td>
            <td class="py-3">
              <span :class="u.is_active ? 'badge-passed' : 'badge-failed'">
                {{ u.is_active ? 'Активен' : 'Неактивен' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'
const users = ref([])
const loading = ref(true)
const search = ref('')
async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/users', { params: { search: search.value || undefined } })
    users.value = data
  } finally { loading.value = false }
}
onMounted(load)
watch(search, () => setTimeout(load, 300))
</script>
