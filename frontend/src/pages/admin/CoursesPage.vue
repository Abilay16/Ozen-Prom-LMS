<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Курсы</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <!-- Filter -->
    <div class="flex gap-3 mb-4">
      <select v-model="filterDisc" @change="load" class="input-field max-w-xs">
        <option value="">Все дисциплины</option>
        <option v-for="d in disciplines" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
    </div>

    <!-- Modal -->
    <div v-if="modal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-lg">
        <h2 class="font-semibold text-lg mb-4">{{ editing ? 'Редактировать курс' : 'Новый курс' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium text-gray-700">Дисциплина</label>
            <select v-model="form.discipline_id" class="input-field mt-1">
              <option value="">— Выберите —</option>
              <option v-for="d in disciplines" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Название курса</label>
            <input v-model="form.name" class="input-field mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Описание</label>
            <textarea v-model="form.description" rows="3" class="input-field mt-1"></textarea>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Длительность (ч)</label>
            <input v-model.number="form.duration_hours" type="number" class="input-field mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Целевые должности</label>
            <input v-model="form.target_positions" class="input-field mt-1" placeholder="водитель, слесарь, электрик (через запятую)" />
            <p class="text-xs text-gray-400 mt-1">Если поставить пустым — курс достанется всем, кому не подошёл другой курс</p>
          </div>
        </div>
        <div class="flex gap-3 mt-4">
          <button @click="save" class="btn-primary">{{ editing ? 'Сохранить' : 'Создать' }}</button>
          <button @click="modal = false" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">Название</th>
            <th class="text-left px-4 py-3">Дисциплина</th>
            <th class="text-left px-4 py-3 hidden md:table-cell">Длит. (ч)</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in courses" :key="c.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">
              {{ c.name }}
              <div v-if="c.target_positions" class="text-xs text-blue-500 mt-0.5">Должн.: {{ c.target_positions }}</div>
            </td>
            <td class="px-4 py-3">{{ c.discipline?.name }}</td>
            <td class="px-4 py-3 hidden md:table-cell">{{ c.duration_hours }}</td>
            <td class="px-4 py-3 flex gap-3">
              <RouterLink :to="`/admin/courses/${c.id}`" class="text-blue-600 hover:underline text-xs">Открыть</RouterLink>
              <button @click="openEdit(c)" class="text-gray-500 hover:underline text-xs">Изменить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'

const courses = ref([])
const disciplines = ref([])
const filterDisc = ref('')
const modal = ref(false)
const editing = ref(null)
const form = ref({ discipline_id: '', name: '', description: '', duration_hours: 8 })

onMounted(async () => {
  const { data } = await api.get('/admin/disciplines')
  disciplines.value = data
  await load()
})

async function load() {
  const params = filterDisc.value ? { discipline_id: filterDisc.value } : {}
  const { data } = await api.get('/admin/courses', { params })
  courses.value = data
}

function openCreate() {
  editing.value = null
  form.value = { discipline_id: '', name: '', description: '', duration_hours: 8, target_positions: '' }
  modal.value = true
}

function openEdit(c) {
  editing.value = c
  form.value = { discipline_id: c.discipline_id, name: c.name, description: c.description || '', duration_hours: c.duration_hours, target_positions: c.target_positions || '' }
  modal.value = true
}

async function save() {
  if (editing.value) {
    await api.patch(`/admin/courses/${editing.value.id}`, form.value)
  } else {
    await api.post('/admin/courses', form.value)
  }
  modal.value = false
  await load()
}
</script>
