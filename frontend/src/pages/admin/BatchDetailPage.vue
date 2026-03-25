<template>
  <div>
    <RouterLink to="/admin/batches" class="text-blue-600 text-sm hover:underline">&larr; Назад к потокам</RouterLink>
    <div class="mt-4 mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ batch?.name || 'Загрузка...' }}</h1>
      <span v-if="batch" :class="statusBadge(batch.status)" class="text-sm">{{ batch.status }}</span>
    </div>

    <!-- Step 1: Upload Excel -->
    <div class="card mb-4">
      <h2 class="font-semibold mb-3">1. Загрузить Excel-файл</h2>
      <div class="flex items-center gap-3 flex-wrap">
        <input ref="fileInput" type="file" accept=".xlsx,.xls" class="hidden" @change="onFileSelect" />
        <button @click="fileInput.click()" class="btn-secondary">Выбрать файл</button>
        <span class="text-sm text-gray-500">{{ selectedFile?.name || 'Файл не выбран' }}</span>
        <button v-if="selectedFile" @click="uploadFile" :disabled="uploading" class="btn-primary">
          {{ uploading ? 'Загрузка...' : 'Загрузить' }}
        </button>
      </div>
      <p v-if="uploadMsg" class="mt-2 text-sm text-green-600">{{ uploadMsg }}</p>
    </div>

    <!-- Step 2: Preview -->
    <div v-if="preview" class="card mb-4">
      <h2 class="font-semibold mb-3">2. Проверить данные</h2>
      <div class="grid grid-cols-3 gap-3 mb-4">
        <div class="text-center p-3 bg-green-50 rounded">
          <div class="text-2xl font-bold text-green-600">{{ preview.ok }}</div>
          <div class="text-xs text-gray-500">ОК</div>
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

      <!-- Tabs -->
      <div class="flex gap-1 mb-3 border-b">
        <button
          v-for="tab in ['ok', 'manual_review', 'error']"
          :key="tab"
          @click="activeTab = tab"
          :class="['px-4 py-2 text-sm font-medium -mb-px', activeTab === tab ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500']"
        >
          {{ tabLabel(tab) }}
        </button>
      </div>

      <div class="overflow-x-auto">
        <table class="text-sm w-full">
          <thead>
            <tr class="text-left text-gray-500 text-xs uppercase">
              <th class="py-1 pr-4">ФИО</th>
              <th class="py-1 pr-4">Должность</th>
              <th class="py-1 pr-4">Дисциплина</th>
              <th class="py-1">Статус / Ошибка</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in filteredRows"
              :key="row.row_number"
              class="border-t text-gray-700"
            >
              <td class="py-1 pr-4">{{ row.full_name || '—' }}</td>
              <td class="py-1 pr-4">{{ row.position || '—' }}</td>
              <td class="py-1 pr-4">{{ row.discipline || '—' }}</td>
              <td class="py-1 text-xs text-red-500">{{ row.error_message || row.status }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Step 3: Confirm -->
      <div class="mt-4 pt-4 border-t flex items-center gap-4">
        <button @click="confirmImport" :disabled="confirming" class="btn-primary">
          {{ confirming ? 'Создание...' : 'Подтвердить и создать пользователей' }}
        </button>
        <span class="text-sm text-gray-400">Будет создано ~{{ preview.ok }} пользователей</span>
      </div>
    </div>

    <!-- Step 4: Result / Download credentials -->
    <div v-if="result" class="card">
      <h2 class="font-semibold mb-3">3. Результат импорта</h2>
      <div class="grid grid-cols-2 gap-3 mb-4">
        <div class="p-3 bg-green-50 rounded">
          <div class="font-bold text-green-600">{{ result.created }}</div>
          <div class="text-xs text-gray-500">Создано пользователей</div>
        </div>
        <div class="p-3 bg-yellow-50 rounded">
          <div class="font-bold text-yellow-600">{{ result.duplicates }}</div>
          <div class="text-xs text-gray-500">Дубликатов пропущено</div>
        </div>
      </div>
      <a :href="`/api/v1/admin/exports/logins-passwords?batch_id=${batchId}`" class="btn-primary inline-block">
        Скачать логины и пароли (.xlsx)
      </a>
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
const uploadMsg = ref('')
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
  uploadMsg.value = ''
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  await api.post(`/admin/batches/${batchId}/upload-excel`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  uploadMsg.value = 'Файл загружен. Анализируем...'
  const { data } = await api.post(`/admin/batches/${batchId}/preview-import`)
  preview.value = data
  uploading.value = false
  uploadMsg.value = ''
}

const filteredRows = computed(() => {
  if (!preview.value?.rows) return []
  return preview.value.rows.filter(r => r.status === activeTab.value)
})

function tabLabel(t) {
  return { ok: 'ОК', manual_review: 'Проверить', error: 'Ошибки' }[t]
}

async function confirmImport() {
  confirming.value = true
  const { data } = await api.post(`/admin/batches/${batchId}/confirm-import`)
  result.value = data
  confirming.value = false
  const { data: b } = await api.get(`/admin/batches/${batchId}`)
  batch.value = b
}

function statusBadge(s) {
  return { draft: 'badge-assigned', processing: 'badge-progress', completed: 'badge-passed', archived: 'badge-failed' }[s] || 'badge-assigned'
}
</script>
