<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Протоколы проверки знаний</h1>
      <router-link
        v-if="canEdit"
        to="/admin/protocols/new"
        class="bg-brand-dark text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90"
      >
        + Новый протокол
      </router-link>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl shadow-sm p-4 mb-4 flex flex-wrap gap-3">
      <input v-model="search" @input="debouncedLoad" type="text" placeholder="Поиск по № протокола, организации..." class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64" />
      <select v-model="filters.training_type_id" @change="list.reload()" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
        <option value="">Все типы</option>
        <option v-for="tt in trainingTypes" :key="tt.id" :value="tt.id">{{ tt.name_short }}</option>
      </select>
      <select v-model="filters.status" @change="list.reload()" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
        <option value="">Все статусы</option>
        <option value="draft">Черновик</option>
        <option value="awaiting_signatures">На подписи</option>
        <option value="signed">Подписан</option>
        <option value="archived">Архив</option>
      </select>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl shadow-sm overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-600">№ протокола</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Тип</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Организация</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Дата экзамена</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Статус</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="list.loading.value">
            <td colspan="6" class="py-2"><RowsSkeleton :rows="3" /></td>
          </tr>
          <tr v-else-if="protocols.length === 0">
            <td colspan="6" class="text-center py-8 text-gray-400">
              {{ search || filters.status || filters.training_type_id ? 'Ничего не найдено по этому запросу.' : 'Протоколов пока нет' }}
            </td>
          </tr>
          <tr
            v-for="p in protocols"
            :key="p.id"
            class="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
            @click="$router.push(`/admin/protocols/${p.id}`)"
          >
            <td class="px-4 py-3 font-medium text-gray-900">{{ p.protocol_number }}</td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 rounded text-xs font-medium" :class="typeClass(p.training_type?.code)">
                {{ p.training_type?.name_short ?? '—' }}
              </span>
            </td>
            <td class="px-4 py-3 text-gray-600">{{ p.organization?.name ?? '—' }}</td>
            <td class="px-4 py-3 text-gray-600">{{ formatDate(p.exam_date) }}</td>
            <td class="px-4 py-3">
              <Badge :variant="statusVariant(p.status)">{{ statusLabel(p.status) }}</Badge>
            </td>
            <td class="px-4 py-3 text-right" @click.stop>
              <router-link
                :to="`/admin/protocols/${p.id}`"
                class="text-blue-600 hover:underline text-xs mr-3"
              >Открыть</router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <LoadMore :shown="protocols.length" :total="list.total.value" :loading="list.loadingMore.value" @more="list.loadMore()" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import Badge from '@/components/Badge.vue'
import RowsSkeleton from '@/components/RowsSkeleton.vue'
import LoadMore from '@/components/LoadMore.vue'
import { useRole } from '@/composables/useRole'
import { usePagedList } from '@/composables/usePagedList'

const { canEdit } = useRole()
const trainingTypes = ref([])
const search = ref('')
const filters = ref({ training_type_id: '', status: '' })
let debounceTimer = null

// Поиск — на сервере: раньше искали только среди 50 загруженных протоколов.
const list = usePagedList('/admin/protocols', () => ({
  search: search.value.trim(),
  training_type_id: filters.value.training_type_id,
  status: filters.value.status,
}))
const protocols = list.items

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

function statusLabel(s) {
  return { draft: 'Черновик', awaiting_signatures: 'На подписи', signed: 'Подписан', archived: 'Архив' }[s] ?? s
}

function statusVariant(s) {
  return {
    draft: 'progress',
    awaiting_signatures: 'assigned',
    signed: 'passed',
    archived: 'neutral',
  }[s] ?? 'neutral'
}

function typeClass(code) {
  return {
    biot: 'bg-blue-100 text-blue-700',
    ptm: 'bg-orange-100 text-orange-700',
    prombez: 'bg-purple-100 text-purple-700',
  }[code] ?? 'bg-gray-100 text-gray-600'
}
</script>
