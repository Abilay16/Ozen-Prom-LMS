<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Медицинские осмотры</h1>
      <button
        @click="showImportPanel = !showImportPanel"
        class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
      >📥 Импорт Excel</button>
    </div>

    <!-- Import panel -->
    <div v-if="showImportPanel" class="bg-white rounded-xl shadow-sm border border-blue-100 p-5 mb-5">
      <h2 class="text-sm font-semibold text-gray-700 mb-4">Загрузить файл от клиники (.xlsx)</h2>
      <div class="flex flex-wrap gap-4 items-end">
        <div>
          <label class="block text-xs text-gray-500 mb-1">Организация</label>
          <select v-model="importOrgId" class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-56">
            <option value="">Без привязки</option>
            <option v-for="o in orgs" :key="o.id" :value="o.id">{{ o.name }}</option>
          </select>
        </div>
        <div>
          <label class="block text-xs text-gray-500 mb-1">Файл Excel</label>
          <input
            ref="importFileInput"
            type="file"
            accept=".xlsx,.xls"
            class="text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 file:text-xs file:font-medium hover:file:bg-blue-100"
          />
        </div>
        <button
          @click="doImport"
          :disabled="importing"
          class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
        >{{ importing ? 'Импорт...' : 'Загрузить' }}</button>
      </div>
      <div v-if="importResult" class="mt-3 text-sm" :class="importResult.ok ? 'text-green-700' : 'text-red-600'">
        {{ importResult.message }}
      </div>
    </div>

    <!-- Unmatched panel -->
    <div v-if="unmatchedItems.length > 0" class="bg-orange-50 border border-orange-200 rounded-xl p-4 mb-5">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <span class="text-lg">⚠️</span>
          <span class="text-sm font-semibold text-orange-800">
            {{ unmatchedItems.length }} {{ unmatchedItems.length === 1 ? 'запись не привязана' : 'записей не привязаны' }} к пользователям — сопоставьте вручную
          </span>
        </div>
        <button @click="unmatchedItems = []" class="text-xs text-orange-400 hover:text-orange-600">Скрыть</button>
      </div>
      <div class="space-y-2">
        <div
          v-for="item in unmatchedItems"
          :key="item.id"
          class="flex flex-wrap items-center gap-3 bg-white rounded-lg p-3 border border-orange-100"
        >
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-800">{{ item.full_name }}</div>
            <div class="text-xs text-gray-400 mt-0.5">
              {{ formatDate(item.exam_date) }}{{ item.position ? ' · ' + item.position : '' }}
            </div>
          </div>
          <button
            @click="openAssignModal(item)"
            class="text-xs px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap"
          >🔗 Привязать</button>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white rounded-xl shadow-sm p-4 mb-4 flex flex-wrap gap-3">
      <input
        v-model="search"
        placeholder="Поиск по ФИО..."
        class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-64"
      />
      <select v-model="filterOrg" @change="load" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
        <option value="">Все организации</option>
        <option v-for="o in orgs" :key="o.id" :value="o.id">{{ o.name }}</option>
      </select>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 border-b border-gray-200">
          <tr>
            <th class="text-left px-4 py-3 font-medium text-gray-600">ФИО</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Дата рожд.</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Пол</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Объект/участок</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Должность</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">МКБ-10</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Дата осмотра</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Заключение</th>
            <th class="text-left px-4 py-3 font-medium text-gray-600">Сотрудник</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-if="loading">
            <td colspan="10" class="text-center py-10 text-gray-400">Загрузка...</td>
          </tr>
          <tr v-else-if="filteredRecords.length === 0">
            <td colspan="10" class="text-center py-10 text-gray-400">Нет данных</td>
          </tr>
          <tr v-for="r in filteredRecords" :key="r.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-800">{{ r.full_name }}</td>
            <td class="px-4 py-3 text-gray-600">{{ formatDate(r.birth_date) }}</td>
            <td class="px-4 py-3 text-gray-600">{{ r.gender ?? '—' }}</td>
            <td class="px-4 py-3 text-gray-600 max-w-[160px] truncate" :title="r.workplace">{{ r.workplace ?? '—' }}</td>
            <td class="px-4 py-3 text-gray-600 max-w-[160px] truncate" :title="r.position">{{ r.position ?? '—' }}</td>
            <td class="px-4 py-3 text-gray-600 max-w-[140px] truncate" :title="r.icd10_group">{{ r.icd10_group ?? '—' }}</td>
            <td class="px-4 py-3 text-gray-600">{{ formatDate(r.exam_date) }}</td>
            <td class="px-4 py-3">
              <span
                class="px-2 py-0.5 rounded text-xs font-medium"
                :class="r.fit_for_work === true ? 'bg-green-100 text-green-700' : r.fit_for_work === false ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'"
              >
                {{ r.fit_for_work === true ? 'Годен' : r.fit_for_work === false ? 'Не годен' : '—' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div v-if="r.user_id" class="flex items-center gap-1.5">
                <span class="text-xs text-green-600 font-medium">✓ Привязан</span>
                <button @click="openAssignModal(r)" class="text-xs text-gray-400 hover:text-blue-600 transition-colors" title="Изменить привязку">✏</button>
              </div>
              <button
                v-else
                @click="openAssignModal(r)"
                class="text-xs text-orange-500 hover:text-orange-700 font-medium transition-colors"
              >🔗 Привязать</button>
            </td>
            <td class="px-4 py-3">
              <button
                @click="deleteRecord(r.id)"
                class="text-xs text-red-500 hover:text-red-700 transition-colors"
              >🗑 Удалить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Assign user modal -->
    <Teleport to="body">
      <div
        v-if="assignModal"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
        @click.self="assignModal = null"
      >
        <div class="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md">
          <h3 class="text-base font-semibold text-gray-800 mb-1">Привязать к пользователю</h3>
          <div class="text-sm text-gray-500 mb-4">
            ФИО из файла: <span class="font-medium text-gray-800">{{ assignModal.full_name }}</span>
          </div>
          <div class="space-y-2">
            <input
              v-model="assignSearch"
              placeholder="Поиск пользователя по ФИО..."
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              v-model="assignSelectedUserId"
              size="7"
              class="w-full border border-gray-300 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">— выберите пользователя —</option>
              <option v-for="u in assignFilteredUsers" :key="u.id" :value="u.id">
                {{ u.full_name }}
              </option>
            </select>
          </div>
          <div v-if="allUsersLoading" class="text-xs text-gray-400 mt-2">Загрузка пользователей...</div>
          <div class="flex gap-3 mt-4">
            <button
              @click="doAssign"
              :disabled="!assignSelectedUserId || assignSaving"
              class="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >{{ assignSaving ? 'Сохранение...' : 'Привязать' }}</button>
            <button
              @click="assignModal = null"
              class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-colors"
            >Отмена</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="flex justify-center mt-4 gap-2">
      <button
        v-for="p in pageCount"
        :key="p"
        @click="page = p; load()"
        :class="page === p ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'"
        class="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
      >{{ p }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

const records = ref([])
const orgs = ref([])
const loading = ref(true)
const search = ref('')
const filterOrg = ref('')
const page = ref(1)
const pageSize = 50
const total = ref(0)

const filteredRecords = computed(() => {
  const s = search.value.trim().toLowerCase()
  if (!s) return records.value
  return records.value.filter(r => r.full_name?.toLowerCase().includes(s))
})

const showImportPanel = ref(false)
const importOrgId = ref('')
const importFileInput = ref(null)
const importing = ref(false)
const importResult = ref(null)

// Unmatched after import
const unmatchedItems = ref([])

// Assign modal
const assignModal = ref(null)   // exam record being assigned
const assignSearch = ref('')
const assignSelectedUserId = ref('')
const assignSaving = ref(false)
const allUsers = ref([])
const allUsersLoading = ref(false)

const assignFilteredUsers = computed(() => {
  const s = assignSearch.value.trim().toLowerCase()
  if (!s) return allUsers.value
  return allUsers.value.filter(u => u.full_name?.toLowerCase().includes(s))
})

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

onMounted(async () => {
  const [orgsRes] = await Promise.all([
    api.get('/admin/organizations'),
  ])
  orgs.value = orgsRes.data?.items ?? orgsRes.data ?? []
  await load()
})

async function load() {
  loading.value = true
  try {
    const params = { skip: (page.value - 1) * pageSize, limit: pageSize }
    if (search.value) params.search = search.value
    if (filterOrg.value) params.organization_id = filterOrg.value
    const res = await api.get('/admin/medical-exams', { params })
    records.value = res.data?.items ?? res.data ?? []
    total.value = res.data?.total ?? records.value.length
  } finally {
    loading.value = false
  }
}

async function doImport() {
  importResult.value = null
  const file = importFileInput.value?.files?.[0]
  if (!file) { importResult.value = { ok: false, message: 'Выберите файл Excel' }; return }
  importing.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    if (importOrgId.value) form.append('organization_id', importOrgId.value)
    const res = await api.post('/admin/medical-exams/import', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    const { imported, total_parsed, unmatched } = res.data
    const unmatchedCount = unmatched?.length ?? 0
    importResult.value = {
      ok: true,
      message: `Импортировано: ${imported} записей` +
        (unmatchedCount > 0 ? ` (автоматически не привязано: ${unmatchedCount})` : ' — все привязаны')
    }
    unmatchedItems.value = unmatched ?? []
    if (importFileInput.value) importFileInput.value.value = ''
    await load()
  } catch (e) {
    importResult.value = { ok: false, message: e.response?.data?.detail ?? 'Ошибка импорта' }
  } finally {
    importing.value = false
  }
}

async function openAssignModal(item) {
  assignModal.value = item
  assignSearch.value = ''
  assignSelectedUserId.value = ''
  if (allUsers.value.length === 0) {
    allUsersLoading.value = true
    try {
      const res = await api.get('/admin/users', { params: { limit: 1000 } })
      allUsers.value = (res.data?.items ?? res.data ?? [])
        .sort((a, b) => a.full_name.localeCompare(b.full_name, 'ru'))
    } finally {
      allUsersLoading.value = false
    }
  }
}

async function doAssign() {
  if (!assignSelectedUserId.value || !assignModal.value) return
  assignSaving.value = true
  try {
    await api.patch(`/admin/medical-exams/${assignModal.value.id}/assign-user`, {
      user_id: assignSelectedUserId.value,
    })
    // Remove from unmatched list if present
    unmatchedItems.value = unmatchedItems.value.filter(i => i.id !== assignModal.value.id)
    // Update user_id in main table
    const rec = records.value.find(r => r.id === assignModal.value.id)
    if (rec) rec.user_id = assignSelectedUserId.value
    assignModal.value = null
  } catch (e) {
    alert(e.response?.data?.detail ?? 'Ошибка привязки')
  } finally {
    assignSaving.value = false
  }
}

async function deleteRecord(id) {
  if (!confirm('Удалить запись медосмотра?')) return
  try {
    await api.delete(`/admin/medical-exams/${id}`)
    records.value = records.value.filter(r => r.id !== id)
    total.value = Math.max(0, total.value - 1)
  } catch {
    alert('Ошибка удаления')
  }
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU')
}
</script>
