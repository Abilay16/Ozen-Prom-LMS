<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Дисциплины</h1>
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
      Архивные дисциплины не предлагаются для новых потоков. Сотрудники, которым они уже назначены,
      доучиваются как обычно; выданные удостоверения и сертификаты остаются действительными.
    </p>

    <div v-if="disciplines.length" class="flex gap-3 mb-4">
      <input v-model="search" type="text" placeholder="Поиск по коду, названию..." class="input-field max-w-xs" />
    </div>

    <Modal v-model="modal" title="Дисциплина" max-width="max-w-sm">
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
      <template #footer>
        <button @click="save" :disabled="saving" class="btn-primary">Сохранить</button>
        <button @click="modal = false" class="btn-secondary">Отмена</button>
      </template>
    </Modal>

    <RowsSkeleton v-if="loading" />

    <div v-else-if="!disciplines.length" class="text-center py-16 text-gray-400">
      <Tags class="w-10 h-10 mx-auto mb-2" aria-hidden="true" />
      <div>{{ view === 'active' ? 'Нет действующих дисциплин. Добавьте первую.' : 'В архиве пусто.' }}</div>
    </div>

    <div v-else-if="!filteredDisciplines.length" class="text-center py-16 text-gray-400">
      Ничего не найдено по этому запросу.
    </div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">Код</th>
            <th class="text-left px-4 py-3">Название</th>
            <th class="text-left px-4 py-3">Курсов</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in filteredDisciplines" :key="d.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-mono font-medium">{{ d.code }}</td>
            <td class="px-4 py-3">{{ d.name }}</td>
            <td class="px-4 py-3 tabular-nums">{{ d.course_count }}</td>
            <td class="px-4 py-3 flex gap-3 justify-end">
              <button @click="openEdit(d)" class="text-xs text-blue-600 hover:underline">Изменить</button>
              <button v-if="view === 'active'" @click="archive(d)" class="text-xs text-gray-500 hover:text-gray-800 hover:underline">В архив</button>
              <button v-else @click="restore(d)" class="text-xs text-green-600 hover:underline">Вернуть</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { Tags } from 'lucide-vue-next'
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
const disciplines = ref([])
const search = ref('')
const modal = ref(false)
const editing = ref(null)
const loading = ref(true)
const saving = ref(false)
const form = ref({ code: '', name: '' })

const filteredDisciplines = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return disciplines.value
  return disciplines.value.filter(d => d.code?.toLowerCase().includes(q) || d.name?.toLowerCase().includes(q))
})

onMounted(load)

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/disciplines', { params: { archived: view.value === 'archived' } })
    disciplines.value = data
  } finally {
    loading.value = false
  }
}

function switchView(v) {
  if (view.value === v) return
  view.value = v
  search.value = ''
  load()
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
  saving.value = true
  try {
    if (editing.value) {
      await api.patch(`/admin/disciplines/${editing.value.id}`, form.value)
    } else {
      await api.post('/admin/disciplines', form.value)
    }
    modal.value = false
    await load()
    toast.success(editing.value ? 'Изменения сохранены' : 'Дисциплина добавлена')
  } catch (e) {
    toast.error(apiErrorMessage(e))
  } finally {
    saving.value = false
  }
}

async function archive(d) {
  const ok = await confirm({
    message: `Убрать дисциплину «${d.name}» в архив? Её больше нельзя будет выбрать для нового потока. `
      + 'Кто уже учится — доучится, выданные удостоверения и сертификаты останутся действительными.',
    confirmText: 'В архив',
  })
  if (!ok) return
  try {
    await api.post(`/admin/disciplines/${d.id}/archive`)
  } catch (e) {
    toast.error(apiErrorMessage(e))
    return
  }
  await load()
  toast.success('Дисциплина в архиве')
}

async function restore(d) {
  try {
    await api.post(`/admin/disciplines/${d.id}/restore`)
  } catch (e) {
    toast.error(apiErrorMessage(e))
    return
  }
  await load()
  toast.success('Дисциплина снова действует')
}
</script>
