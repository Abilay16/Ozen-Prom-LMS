<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Удостоверения</h1>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl shadow-sm p-4 mb-4 flex flex-wrap gap-3">
      <input v-model="search" @input="debouncedLoad" placeholder="Поиск по ФИО или номеру..." class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64" />
      <select v-model="filters.training_type_id" @change="list.reload()" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
        <option value="">Все типы</option>
        <option v-for="tt in trainingTypes" :key="tt.id" :value="tt.id">{{ tt.name_short }}</option>
      </select>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl shadow-sm overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-600">№ удостоверения</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">ФИО</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Тип</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Организация</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Выдано</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">До</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="list.loading.value">
            <td colspan="7" class="py-2"><RowsSkeleton :rows="3" /></td>
          </tr>
          <tr v-else-if="certs.length === 0">
            <td colspan="7" class="text-center py-8 text-gray-400">{{ search || filters.training_type_id ? 'Ничего не найдено по этому запросу.' : 'Удостоверений пока нет' }}</td>
          </tr>
          <tr
            v-for="c in certs"
            :key="c.id"
            class="border-t border-gray-100 hover:bg-gray-50"
          >
            <td class="px-4 py-3 font-mono text-xs text-gray-700">{{ c.certificate_number }}</td>
            <td class="px-4 py-3 font-medium text-gray-900">{{ c.full_name }}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 rounded text-xs font-medium" :class="typeClass(c.training_type?.code)">
                {{ c.training_type?.name_short ?? '—' }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-600 text-xs">{{ c.organization_name ?? '—' }}</td>
            <td class="px-4 py-3 text-gray-600">{{ formatDate(c.issued_date) }}</td>
            <td class="px-4 py-3" :class="isExpired(c.valid_until) ? 'text-red-600' : isExpiringSoon(c.valid_until) ? 'text-orange-500' : 'text-gray-600'">
              {{ formatDate(c.valid_until) }}
              <span v-if="isExpired(c.valid_until)" class="text-xs ml-1">(истекло)</span>
              <span v-else-if="isExpiringSoon(c.valid_until)" class="text-xs ml-1">(скоро)</span>
            </td>
            <td class="px-4 py-3 text-right">
              <router-link :to="`/admin/certificates/${c.id}`" class="text-blue-600 hover:underline text-xs">📄 Просмотреть</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <LoadMore :shown="certs.length" :total="list.total.value" :loading="list.loadingMore.value" @more="list.loadMore()" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import RowsSkeleton from '@/components/RowsSkeleton.vue'
import LoadMore from '@/components/LoadMore.vue'
import { usePagedList } from '@/composables/usePagedList'

const trainingTypes = ref([])
const search = ref('')
const filters = ref({ training_type_id: '' })
let debounceTimer = null

const list = usePagedList('/admin/certificates', () => ({
  search: search.value.trim(),
  training_type_id: filters.value.training_type_id,
}))
const certs = list.items

function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => list.reload(), 350)
}

onMounted(async () => {
  list.reload()
  try {
    trainingTypes.value = (await api.get('/admin/training-types')).data
  } catch {}
})

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU')
}

function isExpired(d) {
  if (!d) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return new Date(d + 'T00:00:00') < today
}

function isExpiringSoon(d) {
  if (!d) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expires = new Date(d + 'T00:00:00')
  const diff = expires - today
  return diff >= 0 && diff < 90 * 24 * 60 * 60 * 1000 // 90 days
}

function typeClass(code) {
  return {
    biot: 'bg-blue-100 text-blue-700',
    ptm: 'bg-orange-100 text-orange-700',
    prombez: 'bg-purple-100 text-purple-700',
  }[code] ?? 'bg-gray-100 text-gray-600'
}
</script>
