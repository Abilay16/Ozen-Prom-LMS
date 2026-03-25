<template>
  <div>
    <RouterLink to="/admin/batches" class="text-blue-600 text-sm hover:underline">&larr; Назад к потокам</RouterLink>

    <div class="mt-4 mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ batch?.name || 'Загрузка...' }}</h1>
      <span v-if="batch" :class="statusBadge(batch.status)" class="text-sm px-3 py-1 rounded-full">{{ statusLabel(batch.status) }}</span>
    </div>

    <!-- Info: disciplines -->
    <div v-if="batch?.disciplines?.length" class="card mb-4">
      <div class="text-sm font-medium text-gray-600 mb-2">Обучения в этом потоке:</div>
      <div class="flex flex-wrap gap-2">
        <span v-for="d in batch.disciplines" :key="d.id" class="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">
          {{ d.name }}
        </span>
      </div>
    </div>

    <!-- Excel format hint -->
    <div class="card mb-4 bg-blue-50 border border-blue-200">
      <div class="text-sm font-semibold text-blue-800 mb-1"> Формат Excel-файла</div>
      <div class="text-sm text-blue-700">
        Колонки: <strong>ФИО</strong> | <strong>Должность</strong> | <strong>Организация</strong><br/>
        Первая строка  заголовки. Пример колонок: "ФИО", "Должность", "Организация".
      </div>
    </div>

    <!-- Step 1: Upload Excel -->
    <div class="card mb-4">
      <h2 class="font-semibold mb-3">1. Загрузить Excel-файл сотрудников</h2>
      <div class="flex items-center gap-3 flex-wrap">
        <input ref="fileInput" type="file" accept=".xlsx,.xls" class="hidden" @change="onFileSelect" />
        <button @click="fileInput.click()" class="btn-secondary">Выбрать файл</button>
        <span class="text-sm text-gray-500">{{ selectedFile?.name || 'Файл не выбран' }}</span>
        <button v-if="selectedFile" @click="uploadFile" :disabled="uploading" class="btn-primary">
          {{ uploading ? 'Загрузка...' : 'Загрузить и проверить' }}
        </button>
      </div>
      <p v-if="uploadError" class="mt-2 text-sm text-red-500">{{ uploadError }}</p>
    </div>

    <!-- Step 2: Preview -->
    <div v-if="preview" class="card mb-4">
      <h2 class="font-semibold mb-3">2. Предварительный просмотр</h2>
      <div class="grid grid-cols-3 gap-3 mb-4">
        <div class="text-center p-3 bg-green-50 rounded">
          <div class="text-2xl font-bold text-green-600">{{ preview.ok }}</div>
          <div class="text-xs text-gray-500">Готовы к импорту</div>
        </div>
        <div class="text-center p-3 bg-yellow-50 rounded">
          <div class="text-2xl font-bold text-yellow-600">{{ preview.manual_review }}</div>
          <div class="text-xs text-gray-500">На проверку</div>
        </div>
        <div class="text-center p-3 bg-red-50 rounded">
          <div class="text-2xl font-bold text-red-600">{{ preview.error }}</div>
          <div class="text-xs text-gray-500">Ошибок</div>
        </div>
      </div>

      <div class="flex gap-1 mb-3 border-b">
        <button v-for="tab in ['ok', 'manual_review', 'error']" :key="tab"
          @click="activeTab = tab"
          :class="['px-4 py-2 text-sm font-medium -mb-px', activeTab === tab ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500']">
          {{ tabLabel(tab) }}
        </button>
      </div>

      <div class="overflow-x-auto">
        <table class="text-sm w-full">
          <thead>
            <tr class="text-left text-gray-500 text-xs uppercase">
              <th class="py-1 pr-4">№</th>
              <th class="py-1 pr-4">ФИО</th>
              <th class="py-1 pr-4">Должность</th>
              <th class="py-1 pr-4">Организация</th>
              <th class="py-1">Примечание</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredRows" :key="row.row_number" class="border-t text-gray-700">
              <td class="py-1 pr-4 text-gray-400">{{ row.row_number }}</td>
              <td class="py-1 pr-4">{{ row.full_name || '' }}</td>
              <td class="py-1 pr-4">{{ row.position || '' }}</td>
              <td class="py-1 pr-4">{{ row.organization || '' }}</td>
              <td class="py-1 text-xs text-yellow-600">{{ row.warnings?.join(', ') || '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="mt-4 pt-4 border-t flex items-center gap-4">
        <button @click="confirmImport" :disabled="confirming" class="btn-primary">
          {{ confirming ? 'Создаём пользователей...' : `Подтвердить  создать пользователей (${preview.ok + preview.manual_review})` }}
        </button>
      </div>
    </div>

    <!-- Step 3: Credentials table -->
    <div v-if="result" class="card">
      <div class="flex items-center justify-between mb-3">
        <h2 class="font-semibold">3. Логины и пароли</h2>
        <button @click="downloadCredentials" class="btn-secondary text-sm"> Скачать Excel</button>
      </div>

      <div class="grid grid-cols-4 gap-3 mb-4 text-center text-sm">
        <div class="p-2 bg-green-50 rounded">
          <div class="font-bold text-green-600 text-lg">{{ result.summary?.created }}</div>
          <div class="text-gray-500 text-xs">Создано</div>
        </div>
        <div class="p-2 bg-blue-50 rounded">
          <div class="font-bold text-blue-600 text-lg">{{ result.summary?.duplicates }}</div>
          <div class="text-gray-500 text-xs">Дубликатов</div>
        </div>
        <div class="p-2 bg-yellow-50 rounded">
          <div class="font-bold text-yellow-600 text-lg">{{ result.summary?.manual_review }}</div>
          <div class="text-gray-500 text-xs">Без курса</div>
        </div>
        <div class="p-2 bg-red-50 rounded">
          <div class="font-bold text-red-600 text-lg">{{ result.summary?.errors }}</div>
          <div class="text-gray-500 text-xs">Ошибок</div>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="text-sm w-full border border-gray-200 rounded">
          <thead class="bg-gray-50">
            <tr class="text-left text-xs text-gray-500 uppercase">
              <th class="px-3 py-2">ФИО</th>
              <th class="px-3 py-2">Организация</th>
              <th class="px-3 py-2">Должность</th>
              <th class="px-3 py-2 font-bold text-blue-700">Логин</th>
              <th class="px-3 py-2 font-bold text-blue-700">Пароль</th>
              <th class="px-3 py-2">Курсы</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in result.credentials" :key="c.num" class="border-t">
              <td class="px-3 py-2">{{ c.full_name }}</td>
              <td class="px-3 py-2 text-gray-500">{{ c.organization }}</td>
              <td class="px-3 py-2 text-gray-500">{{ c.position }}</td>
              <td class="px-3 py-2 font-mono font-semibold text-blue-700">{{ c.login }}</td>
              <td class="px-3 py-2 font-mono font-semibold text-green-700">{{ c.password }}</td>
              <td class="px-3 py-2 text-xs text-gray-400">{{ c.courses }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const batchId = route.params.id

const batch = ref(null)
const selectedFile = ref(null)
const fileInput = ref(null)
const uploading = ref(false)
const uploadError = ref('')
const preview = ref(null)
const activeTab = ref('ok')
const confirming = ref(false)
const result = ref(null)

onMounted(async () => {
  const { data } = await api.get(`/admin/batches/${batchId}`)
  batch.value = data
})

function onFileSelect(e) {
  selectedFile.value = e.target.files[0]
}

async function uploadFile() {
  uploading.value = true
  uploadError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', selectedFile.value)
    await api.post(`/admin/batches/${batchId}/upload-excel`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    const { data } = await api.post(`/admin/batches/${batchId}/preview-import`)
    preview.value = data
  } catch (err) {
    uploadError.value = err.response?.data?.detail || 'Ошибка загрузки файла'
  }
  uploading.value = false
}

const filteredRows = computed(() => {
  if (!preview.value?.rows) return []
  return preview.value.rows.filter(r => r.status === activeTab.value)
})

function tabLabel(t) {
  return { ok: 'Готовы', manual_review: 'Проверить', error: 'Ошибки' }[t]
}

async function confirmImport() {
  confirming.value = true
  try {
    const { data } = await api.post(`/admin/batches/${batchId}/confirm-import`)
    result.value = data
    const { data: b } = await api.get(`/admin/batches/${batchId}`)
    batch.value = b
    preview.value = null
  } catch (err) {
    alert('Ошибка: ' + (err.response?.data?.detail || err.message))
  }
  confirming.value = false
}

async function downloadCredentials() {
  const token = localStorage.getItem('token')
  const url = `${import.meta.env.VITE_API_URL || ''}/api/v1/admin/exports/logins-passwords?batch_id=${batchId}`
  const a = document.createElement('a')
  a.href = url
  a.download = `credentials_${batchId}.xlsx`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function statusBadge(s) {
  return {
    draft: 'bg-gray-100 text-gray-600',
    processing: 'bg-yellow-100 text-yellow-700',
    completed: 'bg-green-100 text-green-700',
    archived: 'bg-red-100 text-red-600',
  }[s] || 'bg-gray-100'
}

function statusLabel(s) {
  return { draft: 'Черновик', processing: 'Обработка', completed: 'Завершён', archived: 'Архив' }[s] || s
}
</script>
