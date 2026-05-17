<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Пользователи</h1>
      <button @click="openCreate()" class="btn-primary">+ Добавить пользователя</button>
    </div>
    <div class="card">
      <div class="flex gap-4 mb-4">
        <input v-model="search" type="text" placeholder="Поиск по ФИО..." class="input-field max-w-xs" />
      </div>
      <div v-if="loading" class="text-gray-400 py-8 text-center">Загрузка...</div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 text-left">
            <th class="py-3 px-2 font-semibold text-gray-600">Фото</th>
            <th class="py-3 px-2 font-semibold text-gray-600">ФИО</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Логин</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Пароль</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Должность</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Организация</th>
            <th class="py-3 px-2 font-semibold text-gray-600">Статус</th>
            <th class="py-3 px-2 font-semibold text-gray-600"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b border-gray-100 hover:bg-gray-50">
            <td class="py-3 px-2">
              <div class="w-9 h-9 rounded-full overflow-hidden bg-gray-100 flex items-center justify-center">
                <img v-if="u.photo_url" :src="u.photo_url" class="w-full h-full object-cover" alt="" />
                <span v-else class="text-lg">👤</span>
              </div>
            </td>
            <td class="py-3 px-2">{{ u.full_name }}</td>
            <td class="py-3 px-2 font-mono text-gray-500">{{ u.login }}</td>
            <td class="py-3 px-2">
              <span v-if="u.plain_password" class="font-mono text-gray-700">{{ u.plain_password }}</span>
              <span v-else class="text-gray-300 text-xs italic">не задан</span>
            </td>
            <td class="py-3 px-2 text-gray-500">{{ u.position_raw || '—' }}</td>
            <td class="py-3 px-2 text-gray-500">{{ orgName(u.organization_id) }}</td>
            <td class="py-3 px-2">
              <span :class="u.is_active ? 'badge-passed' : 'badge-failed'">
                {{ u.is_active ? 'Активен' : 'Неактивен' }}
              </span>
            </td>
            <td class="py-3 px-2">
              <button @click="openEdit(u)" class="text-xs text-blue-600 hover:underline">Изменить</button>
              <button @click="deleteUser(u)" class="text-xs text-red-400 hover:text-red-600 hover:underline ml-2">Удалить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit modal -->
    <div v-if="modal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-lg space-y-4">
        <h2 class="text-lg font-bold">{{ editing ? 'Изменить пользователя' : 'Новый пользователь' }}</h2>

        <!-- Photo upload (edit only) -->
        <div v-if="editing" class="flex items-center gap-4">
          <div class="w-16 h-16 rounded-full overflow-hidden bg-gray-100 flex items-center justify-center shrink-0">
            <img v-if="editing.photo_url" :src="editing.photo_url + '?t=' + photoTs" class="w-full h-full object-cover" alt="Фото" />
            <span v-else class="text-3xl">👤</span>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700 block mb-1">Фото пользователя</label>
            <input type="file" accept="image/jpeg,image/png,image/webp" @change="handlePhotoFile" class="text-sm text-gray-600" />
            <p v-if="photoError" class="text-xs text-red-500 mt-1">{{ photoError }}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2">
            <label class="text-sm font-medium text-gray-700">ФИО <span class="text-red-400">*</span></label>
            <input v-model="form.full_name" class="input-field mt-1" placeholder="Иванов Иван Иванович" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Логин</label>
            <input v-model="form.login" class="input-field mt-1 font-mono" :placeholder="editing ? editing.login : 'авто'" :disabled="!!editing" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">{{ editing ? 'Новый пароль' : 'Пароль' }}</label>
            <input v-model="form.new_password" class="input-field mt-1 font-mono" :placeholder="editing ? 'оставьте пустым' : 'авто'" />
            <p v-if="editing && form.current_password" class="text-xs text-gray-400 mt-1">Текущий: <span class="font-mono font-semibold">{{ form.current_password }}</span></p>
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Должность</label>
            <input v-model="form.position_raw" class="input-field mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Организация</label>
            <input v-model="form.organization_name" list="orgs-datalist" class="input-field mt-1" placeholder="Название организации" />
            <datalist id="orgs-datalist">
              <option v-for="o in orgs" :key="o.id" :value="o.name" />
            </datalist>
          </div>
          <div v-if="!editing">
            <label class="text-sm font-medium text-gray-700">Роль</label>
            <select v-model="form.role" class="input-field mt-1">
              <option value="learner">Обучаемый (слушатель)</option>
              <option value="admin">Администратор</option>
              <option value="commission">Админ + Член комиссии</option>
            </select>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <input type="checkbox" v-model="form.is_active" id="is_active" />
          <label for="is_active" class="text-sm text-gray-700">Активен</label>
        </div>
        <div class="flex gap-3 pt-2">
          <button @click="save" :disabled="saving || !form.full_name" class="btn-primary flex-1">
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
const orgs = ref([])
const loading = ref(true)
const search = ref('')
const modal = ref(false)
const saving = ref(false)
const editing = ref(null)
const form = ref({})
const photoError = ref('')
const photoTs = ref(Date.now())  // cache-bust after upload

