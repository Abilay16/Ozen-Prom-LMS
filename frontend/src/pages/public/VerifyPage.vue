<template>
  <div class="min-h-screen bg-gray-100">

    <!-- Header -->
    <div class="bg-blue-700 text-white px-4 py-4 text-center shadow print:hidden">
      <div class="text-base font-bold tracking-widest">ÖZEN-PROM</div>
      <div class="text-xs opacity-70 mt-0.5">Проверка удостоверения</div>
    </div>

    <div v-if="loading" class="text-center py-16 text-gray-400 text-sm">Проверяем удостоверение...</div>

    <div v-else-if="error" class="max-w-sm mx-auto px-4 py-6">
      <div class="bg-white rounded-2xl shadow p-8 text-center">
        <div class="text-5xl mb-4">❌</div>
        <h2 class="text-xl font-bold text-red-600 mb-2">Недействительно</h2>
        <p class="text-gray-500 text-sm">Удостоверение не найдено или отозвано.</p>
      </div>
    </div>

    <template v-else>
      <div class="max-w-2xl mx-auto px-4 pt-4">
        <!-- Status banner -->
        <div
          class="rounded-2xl p-4 mb-4 text-center font-semibold text-sm shadow-sm print:hidden"
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
      </div>

      <!-- Actual certificate document -->
      <div class="pb-8 px-4">
        <CertificateDocument
          :cert="cert"
          :protocol="cert.protocol"
          :qr-data-url="qrDataUrl"
          :verify-url="verifyUrl"
        />
      </div>

      <div class="pb-6 text-center text-xs text-gray-400 print:hidden">
        Данные проверены на портале Özen-Prom
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import QRCode from 'qrcode'
import api from '@/services/api'
import CertificateDocument from '@/components/CertificateDocument.vue'

const route = useRoute()
const cert = ref(null)
const loading = ref(true)
const error = ref(false)
const qrDataUrl = ref('')

const verifyUrl = computed(() =>
  `ozenlms.kz/verify/${cert.value?.id ?? ''}`
)

onMounted(async () => {
  try {
    const res = await api.get(`/verify/${route.params.id}`)
    cert.value = res.data

    try {
      const verifyLink = `${window.location.origin}/verify/${res.data.id}`
      qrDataUrl.value = await QRCode.toDataURL(verifyLink, {
        width: 80, margin: 1,
        color: { dark: '#1a3a5c', light: '#ffffff' },
      })
    } catch { /* non-critical */ }
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>
