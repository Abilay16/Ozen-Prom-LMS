<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Дисциплины</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <div v-if="modal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-sm">
        <h2 class="font-semibold text-lg mb-4">Дисциплина</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium text-gray-700">Код (напр. BIOT)</label>
            <input v-model="form.code" class="input-field mt-1 uppercase" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Название (напр. БиОТ)</label>
            <input v-model="form.name" class="input-field mt-1" />
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
            <th class="text-left px-4 py-3">Код</th>
            <th class="text-left px-4 py-3">Название</th>
            <th class="text-left px-4 py-3">Статус</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in disciplines" :key="d.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-mono font-medium">{{ d.code }}</td>
            <td class="px-4 py-3">{{ d.name }}</td>
            <td class="px-4 py-3">
              <span :class="d.is_active ? 'badge-passed' : 'badge-failed'">{{ d.is_active ? 'Активна' : 'Неактивна' }}</span>
            </td>
            <td class="px-4 py-3 flex gap-3">
              <button @click="openEdit(d)" class="text-xs text-blue-600 hover:underline">Изменить</button>
              <button @click="deleteDisc(d)" class="text-xs text-red-400 hover:text-red-600 hover:underline">Удалить</button>
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

const disciplines = ref([])
const modal = ref(false)
const editing = ref(null)
const form = ref({ code: '', name: '' })

onMounted(load)

async function load() {
  const { data } = await api.get('/admin/disciplines')
  disciplines.value = data
}

function openCreate() {
  editing.value = null
  form.value = { code: '', name: '' }
  modal.value = true
}

function openEdit(d) {
  editing.value = d
  form.value = { code: d.code, name: d.name }
  modal.value = true
}

async function save() {
  if (editing.value) {
    await api.patch(`/admin/disciplines/${editing.value.id}`, form.value)
  } else {
    await api.post('/admin/disciplines', form.value)
  }
  modal.value = false
  await load()
}

async function deleteDisc(d) {
  if (!confirm(`Удалить дисциплину "${d.name}"?`)) return
  await api.delete(`/admin/disciplines/${d.id}`)
  await load()
}
</script>
