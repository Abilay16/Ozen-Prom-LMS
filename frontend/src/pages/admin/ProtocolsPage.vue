<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Протоколы проверки знаний</h1>
      <router-link
        v-if="!isCommission"
        to="/admin/protocols/new"
        class="bg-brand-dark text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90"
      >
        + Новый протокол
      </router-link>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl shadow-sm p-4 mb-4 flex flex-wrap gap-3">
      <select v-model="filters.training_type_id" @change="load" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
        <option value="">Все типы</option>
        <option v-for="tt in trainingTypes" :key="tt.id" :value="tt.id">{{ tt.name_short }}</option>
      </select>
      <select v-model="filters.status" @change="load" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
        <option value="">Все статусы</option>
        <option value="draft">Черновик</option>
        <option value="awaiting_signatures">На подписи</option>
        <option value="signed">Подписан</option>
        <option value="archived">Архив</option>
      </select>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
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
          <tr v-if="loading">
            <td colspan="6" class="text-center py-8 text-gray-400">Загрузка...</td>
          </tr>
          <tr v-else-if="protocols.length === 0">
            <td colspan="6" class="text-center py-8 text-gray-400">Протоколов пока нет</td>
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
              <span class="px-2 py-0.5 rounded text-xs font-medium" :class="statusClass(p.status)">
                {{ statusLabel(p.status) }}
              </span>
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const isCommission = localStorage.getItem('is_commission') === '1'
const protocols = ref([])
const trainingTypes = ref([])
const loading = ref(true)
const filters = ref({ training_type_id: '', status: '' })

async function load() {
  loading.value = true
  try {
    const params = {}
    if (filters.value.training_type_id) params.training_type_id = filters.value.training_type_id
    if (filters.value.status) params.status = filters.value.status
    const res = await api.get('/admin/protocols', { params })
    protocols.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const [ttRes] = await Promise.all([api.get('/admin/training-types'), load()])
  trainingTypes.value = ttRes.data
})

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU')
}

function statusLabel(s) {
  return { draft: 'Черновик', awaiting_signatures: 'На подписи', signed: 'Подписан', archived: 'Архив' }[s] ?? s
}

function statusClass(s) {
  return {
    draft: 'bg-yellow-100 text-yellow-700',
    awaiting_signatures: 'bg-blue-100 text-blue-700',
    signed: 'bg-green-100 text-green-700',
    archived: 'bg-gray-100 text-gray-600',
  }[s] ?? 'bg-gray-100 text-gray-600'
}

function typeClass(code) {
  return {
    biot: 'bg-blue-100 text-blue-700',
    ptm: 'bg-orange-100 text-orange-700',
    prombez: 'bg-purple-100 text-purple-700',
  }[code] ?? 'bg-gray-100 text-gray-600'
}
</script>
