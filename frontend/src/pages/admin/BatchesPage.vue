<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Потоки обучения</h1>
      <button @click="showCreate = true" class="btn-primary">+ Новый поток</button>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-lg">
        <h2 class="font-semibold text-lg mb-4">Новый поток обучения</h2>
        <div class="space-y-4">
          <div>
            <label class="text-sm font-medium text-gray-700">Название потока</label>
            <input v-model="form.name" class="input-field mt-1" placeholder="Например: КазТрансОйл  май 2026" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700 block mb-2">Виды обучения</label>
            <div v-if="disciplines.length === 0" class="text-sm text-gray-400">Нет доступных дисциплин. Создайте их в разделе Дисциплины.</div>
            <div v-else class="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded p-3">
              <label v-for="d in disciplines" :key="d.id" class="flex items-center gap-3 cursor-pointer hover:bg-gray-50 p-1 rounded">
                <input type="checkbox" :value="d.id" v-model="form.discipline_ids" class="w-4 h-4 text-blue-600" />
                <span class="text-sm">{{ d.name }}</span>
                <span class="text-xs text-gray-400">({{ d.code }})</span>
              </label>
            </div>
            <div v-if="form.discipline_ids.length" class="mt-1 text-xs text-blue-600">
              Выбрано: {{ form.discipline_ids.length }}
            </div>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Примечание (необязательно)</label>
            <textarea v-model="form.notes" class="input-field mt-1" rows="2" placeholder="Любые заметки..."></textarea>
          </div>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="createBatch" :disabled="!form.name || !form.discipline_ids.length" class="btn-primary">Создать</button>
          <button @click="closeCreate" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!batches.length" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-2"></div>
      <div>Нет потоков. Создайте первый поток.</div>
    </div>

    <!-- Batches list -->
    <div class="space-y-3">
      <RouterLink v-for="b in batches" :key="b.id" :to="`/admin/batches/${b.id}`"
        class="card block hover:shadow-md transition-shadow">
        <div class="flex items-center justify-between">
          <div class="flex-1 min-w-0">
            <div class="font-semibold">{{ b.name }}</div>
            <div class="text-sm text-gray-400 mt-1">{{ formatDate(b.created_at) }}</div>
            <div v-if="b.discipline_names?.length" class="flex flex-wrap gap-1 mt-2">
              <span v-for="n in b.discipline_names" :key="n"
                class="text-xs px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full">{{ n }}</span>
            </div>
          </div>
          <span :class="statusBadge(b.status)" class="ml-4 px-3 py-1 rounded-full text-sm whitespace-nowrap">
            {{ statusLabel(b.status) }}
          </span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'

const batches = ref([])
const disciplines = ref([])
const showCreate = ref(false)
const form = ref({ name: '', discipline_ids: [], notes: '' })

onMounted(async () => {
  const [b, d] = await Promise.all([
    api.get('/admin/batches'),
    api.get('/admin/disciplines'),
  ])
  batches.value = b.data
  disciplines.value = d.data
})

async function createBatch() {
  await api.post('/admin/batches', {
    name: form.value.name,
    discipline_ids: form.value.discipline_ids,
    notes: form.value.notes || null,
  })
  closeCreate()
  const { data } = await api.get('/admin/batches')
  batches.value = data
}

function closeCreate() {
  showCreate.value = false
  form.value = { name: '', discipline_ids: [], notes: '' }
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: 'long', year: 'numeric' })
}

function statusBadge(s) {
  return {
    draft: 'bg-gray-100 text-gray-600',
    processing: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    archived: 'bg-red-100 text-red-600',
  }[s] || 'bg-gray-100'
}

function statusLabel(s) {
  return { draft: 'Черновик', processing: 'Обработка', completed: 'Завершён', archived: 'Архив' }[s] || s
}
</script>
