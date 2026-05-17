<template>
  <div class="min-h-screen bg-gray-100">

    <!-- Header -->
    <div class="bg-blue-700 text-white px-4 py-4 text-center shadow">
      <div class="text-base font-bold tracking-widest">ÖZEN-PROM</div>
      <div class="text-xs opacity-70 mt-0.5">Система управления обучением и допусками</div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <div class="text-gray-400 text-sm">Загрузка карточки...</div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="max-w-sm mx-auto mt-10 px-4 text-center">
      <div class="text-6xl mb-4">❌</div>
      <h2 class="text-xl font-bold text-red-600 mb-2">Карточка не найдена</h2>
      <p class="text-gray-500 text-sm">Данный QR-код недействителен или устарел.</p>
    </div>

    <!-- Worker card -->
    <div v-else class="max-w-sm mx-auto px-4 py-6 space-y-4">

      <!-- Identity block -->
      <div class="bg-white rounded-2xl shadow-sm p-5 text-center">
        <div class="w-20 h-20 rounded-full overflow-hidden mx-auto mb-3 bg-blue-100 flex items-center justify-center">
          <img v-if="worker.photo_url" :src="worker.photo_url" class="w-full h-full object-cover" alt="Фото" />
          <span v-else class="text-3xl">👷</span>
        </div>
        <h1 class="text-lg font-bold text-gray-900 leading-snug">{{ worker.full_name }}</h1>
        <div v-if="worker.position" class="text-sm text-gray-600 mt-1">{{ worker.position }}</div>
        <div v-if="worker.organization_name" class="text-xs text-gray-400 mt-0.5 font-medium">
          {{ worker.organization_name }}
        </div>
      </div>

      <!-- Summary badges -->
      <div class="grid grid-cols-3 gap-2 text-center">
        <div class="bg-green-50 rounded-xl p-3">
          <div class="text-2xl font-bold text-green-700">{{ countByStatus('active') }}</div>
          <div class="text-xs text-green-600 mt-0.5">Действуют</div>
        </div>
        <div class="bg-orange-50 rounded-xl p-3">
          <div class="text-2xl font-bold text-orange-600">{{ countByStatus('expiring_soon') }}</div>
          <div class="text-xs text-orange-500 mt-0.5">Скоро истекут</div>
        </div>
        <div class="bg-red-50 rounded-xl p-3">
          <div class="text-2xl font-bold text-red-600">{{ countByStatus('expired') }}</div>
          <div class="text-xs text-red-500 mt-0.5">Истекли</div>
        </div>
      </div>

      <!-- Certificate list -->
      <div>
        <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-widest px-1 mb-2">
          Удостоверения ({{ worker.certificates.length }})
        </h2>

        <div v-if="worker.certificates.length === 0"
          class="bg-white rounded-2xl p-5 text-center text-gray-400 text-sm">
          Нет выданных удостоверений
        </div>

        <div class="space-y-2">
          <router-link
            v-for="c in worker.certificates"
            :key="c.id"
            :to="`/verify/${c.id}`"
            class="flex items-center bg-white rounded-2xl p-4 shadow-sm border-l-4 active:bg-gray-50 transition-colors"
            :class="{
              'border-green-400': c.status === 'active',
              'border-orange-400': c.status === 'expiring_soon',
              'border-red-400': c.status === 'expired',
            }"
          >
            <!-- Type badge -->
            <div
              class="shrink-0 w-12 h-12 rounded-xl flex items-center justify-center text-xs font-bold mr-3"
              :class="{
                'bg-green-100 text-green-700': c.status === 'active',
                'bg-orange-100 text-orange-700': c.status === 'expiring_soon',
                'bg-red-100 text-red-700': c.status === 'expired',
              }"
            >
              {{ c.training_type_name ?? '—' }}
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span
                  class="text-xs px-2 py-0.5 rounded-full font-medium"
                  :class="{
                    'bg-green-100 text-green-700': c.status === 'active',
                    'bg-orange-100 text-orange-600': c.status === 'expiring_soon',
                    'bg-red-100 text-red-600': c.status === 'expired',
                  }"
                >{{ statusLabel(c.status) }}</span>
              </div>
              <div class="text-xs text-gray-500 font-mono mt-0.5 truncate">{{ c.certificate_number }}</div>
            </div>

            <!-- Date -->
            <div class="text-right ml-2 shrink-0">
              <div class="text-xs text-gray-400">до</div>
              <div
                class="text-sm font-semibold leading-tight"
                :class="{
                  'text-green-700': c.status === 'active',
                  'text-orange-600': c.status === 'expiring_soon',
                  'text-red-600': c.status === 'expired',
                }"
              >{{ formatDate(c.valid_until) }}</div>
            </div>

            <div class="ml-2 text-gray-300 text-lg">›</div>
          </router-link>
        </div>
      </div>

      <!-- Footer -->
      <div class="text-center text-xs text-gray-400 pt-2 pb-4">
        Özen-Prom · Нажмите на удостоверение для подробной проверки
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const worker = ref(null)
const loading = ref(true)
const error = ref(false)

onMounted(async () => {
  try {
    const res = await api.get(`/verify/worker/${route.params.token}`)
    worker.value = res.data
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

function statusLabel(s) {
  if (s === 'expired') return 'Истекло'
  if (s === 'expiring_soon') return 'Скоро истекает'
  return 'Действительно'
}

function countByStatus(s) {
  return worker.value?.certificates.filter(c => c.status === s).length ?? 0
}
</script>
