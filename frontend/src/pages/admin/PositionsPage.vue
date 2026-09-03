<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Должности</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <div v-if="positions.length" class="flex gap-3 mb-4">
      <input v-model="search" type="text" placeholder="Поиск по названию, категории..." class="input-field max-w-xs" />
    </div>

    <Modal v-model="modal" title="Должность" max-width="max-w-sm">
      <div class="space-y-3">
        <div>
          <label class="text-sm font-medium text-gray-700">Название (рус)</label>
          <input v-model="form.name" class="input-field mt-1" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-700">Название (каз)</label>
          <input v-model="form.name_kz" class="input-field mt-1" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-700">Категория</label>
          <input v-model="form.category" class="input-field mt-1" placeholder="Например: ИТР, рабочий" />
        </div>
      </div>
      <template #footer>
        <button @click="save" :disabled="saving" class="btn-primary">Сохранить</button>
        <button @click="modal = false" class="btn-secondary">Отмена</button>
      </template>
    </Modal>

    <div v-if="loading" class="text-gray-400 py-8 text-center">Загрузка...</div>

    <div v-else-if="!positions.length" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-2">🧑‍🔧</div>
      <div>Нет должностей. Добавьте первую.</div>
    </div>

    <div v-else-if="!filteredPositions.length" class="text-center py-16 text-gray-400">
      Ничего не найдено по этому запросу.
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">Название</th>
            <th class="text-left px-4 py-3">Категория</th>
            <th class="text-left px-4 py-3">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filteredPositions" :key="p.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3">{{ p.name }}</td>
            <td class="px-4 py-3 text-gray-500">{{ p.category }}</td>
            <td class="px-4 py-3">
              <Badge :variant="p.is_active ? 'passed' : 'failed'">{{ p.is_active ? 'Активна' : 'Неактивна' }}</Badge>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import Modal from '@/components/Modal.vue'
import Badge from '@/components/Badge.vue'

const toast = useToast()
const positions = ref([])
const search = ref('')
const modal = ref(false)

const filteredPositions = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return positions.value
  return positions.value.filter(p => p.name?.toLowerCase().includes(q) || p.category?.toLowerCase().includes(q))
})
const editing = ref(null)
const loading = ref(true)
const saving = ref(false)
const form = ref({ name: '', name_kz: '', category: '' })

onMounted(load)

async function load() {
  try {
    const { data } = await api.get('/admin/positions')
    positions.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: '', name_kz: '', category: '' }
  modal.value = true
}

async function save() {
  saving.value = true
  try {
    if (editing.value) {
      await api.patch(`/admin/positions/${editing.value.id}`, form.value)
    } else {
      await api.post('/admin/positions', form.value)
    }
    modal.value = false
    await load()
    toast.success(editing.value ? 'Изменения сохранены' : 'Должность добавлена')
  } catch (e) {
    toast.error(apiErrorMessage(e))
  } finally {
    saving.value = false
  }
}
</script>
