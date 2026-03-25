<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Должности</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <div v-if="modal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-sm">
        <h2 class="font-semibold text-lg mb-4">Должность</h2>
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
        <div class="flex gap-3 mt-4">
          <button @click="save" class="btn-primary">Сохранить</button>
          <button @click="modal = false" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">Название</th>
            <th class="text-left px-4 py-3">Категория</th>
            <th class="text-left px-4 py-3">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in positions" :key="p.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3">{{ p.name }}</td>
            <td class="px-4 py-3 text-gray-500">{{ p.category }}</td>
            <td class="px-4 py-3">
              <span :class="p.is_active ? 'badge-passed' : 'badge-failed'">{{ p.is_active ? 'Активна' : 'Неактивна' }}</span>
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

const positions = ref([])
const modal = ref(false)
const editing = ref(null)
const form = ref({ name: '', name_kz: '', category: '' })

onMounted(load)

async function load() {
  const { data } = await api.get('/admin/positions')
  positions.value = data
}

function openCreate() {
  editing.value = null
  form.value = { name: '', name_kz: '', category: '' }
  modal.value = true
}

async function save() {
  if (editing.value) {
    await api.patch(`/admin/positions/${editing.value.id}`, form.value)
  } else {
    await api.post('/admin/positions', form.value)
  }
  modal.value = false
  await load()
}
</script>
