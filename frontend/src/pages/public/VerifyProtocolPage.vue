<template>
  <div class="min-h-screen bg-gray-100">

    <div class="bg-blue-700 text-white px-4 py-4 text-center shadow print:hidden">
      <div class="text-base font-bold tracking-widest">ÖZEN-PROM</div>
      <div class="text-xs opacity-70 mt-0.5">Протокол проверки знаний</div>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400 text-sm">Загрузка...</div>

    <div v-else-if="error" class="max-w-sm mx-auto px-4 py-6">
      <div class="bg-white rounded-2xl shadow p-8 text-center">
        <div class="text-5xl mb-4">❌</div>
        <h2 class="text-xl font-bold text-red-600 mb-2">Не найдено</h2>
        <p class="text-gray-500 text-sm">Протокол не найден.</p>
      </div>
    </div>

    <div v-else class="max-w-2xl mx-auto px-4 py-6">
      <router-link :to="`/verify/${route.params.id}`" class="text-sm text-gray-500 hover:text-gray-700 print:hidden">← К удостоверению</router-link>

      <div class="bg-white rounded-2xl shadow-sm p-6 mt-4">
        <h1 class="text-lg font-bold text-gray-900 mb-1">Протокол № {{ p.protocol_number }}</h1>
        <div class="text-sm text-gray-500 mb-4">от {{ formatDate(p.exam_date) }}</div>

        <div v-if="p.organization_name" class="mb-3">
          <div class="text-xs text-gray-400 mb-0.5">Организация</div>
          <div class="text-sm text-gray-800">{{ p.organization_name }}</div>
        </div>

        <div v-if="p.order_number" class="mb-3">
          <div class="text-xs text-gray-400 mb-0.5">Основание</div>
          <div class="text-sm text-gray-800">
            Приказ № {{ p.order_number }}<span v-if="p.order_date"> от {{ formatDate(p.order_date) }}</span>
          </div>
        </div>

        <div v-if="p.regulatory_docs" class="mb-3">
          <div class="text-xs text-gray-400 mb-0.5">Нормативные документы</div>
          <div class="text-sm text-gray-700 whitespace-pre-line">{{ p.regulatory_docs }}</div>
        </div>

        <hr class="my-4 border-gray-100">

        <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Комиссия</h2>
        <div class="space-y-2 mb-4">
          <div v-for="m in p.commission_members" :key="m.id" class="text-sm">
            <span class="font-medium text-gray-800">{{ m.role === 'chair' ? 'Председатель' : 'Член комиссии' }}:</span>
            {{ m.full_name }}
            <span v-if="m.position_title" class="text-gray-500"> — {{ m.position_title }}</span>
          </div>
        </div>

        <hr class="my-4 border-gray-100" v-if="p.participant">

        <template v-if="p.participant">
          <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Результат проверки</h2>
          <div class="space-y-2 text-sm">
            <div><span class="text-gray-500">ФИО:</span> <strong>{{ p.participant.full_name }}</strong></div>
            <div v-if="p.participant.position"><span class="text-gray-500">Должность:</span> {{ p.participant.position }}</div>
            <div v-if="p.participant.education"><span class="text-gray-500">Образование:</span> {{ p.participant.education }}</div>
            <div>
              <span class="text-gray-500">Заключение:</span>
              <span :class="p.participant.result === 'passed' ? 'text-green-700 font-semibold' : 'text-red-600 font-semibold'">
                {{ p.participant.result === 'passed' ? 'сдал(а)' : 'не сдал(а)' }}
              </span>
            </div>
          </div>
        </template>
      </div>

      <div class="mt-4 text-center text-xs text-gray-400 print:hidden">
        Данные проверены на портале Özen-Prom
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const p = ref(null)
const loading = ref(true)
const error = ref(false)

onMounted(async () => {
  try {
    const res = await api.get(`/verify/${route.params.id}/protocol`)
    p.value = res.data
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})

function formatDate(d) {
  if (!d) return '—'
  return new Date(d + 'T00:00:00').toLocaleDateString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}
</script>
