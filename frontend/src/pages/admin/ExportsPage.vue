<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Экспорт данных</h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Export 1: Logins & Passwords -->
      <div class="card">
        <h2 class="font-semibold mb-1">Логины и пароли</h2>
        <p class="text-sm text-gray-500 mb-4">Список новых пользователей с их учётными данными по выбранному потоку</p>
        <div class="mb-3">
          <select v-model="selectedBatch" class="input-field">
            <option value="">— Выберите поток —</option>
            <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>
        <a
          v-if="selectedBatch"
          :href="`/api/v1/admin/exports/logins-passwords?batch_id=${selectedBatch}`"
          class="btn-primary inline-block text-center"
          download
        >Скачать .xlsx</a>
        <button v-else disabled class="btn-primary opacity-50 cursor-not-allowed">Выберите поток</button>
      </div>

      <!-- Export 2: All Results -->
      <div class="card">
        <h2 class="font-semibold mb-1">Все результаты тестов</h2>
        <p class="text-sm text-gray-500 mb-4">Сводный отчёт по всем назначениям и попыткам за всё время</p>
        <a href="/api/v1/admin/exports/results" class="btn-primary inline-block text-center" download>Скачать .xlsx</a>
      </div>

      <!-- Export 3: Batch Results -->
      <div class="card">
        <h2 class="font-semibold mb-1">Результаты по потоку</h2>
        <p class="text-sm text-gray-500 mb-4">Отчёт о прохождении курсов по выбранному потоку</p>
        <div class="mb-3">
          <select v-model="selectedBatch2" class="input-field">
            <option value="">— Выберите поток —</option>
            <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>
        <a
          v-if="selectedBatch2"
          :href="`/api/v1/admin/exports/batches/${selectedBatch2}`"
          class="btn-primary inline-block text-center"
          download
        >Скачать .xlsx</a>
        <button v-else disabled class="btn-primary opacity-50 cursor-not-allowed">Выберите поток</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const batches = ref([])
const selectedBatch = ref('')
const selectedBatch2 = ref('')

onMounted(async () => {
  const { data } = await api.get('/admin/batches')
  batches.value = data
})
</script>
