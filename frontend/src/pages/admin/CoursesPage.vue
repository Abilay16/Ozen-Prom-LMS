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
      <input v-model="search" type="text" placeholder="Поиск по названию..." class="input-field max-w-xs" />
    </div>

    <Modal v-model="modal" :title="editing ? 'Редактировать курс' : 'Новый курс'">
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
        <label v-if="editing" class="flex items-start gap-2 cursor-pointer">
          <input v-model="form.is_active" type="checkbox" class="mt-0.5" />
          <span class="text-sm text-gray-700">
            Активен
            <span class="block text-xs text-gray-400">Отключённый курс больше не назначается новым сотрудникам; история обучения сохраняется.</span>
          </span>
        </label>
      </div>
      <template #footer>
        <button @click="save" :disabled="saving" class="btn-primary">{{ editing ? 'Сохранить' : 'Создать' }}</button>
        <button @click="modal = false" class="btn-secondary">Отмена</button>
      </template>
    </Modal>

    <RowsSkeleton v-if="loading" />

    <div v-else-if="!courses.length" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-2">📚</div>
      <div>{{ filterDisc ? 'Нет курсов по выбранной дисциплине.' : 'Нет курсов. Добавьте первый курс.' }}</div>
    </div>

    <div v-else-if="!filteredCourses.length" class="text-center py-16 text-gray-400">
      Ничего не найдено по этому запросу.
    </div>

    <div v-else class="card overflow-x-auto">
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
          <tr v-for="c in filteredCourses" :key="c.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium" :class="{ 'text-gray-400': c.is_active === false }">
              {{ c.name }}
              <span v-if="c.is_active === false" class="ml-1 text-xs font-normal px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">отключён</span>
              <div v-if="c.target_positions" class="text-xs text-blue-500 mt-0.5">Должн.: {{ c.target_positions }}</div>
            </td>
            <td class="px-4 py-3">{{ c.discipline?.name }}</td>
            <td class="px-4 py-3 hidden md:table-cell">{{ c.duration_hours }}</td>
            <td class="px-4 py-3 flex gap-3">
              <RouterLink :to="`/admin/courses/${c.id}`" class="text-blue-600 hover:underline text-xs">Открыть</RouterLink>
              <button @click="openEdit(c)" class="text-gray-500 hover:underline text-xs">Изменить</button>
              <button @click="deleteCourse(c)" class="text-red-400 hover:text-red-600 hover:underline text-xs">Удалить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import Modal from '@/components/Modal.vue'
import RowsSkeleton from '@/components/RowsSkeleton.vue'

const toast = useToast()
const { confirm } = useConfirm()

const courses = ref([])
const disciplines = ref([])
const filterDisc = ref('')
const search = ref('')
const modal = ref(false)
const editing = ref(null)
const loading = ref(true)
const saving = ref(false)
const form = ref({ discipline_id: '', name: '', description: '', duration_hours: 8 })

const filteredCourses = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return courses.value
  return courses.value.filter(c => c.name?.toLowerCase().includes(q))
})

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/disciplines')
    disciplines.value = data
    await load()
  } finally {
    loading.value = false
  }
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
  form.value = { discipline_id: c.discipline_id, name: c.name, description: c.description || '', duration_hours: c.duration_hours, target_positions: c.target_positions || '', is_active: c.is_active !== false }
  modal.value = true
}

async function save() {
  saving.value = true
  try {
    if (editing.value) {
      await api.patch(`/admin/courses/${editing.value.id}`, form.value)
    } else {
      await api.post('/admin/courses', form.value)
    }
    modal.value = false
    await load()
    toast.success(editing.value ? 'Изменения сохранены' : 'Курс добавлен')
  } catch (e) {
    toast.error(apiErrorMessage(e))
  } finally {
    saving.value = false
  }
}

async function deleteCourse(c) {
  const ok = await confirm({ message: `Удалить курс «${c.name}» вместе с материалами и тестом?`, danger: true, confirmText: 'Удалить' })
  if (!ok) return
  try {
    await api.delete(`/admin/courses/${c.id}`)
  } catch (e) {
    // Например, курс уже назначен сотрудникам — сервер объясняет, что делать.
    toast.error(apiErrorMessage(e), 9000)
    return
  }
  await load()
  toast.success('Курс удалён')
}
</script>
