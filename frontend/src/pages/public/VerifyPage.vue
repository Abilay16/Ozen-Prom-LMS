<template>
  <div class="min-h-screen bg-gray-100">

    <!-- Header -->
    <div class="bg-blue-700 text-white px-4 py-4 text-center shadow">
      <div class="text-base font-bold tracking-widest">ÖZEN-PROM</div>
      <div class="text-xs opacity-70 mt-0.5">Проверка удостоверения</div>
    </div>

    <div class="max-w-sm mx-auto px-4 py-6">

      <div v-if="loading" class="text-center py-16 text-gray-400 text-sm">Проверяем удостоверение...</div>

      <div v-else-if="error" class="bg-white rounded-2xl shadow p-8 text-center">
        <div class="text-5xl mb-4">❌</div>
        <h2 class="text-xl font-bold text-red-600 mb-2">Недействительно</h2>
        <p class="text-gray-500 text-sm">Удостоверение не найдено или отозвано.</p>
      </div>

      <template v-else>
        <!-- Status banner -->
        <div
          class="rounded-2xl p-4 mb-4 text-center font-semibold text-sm shadow-sm"
          :class="{
            'bg-green-600 text-white': cert.status === 'active',
            'bg-orange-500 text-white': cert.status === 'expiring_soon',
            'bg-red-600 text-white': cert.status === 'expired',
          }"
        >
          <span v-if="cert.status === 'active'">✅ Удостоверение действительно</span>
          <span v-else-if="cert.status === 'expiring_soon'">⚠️ Удостоверение скоро истекает</span>
          <span v-else>❌ Срок действия удостоверения истёк</span>
        </div>

        <!-- Main info card -->
        <div class="bg-white rounded-2xl shadow-sm p-5 space-y-3 mb-4">
          <div>
            <div class="text-xs text-gray-400 mb-0.5">ФИО</div>
            <div class="font-bold text-gray-900 text-base">{{ cert.full_name }}</div>
          </div>
          <div v-if="cert.organization_name">
            <div class="text-xs text-gray-400 mb-0.5">Организация</div>
            <div class="text-sm text-gray-800">{{ cert.organization_name }}</div>
          </div>
          <div v-if="cert.position">
            <div class="text-xs text-gray-400 mb-0.5">Должность</div>
            <div class="text-sm text-gray-800">{{ cert.position }}</div>
          </div>
          <hr class="border-gray-100">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <div class="text-xs text-gray-400 mb-0.5">Вид проверки</div>
              <div class="text-sm font-semibold text-gray-800">{{ cert.training_type_short ?? cert.training_type }}</div>
              <div class="text-xs text-gray-500">{{ cert.training_type }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-400 mb-0.5">№ удостоверения</div>
              <div class="text-sm font-mono text-gray-700 break-all">{{ cert.certificate_number }}</div>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <div class="text-xs text-gray-400 mb-0.5">Дата выдачи</div>
              <div class="text-sm font-medium text-gray-800">{{ formatDate(cert.issued_date) }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-400 mb-0.5">Действительно до</div>
              <div class="text-sm font-bold" :class="{
                'text-green-700': cert.status === 'active',
                'text-orange-600': cert.status === 'expiring_soon',
                'text-red-600': cert.status === 'expired',
              }">{{ formatDate(cert.valid_until) }}</div>
            </div>
          </div>
          <div v-if="cert.protocol_number">
            <div class="text-xs text-gray-400 mb-0.5">Протокол</div>
            <div class="text-sm font-mono text-gray-700">№ {{ cert.protocol_number }}</div>
          </div>
        </div>

        <!-- Signers -->
        <div v-if="cert.signers && cert.signers.length" class="bg-white rounded-2xl shadow-sm p-5 mb-4">
          <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Подписано ЭЦП ({{ cert.signers.length }})
          </h3>
          <div class="space-y-3">
            <div v-for="(s, i) in cert.signers" :key="i" class="flex items-start gap-3">
              <div class="w-7 h-7 bg-green-100 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                <span class="text-green-700 text-xs">✓</span>
              </div>
              <div>
                <div class="text-sm font-medium text-gray-800">{{ s.full_name }}</div>
                <div class="text-xs text-gray-500 capitalize">{{ s.role }}</div>
                <div v-if="s.cert_owner" class="text-xs text-gray-400 font-mono">{{ s.cert_owner }}</div>
                <div v-if="s.signed_at" class="text-xs text-gray-400">{{ formatDateTime(s.signed_at) }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-4 text-center text-xs text-gray-400">
          Данные проверены на портале Özen-Prom
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const cert = ref(null)
const loading = ref(true)
const error = ref(false)

onMounted(async () => {
  try {
    const res = await api.get(`/verify/${route.params.id}`)
    cert.value = res.data
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

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>
