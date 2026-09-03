<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Дисциплины</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

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

    <div v-if="loading" class="text-gray-400 py-8 text-center">Загрузка...</div>

    <div v-else-if="!disciplines.length" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-2">🏷️</div>
      <div>Нет дисциплин. Добавьте первую.</div>
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
            <th class="text-left px-4 py-3">Статус</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in filteredDisciplines" :key="d.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-mono font-medium">{{ d.code }}</td>
            <td class="px-4 py-3">{{ d.name }}</td>
            <td class="px-4 py-3">
              <Badge :variant="d.is_active ? 'passed' : 'failed'">{{ d.is_active ? 'Активна' : 'Неактивна' }}</Badge>
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
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import Modal from '@/components/Modal.vue'
import Badge from '@/components/Badge.vue'

const toast = useToast()
const { confirm } = useConfirm()

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
  try {
    const { data } = await api.get('/admin/disciplines')
    disciplines.value = data
  } finally {
    loading.value = false
  }
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

async function deleteDisc(d) {
  const ok = await confirm({ message: `Удалить дисциплину «${d.name}»?`, danger: true, confirmText: 'Удалить' })
  if (!ok) return
  await api.delete(`/admin/disciplines/${d.id}`)
  await load()
  toast.success('Дисциплина удалена')
}
</script>
