<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Правила назначения</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <div v-if="rules.length" class="flex gap-3 mb-4">
      <input v-model="search" type="text" placeholder="Поиск по дисциплине, курсу, ключ. слову..." class="input-field max-w-xs" />
    </div>

    <Modal v-model="modal" :title="editing ? 'Изменить правило' : 'Новое правило'">
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
      <template #footer>
        <button @click="save" :disabled="saving" class="btn-primary">{{ editing ? 'Сохранить' : 'Создать' }}</button>
        <button @click="modal = false" class="btn-secondary">Отмена</button>
      </template>
    </Modal>

    <div v-if="loading" class="text-gray-400 py-8 text-center">Загрузка...</div>

    <div v-else-if="!rules.length" class="text-center py-16 text-gray-400">
      <div class="text-4xl mb-2">🧩</div>
      <div>Нет правил. Добавьте первое, чтобы курсы назначались автоматически.</div>
    </div>

    <div v-else-if="!filteredRules.length" class="text-center py-16 text-gray-400">
      Ничего не найдено по этому запросу.
    </div>

    <div v-else class="card overflow-x-auto">
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
          <tr v-for="r in filteredRules" :key="r.id" class="border-b hover:bg-gray-50">
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
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import Modal from '@/components/Modal.vue'

const toast = useToast()
const { confirm } = useConfirm()

const rules = ref([])
const disciplines = ref([])
const courses = ref([])
const search = ref('')
const modal = ref(false)

const filteredRules = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return rules.value
  return rules.value.filter(r =>
    r.discipline?.name?.toLowerCase().includes(q) ||
    r.course?.name?.toLowerCase().includes(q) ||
    r.position_keyword?.toLowerCase().includes(q)
  )
})
const editing = ref(null)
const loading = ref(true)
const saving = ref(false)
const form = ref({ discipline_id: '', position_keyword: '', course_id: '', priority: 10 })

onMounted(async () => {
  try {
    const [r, d, c] = await Promise.all([
      api.get('/admin/rules'),
      api.get('/admin/disciplines'),
      api.get('/admin/courses'),
    ])
    rules.value = r.data
    disciplines.value = d.data
    courses.value = c.data
  } finally {
    loading.value = false
  }
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
  saving.value = true
  try {
    if (editing.value) {
      await api.patch(`/admin/rules/${editing.value.id}`, form.value)
    } else {
      await api.post('/admin/rules', form.value)
    }
    modal.value = false
    const { data } = await api.get('/admin/rules')
    rules.value = data
    toast.success(editing.value ? 'Изменения сохранены' : 'Правило добавлено')
  } catch (e) {
    toast.error(apiErrorMessage(e))
  } finally {
    saving.value = false
  }
}

async function deleteRule(id) {
  const ok = await confirm({ message: 'Удалить правило?', danger: true, confirmText: 'Удалить' })
  if (!ok) return
  await api.delete(`/admin/rules/${id}`)
  const { data } = await api.get('/admin/rules')
  rules.value = data
  toast.success('Правило удалено')
}
</script>