function orgName(id) {
  if (!id) return '—'
  return orgs.value.find(o => o.id === id)?.name || '—'
}

async function load() {
  loading.value = true
  try {
    const [usersRes, orgsRes] = await Promise.all([
      api.get('/admin/users', { params: { search: search.value || undefined } }),
      api.get('/admin/organizations'),
    ])
    users.value = usersRes.data
    orgs.value = orgsRes.data
  } finally { loading.value = false }
}

function openCreate() {
  editing.value = null
  form.value = { full_name: '', login: '', new_password: '', position_raw: '', organization_name: '', role: 'learner', is_active: true }
  modal.value = true
}

function openEdit(u) {
  editing.value = u
  form.value = {
    full_name: u.full_name,
    position_raw: u.position_raw || '',
    organization_name: orgName(u.organization_id) !== '—' ? orgName(u.organization_id) : '',
    is_active: u.is_active,
    new_password: '',
    current_password: u.plain_password || '',
    login: u.login,
    role: 'learner',
  }
  modal.value = true
}

async function save() {
  saving.value = true
  try {
    if (editing.value) {
      // Update existing learner
      const payload = {
        full_name: form.value.full_name,
        position_raw: form.value.position_raw,
        is_active: form.value.is_active,
      }
      if (form.value.organization_name) payload.organization_name = form.value.organization_name
      if (form.value.new_password) payload.new_password = form.value.new_password
      const { data } = await api.patch(`/admin/users/${editing.value.id}`, payload)
      const idx = users.value.findIndex(u => u.id === editing.value.id)
      if (idx !== -1) {
        users.value[idx] = { ...users.value[idx], ...data }
        if (form.value.new_password) users.value[idx].plain_password = form.value.new_password
      }
    } else if (form.value.role === 'learner') {
      // Create learner
      const payload = { full_name: form.value.full_name }
      if (form.value.login) payload.login = form.value.login
      if (form.value.new_password) payload.password = form.value.new_password
      if (form.value.position_raw) payload.position_raw = form.value.position_raw
      if (form.value.organization_name) payload.organization_name = form.value.organization_name
      const { data } = await api.post('/admin/users', payload)
      users.value.unshift(data)
    } else {
      // Create admin / commission member
      const payload = {
        full_name: form.value.full_name,
        login: form.value.login || undefined,
        password: form.value.new_password || undefined,
        position_title: form.value.position_raw || undefined,
        is_commission_eligible: form.value.role === 'commission',
      }
      await api.post('/admin/admin-users', payload)
      alert(`Администратор создан. Логин: ${form.value.login || '(см. в базе)'}`)
    }
    modal.value = false
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally { saving.value = false }
}

onMounted(load)
watch(search, () => setTimeout(load, 300))

async function handlePhotoFile(event) {
  const file = event.target.files?.[0]
  if (!file || !editing.value) return
  photoError.value = ''
  if (file.size > 5 * 1024 * 1024) {
    photoError.value = 'Файл слишком большой (макс. 5 МБ)'
    return
  }
  const fd = new FormData()
  fd.append('photo', file)
  try {
    const { data } = await api.post(`/admin/users/${editing.value.id}/photo`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    // Update local user record and force re-render
    const idx = users.value.findIndex(u => u.id === editing.value.id)
    if (idx !== -1) users.value[idx].photo_url = data.photo_url
    editing.value.photo_url = data.photo_url
    photoTs.value = Date.now()
  } catch (e) {
    photoError.value = 'Ошибка загрузки: ' + (e.response?.data?.detail || e.message)
  }
}

async function deleteUser(u) {
  if (!confirm(`Деактивировать пользователя "${u.full_name}"? Он будет скрыт из списков.`)) return
  await api.delete(`/admin/users/${u.id}`)
  await load()
}
</script>
