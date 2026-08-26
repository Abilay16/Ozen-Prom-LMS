<template>
  <div class="min-h-screen bg-gray-100 py-8 px-4 print:bg-white print:py-0 print:px-0"
       :class="{ 'bg-white py-0 px-0': isPrintMode }">
    <!-- Toolbar (hidden on print and in standalone print mode) -->
    <div v-if="!isPrintMode" class="max-w-2xl mx-auto mb-4 flex gap-3 print:hidden">
      <button @click="$router.back()" class="text-sm text-gray-500 hover:text-gray-700">← Назад</button>
      <button @click="printCert()" class="ml-auto bg-brand-dark text-white text-sm px-4 py-2 rounded-lg hover:bg-opacity-90">
        🖨 Распечатать / Скачать PDF
      </button>
    </div>

    <!-- Standalone print mode toolbar -->
    <div v-if="isPrintMode" class="no-print flex gap-3 p-4 bg-gray-100 border-b mb-4">
      <button @click="router.back()" class="text-sm text-gray-600 hover:text-gray-800">← Назад</button>
      <button @click="window.print()" class="text-sm bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700">🖨 Печать</button>
      <button @click="doSavePdf()" class="text-sm bg-green-600 text-white px-4 py-1.5 rounded hover:bg-green-700">⬇ Скачать PDF</button>
    </div>

    <div v-if="loading" class="max-w-2xl mx-auto text-center py-20 text-gray-400 no-print">Загрузка...</div>
    <div v-else-if="!cert" class="max-w-2xl mx-auto text-center py-20 text-red-500">Удостоверение не найдено</div>

    <!-- Certificate body -->
    <CertificateDocument
      v-if="cert && !loading"
      :cert="cert"
      :protocol="protocol"
      :qr-data-url="qrDataUrl"
      :verify-url="verifyUrl"
    />
  </div><!-- /min-h-screen -->
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import CertificateDocument from '@/components/CertificateDocument.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const cert = ref(null)
const loading = ref(true)
const protocol = ref(null)
const qrDataUrl = ref('')

const isPrintMode = computed(() => route.meta?.printMode === true)

const verifyUrl = computed(() =>
  `ozenlms.kz/verify/${cert.value?.id ?? ''}`
)

onMounted(async () => {
  try {
    // Works for both learner (/learner/certificates/:id) and admin (/admin/certificates/:id)
    const isAdmin = auth.role === 'admin'
    const endpoint = isAdmin
      ? `/admin/certificates/${route.params.id}`
      : `/learner/certificates/${route.params.id}`
    const res = await api.get(endpoint)
    cert.value = res.data

    // Generate QR code pointing to the verify page
    try {
      const verifyLink = `${window.location.origin}/verify/${res.data.id}`
      qrDataUrl.value = await QRCode.toDataURL(verifyLink, {
        width: 80, margin: 1,
        color: { dark: '#1a3a5c', light: '#ffffff' },
      })
    } catch { /* non-critical */ }
    // Load protocol data (for basis text + all commission signatures)
    if (res.data.protocol_id) {
      try {
        const endpoint2 = isAdmin
          ? `/admin/protocols/${res.data.protocol_id}`
          : `/admin/protocols/${res.data.protocol_id}`
        const protoRes = await api.get(endpoint2)
        protocol.value = protoRes.data
      } catch { /* not critical */ }
    }
  } catch {
    cert.value = null
  } finally {
    loading.value = false
    if (isPrintMode.value) {
      await nextTick()
      window.print()
    }
  }
})

function printCert() {
  router.push(`/print/certificate/${route.params.id}`)
}

function doSavePdf() {
  const prev = document.title
  document.title = `Удостоверение_${cert.value?.certificate_number || route.params.id}`
  window.print()
  document.title = prev
}
</script>

<style scoped>
@media print {
  .no-print { display: none !important; }
}

</style>
