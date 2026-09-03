<template>
  <div>
    <RouterLink to="/admin/batches" class="text-blue-600 text-sm hover:underline">&larr; Назад к потокам</RouterLink>

    <div class="mt-4 mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ batch?.name || 'Загрузка...' }}</h1>
      <Badge v-if="batch" :variant="statusVariant(batch.status)">{{ statusLabel(batch.status) }}</Badge>
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

    <!-- Batch stats panel (shown after import completes) -->
    <div v-if="batch?.status === 'completed' && batchStats" class="card mb-4">
      <h2 class="font-semibold mb-3">Статистика потока</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="text-center p-3 bg-gray-50 rounded">
          <div class="text-2xl font-bold text-gray-700">{{ batchStats.total }}</div>
          <div class="text-xs text-gray-500">Сотрудников</div>
        </div>
        <div class="text-center p-3 bg-green-50 rounded">
          <div class="text-2xl font-bold text-green-600">{{ batchStats.passed }}</div>
          <div class="text-xs text-gray-500">Сдали</div>
        </div>
        <div class="text-center p-3 bg-blue-50 rounded">
          <div class="text-2xl font-bold text-blue-600">{{ batchStats.in_progress }}</div>
          <div class="text-xs text-gray-500">В процессе</div>
        </div>
        <div class="text-center p-3 bg-yellow-50 rounded">
          <div class="text-2xl font-bold text-yellow-600">{{ batchStats.assigned }}</div>
          <div class="text-xs text-gray-500">Не начали</div>
        </div>
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

    <!-- Step 1: Upload Excel or add manually -->
    <div class="card mb-4">
      <h2 class="font-semibold mb-3">1. Добавить сотрудников</h2>
      <div class="flex items-center gap-3 flex-wrap">
        <input ref="fileInput" type="file" accept=".xlsx,.xls" class="hidden" @change="onFileSelect" />
        <button @click="fileInput.click()" class="btn-secondary">Выбрать Excel</button>
        <span class="text-sm text-gray-500">{{ selectedFile?.name || 'Файл не выбран' }}</span>
        <button v-if="selectedFile" @click="uploadFile" :disabled="uploading" class="btn-primary">
          {{ uploading ? 'Загрузка...' : 'Загрузить и проверить' }}
        </button>
        <span class="text-gray-300">|</span>
        <button @click="manualModal = true" class="btn-secondary">➕ Добавить вручную</button>
      </div>
      <p v-if="uploadError" class="mt-2 text-sm text-red-500">{{ uploadError }}</p>
    </div>

    <!-- Manual add user modal -->
    <Modal v-model="manualModal" title="Добавить сотрудника вручную" max-width="max-w-md">
      <div v-if="!manualResult" class="space-y-3">
        <div>
          <label class="text-sm font-medium text-gray-700">ФИО <span class="text-red-500">*</span></label>
          <input v-model="manualForm.full_name" class="input-field mt-1" placeholder="Иванов Иван Иванович" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-700">Должность</label>
          <input v-model="manualForm.position" class="input-field mt-1" placeholder="Водитель" />
        </div>
        <div>
          <label class="text-sm font-medium text-gray-700">Организация</label>
          <input v-model="manualForm.organization" class="input-field mt-1" placeholder="ООО Пример" />
        </div>
        <div class="flex gap-3 pt-2">
          <button @click="addUserManually" :disabled="manualAdding" class="btn-primary disabled:opacity-50">
            {{ manualAdding ? 'Создаём...' : 'Добавить' }}
          </button>
          <button @click="manualModal = false; manualResult = null" class="btn-secondary">Отмена</button>
        </div>
      </div>

      <div v-else class="space-y-3">
        <div class="p-3 bg-green-50 border border-green-200 rounded text-sm">
          <div class="font-semibold text-green-700 mb-2">✅ Пользователь создан</div>
          <div><span class="text-gray-500">ФИО:</span> {{ manualResult.full_name }}</div>
          <div v-if="manualResult.organization"><span class="text-gray-500">Орг:</span> {{ manualResult.organization }}</div>
          <div v-if="manualResult.position"><span class="text-gray-500">Должность:</span> {{ manualResult.position }}</div>
          <div class="mt-2 flex gap-4">
            <div><span class="text-gray-500">Логин:</span> <span class="font-mono font-bold text-blue-700">{{ manualResult.login }}</span></div>
            <div><span class="text-gray-500">Пароль:</span> <span class="font-mono font-bold text-green-700">{{ manualResult.password }}</span></div>
          </div>
          <div v-if="manualResult.courses" class="mt-1 text-xs text-gray-500">Курсы: {{ manualResult.courses }}</div>
        </div>
        <div class="flex gap-3">
          <button @click="manualForm = { full_name: '', position: '', organization: '' }; manualResult = null" class="btn-secondary">Добавить ещё одного</button>
          <button @click="manualModal = false; manualResult = null" class="btn-primary">Готово</button>
        </div>
      </div>
    </Modal>

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
import { useToast, apiErrorMessage } from '@/composables/useToast'
import Modal from '@/components/Modal.vue'
import Badge from '@/components/Badge.vue'

