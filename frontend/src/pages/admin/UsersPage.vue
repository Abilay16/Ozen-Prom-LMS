<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Пользователи</h1>
    </div>
    <div class="card">
      <div class="flex gap-4 mb-4">
        <input v-model="search" type="text" placeholder="Поиск по ФИО..." class="input-field max-w-xs" />
      </div>
      <div v-if="loading" class="text-gray-400 py-8 text-center">Загрузка...</div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 text-left">
            <th class="py-3 px-2 font-semibold text-gray-600">ФИО</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Логин</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Пароль</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Должность</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Статус</th>
            <th class="py-3 px-2 font-semibold text-gray-600"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-gray-100 hover:bg-gray-50">
            <td class="py-3 px-2">{{ u.full_name }}</td>
            <td class="py-3 px-2 font-mono text-gray-500">{{ u.login }}</td>
            <td class="py-3 px-2">
              <span v-if="u.plain_password" class="font-mono text-gray-700">{{ u.plain_password }}</span>
              <span v-else class="text-gray-300 text-xs italic">не задан</span>
            </td>
            <td class="py-3 px-2 text-gray-500">{{ u.position_raw || '—' }}</td>
            <td class="py-3 px-2">
              <span :class="u.is_active ? 'badge-passed' : 'badge-failed'">
                {{ u.is_active ? 'Активен' : 'Неактивен' }}
              </span>
            </td>
            <td class="py-3 px-2">
              <button @click="openEdit(u)" class="text-xs text-blue-600 hover:underline">Изменить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit modal -->
    <div v-if="modal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md space-y-4">
        <h2 class="text-lg font-bold">Изменить пользователя</h2>
        <div>
          <label class="text-sm font-medium text-gray-700">ФИО</label>
          <input v-model="form.full_name" class="input-field mt-1" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-700">Должность</label>
          <input v-model="form.position_raw" class="input-field mt-1" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-700">Новый пароль</label>
          <input v-model="form.new_password" class="input-field mt-1" placeholder="Оставьте пустым, чтобы не менять" />
          <p class="text-xs text-gray-400 mt-1">Текущий: <span class="font-mono font-semibold">{{ form.current_password || 'не задан' }}</span></p>
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="form.is_active" id="is_active" />
          <label for="is_active" class="text-sm text-gray-700">Активен</label>
        </div>
        <div class="flex gap-3 pt-2">
          <button @click="save" :disabled="saving" class="btn-primary flex-1">
            {{ saving ? 'Сохраняю...' : 'Сохранить' }}
          </button>
          <button @click="modal = false" class="btn-secondary flex-1">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '@/services/api'

const users = ref([])
const loading = ref(true)
const search = ref('')
const modal = ref(false)
const saving = ref(false)
const editing = ref(null)
const form = ref({})

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/users', { params: { search: search.value || undefined } })
    users.value = data
  } finally { loading.value = false }
}

function openEdit(u) {
  editing.value = u
  form.value = {
    full_name: u.full_name,
    position_raw: u.position_raw || '',
    is_active: u.is_active,
    new_password: '',
    current_password: u.plain_password || '',
  }
  modal.value = true
}

async function save() {
  saving.value = true
  try {
    const payload = {
      full_name: form.value.full_name,
      position_raw: form.value.position_raw,
      is_active: form.value.is_active,
    }
    if (form.value.new_password) payload.new_password = form.value.new_password
    const { data } = await api.patch(`/admin/users/${editing.value.id}`, payload)
    // update local list
    const idx = users.value.findIndex(u => u.id === editing.value.id)
    if (idx !== -1) {
      users.value[idx] = { ...users.value[idx], ...data }
      if (form.value.new_password) users.value[idx].plain_password = form.value.new_password
    }
    modal.value = false
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally { saving.value = false }
}

onMounted(load)
watch(search, () => setTimeout(load, 300))
</script>
