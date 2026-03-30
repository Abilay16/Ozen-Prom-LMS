<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Экспорт данных</h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Export 1: Logins & Passwords -->
      <div class="card flex flex-col">
        <h2 class="font-semibold mb-1">Логины и пароли</h2>
        <p class="text-sm text-gray-500 mb-4">Список сотрудников с логинами и паролями по выбранному потоку</p>
        <div class="mb-3">
          <select v-model="batchForCreds" class="input-field">
            <option value="">— Выберите поток —</option>
            <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>
        <button
          @click="download(`/admin/exports/logins-passwords?batch_id=${batchForCreds}`, `credentials_${batchForCreds}.xlsx`)"
          :disabled="!batchForCreds || downloading === 'creds'"
          class="btn-primary mt-auto"
        >
          {{ downloading === 'creds' ? 'Скачивается...' : 'Скачать .xlsx' }}
        </button>
      </div>

      <!-- Export 2: Batch Results -->
      <div class="card flex flex-col">
        <h2 class="font-semibold mb-1">Результаты по потоку</h2>
        <p class="text-sm text-gray-500 mb-4">Кто сдал / не сдал по выбранному потоку (оценки, даты)</p>
        <div class="mb-3">
          <select v-model="batchForResults" class="input-field">
            <option value="">— Выберите поток —</option>
            <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>
        <button
          @click="download(`/admin/exports/batches/${batchForResults}`, `results_${batchForResults}.xlsx`)"
          :disabled="!batchForResults || downloading === 'batch'"
          class="btn-primary mt-auto"
        >
          {{ downloading === 'batch' ? 'Скачивается...' : 'Скачать .xlsx' }}
        </button>
      </div>

      <!-- Export 3: All Results -->
      <div class="card flex flex-col">
        <h2 class="font-semibold mb-1">Все результаты</h2>
        <p class="text-sm text-gray-500 mb-4">Сводный отчёт по всем назначениям и попыткам за всё время</p>
        <button
          @click="download('/admin/exports/results', 'results_all.xlsx')"
          :disabled="downloading === 'all'"
          class="btn-primary mt-auto"
        >
          {{ downloading === 'all' ? 'Скачивается...' : 'Скачать .xlsx' }}
        </button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const batches = ref([])
const batchForCreds = ref('')
const batchForResults = ref('')
const downloading = ref('')

onMounted(async () => {
  const { data } = await api.get('/admin/batches')
  batches.value = data
})

async function download(url, filename) {
  const key = url.includes('logins') ? 'creds' : url.includes('batches/') ? 'batch' : 'all'
  downloading.value = key
  try {
    const { data } = await api.get(url, { responseType: 'blob' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(data)
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  } catch (err) {
    alert('Ошибка скачивания: ' + err.message)
  }
  downloading.value = ''
}
</script>

