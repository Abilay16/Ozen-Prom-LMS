<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Курсы</h1>
      <button v-if="view === 'active'" @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <div class="flex border-b mb-4" role="tablist">
      <button v-for="t in TABS" :key="t.key" role="tab" :aria-selected="view === t.key"
        @click="switchView(t.key)"
        :class="['px-4 py-2 text-sm font-medium -mb-px', view === t.key ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700']">
        {{ t.label }}
      </button>
    </div>

    <p v-if="view === 'archived'" class="text-sm text-gray-500 mb-4 max-w-2xl">
      Архивные курсы больше не назначаются новым сотрудникам. Кто уже учится — доучивается;
      материалы, тесты, результаты и выданные удостоверения сохраняются.
    </p>

    <!-- Filter -->
    <div class="flex gap-3 mb-4">
      <select v-model="filterDisc" @change="load" class="input-field max-w-xs">
        <option value="">Все дисциплины</option>
        <option v-for="d in filterDisciplines" :key="d.id" :value="d.id">{{ d.name }}{{ d.is_active ? '' : ' (архив)' }}</option>
      </select>
      <input v-model="search" type="text" placeholder="Поиск по названию..." class="input-field max-w-xs" />
    </div>

    <Modal v-model="modal" :title="editing ? 'Редактировать курс' : 'Новый курс'">
      <div class="space-y-3">
        <div v-if="!editing">
          <label class="text-sm font-medium text-gray-700">Дисциплина</label>
          <select v-model="form.discipline_id" class="input-field mt-1">
            <option value="">— Выберите —</option>
            <option v-for="d in disciplines" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </div>
        <div v-else class="text-sm">
          <span class="text-gray-500">Дисциплина:</span> {{ editing.discipline?.name || '—' }}
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
      <template #footer>
        <button @click="save" :disabled="saving" class="btn-primary">{{ editing ? 'Сохранить' : 'Создать' }}</button>
        <button @click="modal = false" class="btn-secondary">Отмена</button>
      </template>
    </Modal>

    <RowsSkeleton v-if="loading" />

    <div v-else-if="!courses.length" class="text-center py-16 text-gray-400">
      <BookOpen class="w-10 h-10 mx-auto mb-2" aria-hidden="true" />
      <div v-if="filterDisc">Нет курсов по выбранной дисциплине.</div>
      <div v-else>{{ view === 'active' ? 'Нет действующих курсов. Добавьте первый курс.' : 'В архиве пусто.' }}</div>
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
            <td class="px-4 py-3 font-medium">
              {{ c.name }}
              <div v-if="c.target_positions" class="text-xs text-blue-500 mt-0.5">Должн.: {{ c.target_positions }}</div>
            </td>
            <td class="px-4 py-3">
              {{ c.discipline?.name }}
              <span v-if="c.discipline && !c.discipline.is_active" class="ml-1 text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">в архиве</span>
            </td>
            <td class="px-4 py-3 hidden md:table-cell">{{ c.duration_hours }}</td>
            <td class="px-4 py-3 flex gap-3 justify-end">
              <RouterLink :to="`/admin/courses/${c.id}`" class="text-blue-600 hover:underline text-xs">Открыть</RouterLink>
              <button @click="openEdit(c)" class="text-gray-500 hover:underline text-xs">Изменить</button>
              <template v-if="view === 'active'">
                <button @click="setArchived(c, true)" class="text-gray-500 hover:text-gray-800 hover:underline text-xs">В архив</button>
                <button @click="deleteCourse(c)" class="text-red-400 hover:text-red-600 hover:underline text-xs">Удалить</button>
              </template>
              <button v-else-if="c.discipline?.is_active" @click="setArchived(c, false)" class="text-green-600 hover:underline text-xs">Вернуть</button>
              <span v-else class="text-xs text-gray-400" title="Сначала верните дисциплину из архива">дисциплина в архиве</span>
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
import { BookOpen } from 'lucide-vue-next'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import Modal from '@/components/Modal.vue'
import RowsSkeleton from '@/components/RowsSkeleton.vue'

const TABS = [
  { key: 'active', label: 'Действующие' },
  { key: 'archived', label: 'Архив' },
]

const toast = useToast()
const { confirm } = useConfirm()

const view = ref('active')
const courses = ref([])
const disciplines = ref([])          // действующие — для нового курса
const archivedDisciplines = ref([])  // для фильтра во вкладке «Архив»
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

// В архиве лежат и отключённые курсы действующих дисциплин, поэтому там
// фильтр предлагает все дисциплины.
const filterDisciplines = computed(() =>
  view.value === 'active' ? disciplines.value : [...disciplines.value, ...archivedDisciplines.value])

onMounted(async () => {
  try {
    const [active, archived] = await Promise.all([
      api.get('/admin/disciplines'),
      api.get('/admin/disciplines', { params: { archived: true } }),
    ])
    disciplines.value = active.data
    archivedDisciplines.value = archived.data
    await load()
  } finally {
    loading.value = false
  }
})

async function load() {
  const params = { archived: view.value === 'archived' }
  if (filterDisc.value) params.discipline_id = filterDisc.value
  const { data } = await api.get('/admin/courses', { params })
  courses.value = data
}

async function switchView(v) {
  if (view.value === v) return
  view.value = v
  search.value = ''
  if (!filterDisciplines.value.some(d => d.id === filterDisc.value)) filterDisc.value = ''
  loading.value = true
  try { await load() } finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { discipline_id: '', name: '', description: '', duration_hours: 8, target_positions: '' }
  modal.value = true
}

function openEdit(c) {
  editing.value = c
  form.value = { name: c.name, description: c.description || '', duration_hours: c.duration_hours, target_positions: c.target_positions || '' }
  modal.value = true
}

async function setArchived(c, archived) {
  if (archived) {
    const ok = await confirm({
      message: `Убрать курс «${c.name}» в архив? Новым сотрудникам он больше не назначится. `
        + 'Кто уже учится — доучится; результаты и удостоверения сохранятся.',
      confirmText: 'В архив',
    })
    if (!ok) return
  }
  try {
    await api.patch(`/admin/courses/${c.id}`, { is_active: !archived })
  } catch (e) {
    toast.error(apiErrorMessage(e))
    return
  }
  await load()
  toast.success(archived ? 'Курс в архиве' : 'Курс снова действует')
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