const toast = useToast()
const route = useRoute()
const batchId = route.params.id

const batch = ref(null)
const batchStats = ref(null)
const selectedFile = ref(null)
const fileInput = ref(null)
const uploading = ref(false)
const uploadError = ref('')
const preview = ref(null)
const activeTab = ref('ok')
const confirming = ref(false)
const result = ref(null)

const manualModal = ref(false)
const manualAdding = ref(false)
const manualResult = ref(null)
const manualForm = ref({ full_name: '', position: '', organization: '' })

async function addUserManually() {
  if (!manualForm.value.full_name.trim()) { toast.error('Введите ФИО'); return }
  manualAdding.value = true
  try {
    const { data } = await api.post(`/admin/batches/${batchId}/add-user`, manualForm.value)
    manualResult.value = data
    // refresh stats if batch is completed
    try {
      const { data: progress } = await api.get('/admin/progress', { params: { batch_id: batchId, limit: 1000 } })
      batchStats.value = {
        total: progress.length,
        passed: progress.filter(r => r.status === 'passed').length,
        in_progress: progress.filter(r => r.status === 'in_progress').length,
        assigned: progress.filter(r => r.status === 'assigned').length,
      }
    } catch {}
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    manualAdding.value = false
  }
}

onMounted(async () => {
  const { data } = await api.get(`/admin/batches/${batchId}`)
  batch.value = data
  if (data.status === 'completed') {
    try {
      const { data: progress } = await api.get('/admin/progress', { params: { batch_id: batchId, limit: 1000 } })
      batchStats.value = {
        total: progress.length,
        passed: progress.filter(r => r.status === 'passed').length,
        in_progress: progress.filter(r => r.status === 'in_progress').length,
        assigned: progress.filter(r => r.status === 'assigned').length,
      }
    } catch {}
  }
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
    if (data.error) {
      toast.error('Ошибка импорта: ' + data.error)
    } else {
      result.value = data
      const { data: b } = await api.get(`/admin/batches/${batchId}`)
      batch.value = b
      preview.value = null
      // Load stats
      try {
        const { data: progress } = await api.get('/admin/progress', { params: { batch_id: batchId, limit: 1000 } })
        batchStats.value = {
          total: progress.length,
          passed: progress.filter(r => r.status === 'passed').length,
          in_progress: progress.filter(r => r.status === 'in_progress').length,
          assigned: progress.filter(r => r.status === 'assigned').length,
        }
      } catch {}
    }
  } catch (err) {
    toast.error(apiErrorMessage(err))
  }
  confirming.value = false
}

async function downloadCredentials() {
  try {
    const { data } = await api.get(`/admin/exports/logins-passwords?batch_id=${batchId}`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `credentials_${batchId}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    toast.error('Ошибка скачивания: ' + err.message)
  }
}

function statusVariant(s) {
  return {
    draft: 'neutral',
    processing: 'progress',
    completed: 'passed',
    archived: 'failed',
  }[s] || 'neutral'
}

function statusLabel(s) {
  return { draft: 'Черновик', processing: 'Обработка', completed: 'Завершён', archived: 'Архив' }[s] || s
}
</script>
