<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Правила назначения</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <div v-if="modal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-lg">
        <h2 class="font-semibold text-lg mb-4">{{ editing ? 'Изменить правило' : 'Новое правило' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium text-gray-700">Дисциплина</label>
            <select v-model="form.discipline_id" class="input-field mt-1">
              <option value="">— Выберите —</option>
              <option v-for="d in disciplines" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Ключевое слово должности (поиск по вхождению)</label>
            <input v-model="form.position_keyword" class="input-field mt-1" placeholder="Например: механик" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Курс</label>
            <select v-model="form.course_id" class="input-field mt-1">
              <option value="">— Выберите —</option>
              <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Приоритет (меньше = выше)</label>
            <input v-model.number="form.priority" type="number" class="input-field mt-1" />
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
            <th class="text-left px-4 py-3">Дисциплина</th>
            <th class="text-left px-4 py-3">Ключ. слово</th>
            <th class="text-left px-4 py-3">Курс</th>
            <th class="text-left px-4 py-3">Приоритет</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rules" :key="r.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3">{{ r.discipline?.name }}</td>
            <td class="px-4 py-3 font-mono">{{ r.position_keyword }}</td>
            <td class="px-4 py-3">{{ r.course?.name }}</td>
            <td class="px-4 py-3">{{ r.priority }}</td>
            <td class="px-4 py-3 flex gap-2">
              <button @click="openEdit(r)" class="text-blue-600 hover:underline text-xs">Изменить</button>
              <button @click="deleteRule(r.id)" class="text-red-500 hover:underline text-xs">Удалить</button>
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

const rules = ref([])
const disciplines = ref([])
const courses = ref([])
const modal = ref(false)
const editing = ref(null)
const form = ref({ discipline_id: '', position_keyword: '', course_id: '', priority: 10 })

onMounted(async () => {
  const [r, d, c] = await Promise.all([
    api.get('/admin/rules'),
    api.get('/admin/disciplines'),
    api.get('/admin/courses'),
  ])
  rules.value = r.data
  disciplines.value = d.data
  courses.value = c.data
})

function openCreate() {
  editing.value = null
  form.value = { discipline_id: '', position_keyword: '', course_id: '', priority: 10 }
  modal.value = true
}

function openEdit(r) {
  editing.value = r
  form.value = { discipline_id: r.discipline_id, position_keyword: r.position_keyword, course_id: r.course_id, priority: r.priority }
  modal.value = true
}

async function save() {
  if (editing.value) {
    await api.patch(`/admin/rules/${editing.value.id}`, form.value)
  } else {
    await api.post('/admin/rules', form.value)
  }
  modal.value = false
  const { data } = await api.get('/admin/rules')
  rules.value = data
}

async function deleteRule(id) {
  if (!confirm('Удалить правило?')) return
  await api.delete(`/admin/rules/${id}`)
  const { data } = await api.get('/admin/rules')
  rules.value = data
}
</script>
