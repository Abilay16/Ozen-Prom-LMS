<template>
  <div class="min-h-screen bg-gray-100 py-8 px-4 print:bg-white print:py-0 print:px-0"
       :class="{ 'bg-white py-0 px-0': isPrintMode }">
    <!-- Toolbar (hidden on print and in standalone print mode) -->
    <div v-if="!isPrintMode" class="max-w-2xl mx-auto mb-4 flex gap-3 print:hidden">
      <button @click="$router.back()" class="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"><ChevronLeft :size="16" /> Назад</button>
      <template v-if="isBiot">
        <button @click="printCert()" class="ml-auto inline-flex items-center gap-1.5 bg-white border border-gray-300 text-gray-700 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
          <Printer :size="16" /> Печать
        </button>
        <button @click="doSavePdf()" :disabled="saving || loading" class="inline-flex items-center gap-1.5 bg-brand-dark text-white text-sm px-4 py-2 rounded-lg hover:bg-opacity-90 disabled:opacity-60">
          <Download :size="16" /> {{ saving ? 'Готовим PDF…' : 'Скачать PDF' }}
        </button>
      </template>
      <button v-else @click="printCert()" class="ml-auto bg-brand-dark text-white text-sm px-4 py-2 rounded-lg hover:bg-opacity-90">
        <Printer :size="16" class="inline -mt-0.5 mr-1" /> Распечатать / Скачать PDF
      </button>
    </div>
    <p v-if="saveError" class="max-w-2xl mx-auto mb-3 text-sm text-red-600 no-print">{{ saveError }}</p>

    <!-- Standalone print mode toolbar -->
    <div v-if="isPrintMode" class="no-print flex gap-3 p-4 bg-gray-100 border-b mb-4">
      <button @click="router.back()" class="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800"><ChevronLeft :size="16" /> Назад</button>
      <!-- window в шаблоне Vue недоступен — раньше эта кнопка не работала -->
      <button @click="printNow" class="inline-flex items-center gap-1.5 text-sm bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700"><Printer :size="16" /> Печать</button>
      <button @click="doSavePdf()" :disabled="saving" class="inline-flex items-center gap-1.5 text-sm bg-green-600 text-white px-4 py-1.5 rounded hover:bg-green-700 disabled:opacity-60"><Download :size="16" /> {{ saving ? 'Готовим PDF…' : 'Скачать PDF' }}</button>
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
import { ChevronLeft, Download, Printer } from 'lucide-vue-next'
import { isBiotItrCertificate } from '@/utils/certKind'
import { downloadBiotCertificatePdf } from '@/utils/certificatePdf'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const cert = ref(null)
const loading = ref(true)
const protocol = ref(null)
const qrDataUrl = ref('')

const saving = ref(false)
const saveError = ref('')

const isPrintMode = computed(() => route.meta?.printMode === true)
const isBiot = computed(() => !!cert.value && isBiotItrCertificate(cert.value))

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
    // Протокол с подписями комиссии (основание + штамп ЭЦП). Берём из
    // публичной проверки: она доступна любой роли. Раньше обучающийся
    // запрашивал админский адрес, получал 403 — и документ был без штампа.
    if (res.data.protocol_id) {
      try {
        protocol.value = (await api.get(`/verify/${res.data.id}`)).data.protocol
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

function printNow() {
  window.print()
}

async function doSavePdf() {
  const name = `${isBiot.value ? 'Сертификат' : 'Удостоверение'}_${cert.value?.certificate_number || route.params.id}`
  // Сертификат БиОТ ИТР — сразу файлом PDF.
  if (isBiot.value) {
    saving.value = true
    saveError.value = ''
    try {
      await downloadBiotCertificatePdf(name)
    } catch {
      saveError.value = 'Не удалось сформировать PDF. Попробуйте «Печать» → «Сохранить как PDF».'
    } finally {
      saving.value = false
    }
    return
  }
  // Остальные удостоверения — через печать; имя файла по номеру документа.
  const prev = document.title
  document.title = name
  window.print()
  document.title = prev
}
</script>

<style scoped>
@media print {
  .no-print { display: none !important; }
}

</style>
