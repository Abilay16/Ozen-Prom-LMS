<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Прогресс обучения</h1>

    <!-- Filters -->
    <div class="flex gap-3 flex-wrap mb-4">
      <input
        v-model="filters.search"
        @input="debouncedLoad"
        placeholder="Поиск по ФИО..."
        class="input-field max-w-xs"
      />
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
      <div class="flex items-center gap-1">
        <span class="text-sm text-gray-500">Дата:</span>
        <input type="date" v-model="filters.date_from" @change="load" class="input-field text-sm" style="width:150px" />
        <span class="text-gray-400">—</span>
        <input type="date" v-model="filters.date_to" @change="load" class="input-field text-sm" style="width:150px" />
      </div>
      <button @click="resetFilters" class="btn-secondary text-sm">Сброс</button>
    </div>


    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">ФИО</th>
            <th class="text-left px-4 py-3">Организация</th>
            <th class="text-left px-4 py-3">Должность</th>
            <th class="text-left px-4 py-3">Дисциплина / Курс</th>
            <th class="text-left px-4 py-3">Статус</th>
            <th class="text-left px-4 py-3">Результат</th>
            <th class="text-left px-4 py-3">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ row.user?.full_name }}</td>
            <td class="px-4 py-3 text-gray-500 text-xs">{{ row.user?.organization_name || '—' }}</td>
            <td class="px-4 py-3 text-gray-500 text-xs">{{ row.user?.position_raw || '—' }}</td>
            <td class="px-4 py-3">
              <div class="font-medium">{{ row.discipline?.name }}</div>
              <div class="text-xs text-gray-400">{{ row.course?.name }}</div>
            </td>
            <td class="px-4 py-3">
              <Badge :variant="statusVariant(row.status)">{{ statusLabel(row.status) }}</Badge>
            </td>
            <td class="px-4 py-3">
              <span v-if="row.best_score != null"
                :class="row.best_passed ? 'text-green-600 font-bold' : 'text-red-500 font-bold'">
                {{ row.best_score }}%
              </span>
              <span v-else class="text-gray-300">—</span>
            </td>
            <td class="px-4 py-3">
              <button
                v-if="canEdit && (row.status === 'failed' || row.status === 'in_progress')"
                @click="allowRetake(row.id)"
                class="text-xs bg-orange-100 text-orange-700 hover:bg-orange-200 px-2 py-1 rounded font-medium"
              >↺ Пересдача</button>
              <span v-else class="text-gray-300 text-xs">—</span>
            </td>
          </tr>
          <tr v-if="!rows.length && !loading">
            <td colspan="7" class="px-4 py-8 text-center text-gray-400">Нет данных</td>
          </tr>
          <tr v-if="loading">
            <td colspan="7" class="py-2"><RowsSkeleton :rows="3" /></td>
          </tr>
        </tbody>
      </table>
      <LoadMore :shown="rows.length" :total="list.total.value" :loading="list.loadingMore.value" @more="list.loadMore()" />
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import Badge from '@/components/Badge.vue'
import RowsSkeleton from '@/components/RowsSkeleton.vue'
import LoadMore from '@/components/LoadMore.vue'
import { usePagedList } from '@/composables/usePagedList'
import { useRole } from '@/composables/useRole'

const toast = useToast()
const { canEdit } = useRole()
const { confirm } = useConfirm()

const organizations = ref([])
const batches = ref([])
const filters = ref({ search: '', organization_id: '', batch_id: '', status: '', date_from: '', date_to: '' })

const list = usePagedList('/admin/progress', () => ({ ...filters.value, search: filters.value.search.trim() }), { pageSize: 100 })
const rows = list.items
const loading = list.loading

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 350)
}

onMounted(async () => {
  load()
  // Справочники для фильтров: ошибка в них не должна ломать сам список.
  const [o, b] = await Promise.allSettled([api.get('/admin/organizations'), api.get('/admin/batches')])
  if (o.status === 'fulfilled') organizations.value = o.value.data
  if (b.status === 'fulfilled') batches.value = b.value.data
})

function load() {
  return list.reload()
}

function resetFilters() {
  filters.value = { search: '', organization_id: '', batch_id: '', status: '', date_from: '', date_to: '' }
  load()
}

function statusLabel(s) {
  return { assigned: 'Назначен', in_progress: 'В процессе', passed: 'Сдан', failed: 'Не сдан' }[s] || s
}

function statusVariant(s) {
  return {
    assigned: 'neutral',
    in_progress: 'assigned',
    passed: 'passed',
    failed: 'failed',
  }[s] || 'neutral'
}

async function allowRetake(assignmentId) {
  const ok = await confirm({ message: 'Разрешить пересдачу? Все предыдущие попытки будут сброшены.', danger: true, confirmText: 'Разрешить' })
  if (!ok) return
  try {
    await api.post(`/admin/progress/${assignmentId}/allow-retake`)
    await load()
    toast.success('Пересдача разрешена')
  } catch (e) {
    toast.error(apiErrorMessage(e))
  }
}
</script>

