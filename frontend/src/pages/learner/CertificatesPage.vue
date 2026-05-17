<template>
  <div class="max-w-2xl mx-auto py-6">
    <h1 class="text-xl font-bold text-gray-800 mb-6">Мои удостоверения</h1>

    <!-- QR worker card section -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
      <div class="flex items-start gap-4">
        <!-- QR canvas -->
        <div class="shrink-0">
          <canvas ref="qrCanvas" class="rounded-lg border border-gray-200" style="width:110px;height:110px"></canvas>
        </div>
        <!-- Info + buttons -->
        <div class="flex-1 min-w-0">
          <div class="font-semibold text-gray-800 mb-0.5">📱 Карточка работника</div>
          <div class="text-xs text-gray-500 mb-3">Сканируйте QR — инспектор увидит все ваши допуски сразу</div>
          <div class="flex flex-wrap gap-2">
            <button
              @click="downloadQrPng"
              :disabled="!verifyToken"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-medium hover:bg-blue-700 disabled:opacity-40 transition-colors"
            >⬇️ Скачать PNG</button>
            <button
              @click="printPlasticCard"
              :disabled="!verifyToken"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-700 text-white text-xs font-medium hover:bg-gray-800 disabled:opacity-40 transition-colors"
            >🖶 Пластиковая карта</button>
          </div>
          <div class="mt-2 text-xs text-gray-400">
            PNG — сохраните в телефон &middot; Пластик — распечатайте 85×54 мм
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-400">Загрузка...</div>

    <div v-else-if="certs.length === 0" class="text-center py-12 text-gray-400">
      У вас пока нет удостоверений о проверке знаний.
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="c in certs"
        :key="c.id"
        class="bg-white rounded-xl shadow-sm p-5 border-l-4"
        :class="isExpired(c.valid_until) ? 'border-red-400' : isExpiringSoon(c.valid_until) ? 'border-orange-400' : 'border-green-400'"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="px-2 py-0.5 rounded text-xs font-medium" :class="typeClass(c.training_type?.code)">
                {{ c.training_type?.name_short ?? 'Удостоверение' }}
              </span>
              <span v-if="isExpired(c.valid_until)" class="px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-600">Истекло</span>
              <span v-else-if="isExpiringSoon(c.valid_until)" class="px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-600">Скоро истекает</span>
              <span v-else class="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-600">Действительно</span>
            </div>
            <div class="text-sm font-medium text-gray-800">{{ c.training_type?.name_ru ?? 'Проверка знаний' }}</div>
            <div class="text-xs text-gray-500 mt-1 font-mono">{{ c.certificate_number }}</div>
            <div v-if="c.organization_name" class="text-xs text-gray-500 mt-1">{{ c.organization_name }}</div>
          </div>
          <div class="text-right text-xs text-gray-500 shrink-0">
            <div>Выдано: <span class="font-medium text-gray-700">{{ formatDate(c.issued_date) }}</span></div>
            <div class="mt-0.5">Действует до: <span class="font-medium" :class="isExpired(c.valid_until) ? 'text-red-600' : isExpiringSoon(c.valid_until) ? 'text-orange-500' : 'text-gray-700'">{{ formatDate(c.valid_until) }}</span></div>
            <router-link :to="`/my/certificates/${c.id}`" class="mt-2 inline-block text-blue-600 hover:underline font-medium">
              📄 Открыть / Напечатать
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- ─── Прочие документы ──────────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mt-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-semibold text-gray-800">📎 Прочие документы</h2>
        <button
          @click="showDocUpload = !showDocUpload"
          class="text-xs px-3 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >+ Загрузить</button>
      </div>

      <!-- Upload form -->
      <div v-if="showDocUpload" class="mb-4 p-4 bg-gray-50 rounded-xl space-y-3">
        <div>
          <label class="block text-xs text-gray-600 mb-1">Название документа</label>
          <input
            v-model="docTitle"
            type="text"
            placeholder="Например: Удостоверение по электробезопасности"
            class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-600 mb-1">Файл (PDF, изображение, Word, Excel — до 20 МБ)</label>
          <input
            ref="docFileInput"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.xls,.xlsx"
            class="w-full text-sm text-gray-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 file:text-xs file:font-medium hover:file:bg-blue-100"
          />
        </div>
        <div class="flex gap-2">
          <button
            @click="uploadDoc"
            :disabled="docUploading"
            class="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >{{ docUploading ? 'Загрузка...' : 'Сохранить' }}</button>
          <button
            @click="showDocUpload = false; docTitle = ''; docFileInput && (docFileInput.value = '')"
            class="px-4 py-1.5 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors"
          >Отмена</button>
        </div>
        <div v-if="docError" class="text-xs text-red-600">{{ docError }}</div>
      </div>

      <!-- Document list -->
      <div v-if="userDocs.length === 0" class="text-sm text-gray-400 py-2">Нет загруженных документов</div>
      <div v-else class="divide-y divide-gray-100">
        <div v-for="d in userDocs" :key="d.id" class="flex items-center justify-between py-2.5">
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-800 truncate">{{ d.title }}</div>
            <div class="text-xs text-gray-400 mt-0.5">{{ d.original_filename }} &middot; {{ formatDate(d.uploaded_at) }}</div>
          </div>
          <div class="flex gap-2 ml-3 shrink-0">
            <a
              :href="docDownloadUrl(d.id)"
              target="_blank"
              class="text-xs px-2.5 py-1 rounded bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
            >⬇ Скачать</a>
            <button
              @click="deleteDoc(d.id)"
              class="text-xs px-2.5 py-1 rounded bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
            >🗑</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ─── Медосмотр ─────────────────────────────────────── -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mt-4 mb-6">
      <h2 class="text-base font-semibold text-gray-800 mb-4">🏥 Медицинский осмотр</h2>
      <div v-if="medExams.length === 0" class="text-sm text-gray-400 py-2">
        Данные о медосмотре отсутствуют
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="m in medExams"
          :key="m.id"
          class="rounded-xl border border-gray-100 p-4 bg-gray-50"
        >
          <div class="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <div>
              <span class="text-xs text-gray-500">Дата осмотра:</span>
              <span class="ml-1 font-medium text-gray-800">{{ formatDate(m.exam_date) }}</span>
            </div>
            <div>
              <span class="text-xs text-gray-500">Заключение:</span>
              <span
                class="ml-1 px-2 py-0.5 rounded text-xs font-medium"
                :class="m.fit_for_work === true ? 'bg-green-100 text-green-700' : m.fit_for_work === false ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'"
              >
                {{ m.fit_for_work === true ? 'Годен' : m.fit_for_work === false ? 'Не годен' : 'Не указано' }}
              </span>
            </div>
            <div v-if="m.icd10_group">
              <span class="text-xs text-gray-500">МКБ-10:</span>
              <span class="ml-1 text-gray-700">{{ m.icd10_group }}</span>
            </div>
            <div v-if="m.workplace">
              <span class="text-xs text-gray-500">Объект/участок:</span>
              <span class="ml-1 text-gray-700">{{ m.workplace }}</span>
            </div>
            <div v-if="m.position">
              <span class="text-xs text-gray-500">Должность:</span>
              <span class="ml-1 text-gray-700">{{ m.position }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import QRCode from 'qrcode'
import api from '@/services/api'

const certs = ref([])
const loading = ref(true)
const verifyToken = ref(null)
const meData = ref(null)
const qrCanvas = ref(null)

// Прочие документы
const userDocs = ref([])
const showDocUpload = ref(false)
const docTitle = ref('')
const docFileInput = ref(null)
const docUploading = ref(false)
const docError = ref('')

// Медосмотры
const medExams = ref([])

onMounted(async () => {
  try {
    const [certsRes, meRes, docsRes, medRes] = await Promise.all([
      api.get('/learner/certificates'),
      api.get('/learner/me'),
      api.get('/learner/documents'),
      api.get('/learner/medical-exams'),
    ])
    certs.value = certsRes.data
    meData.value = meRes.data
    verifyToken.value = meRes.data.verify_token
    userDocs.value = docsRes.data
    medExams.value = medRes.data
  } finally {
    loading.value = false
    if (verifyToken.value) {
      await nextTick()
      generateQr()
    }
  }
})

function docDownloadUrl(docId) {
  return `/api/v1/learner/documents/${docId}/download`
}

async function uploadDoc() {
  docError.value = ''
  if (!docTitle.value.trim()) { docError.value = 'Укажите название документа'; return }
  const file = docFileInput.value?.files?.[0]
  if (!file) { docError.value = 'Выберите файл'; return }
  docUploading.value = true
  try {
    const form = new FormData()
    form.append('title', docTitle.value.trim())
    form.append('file', file)
    const res = await api.post('/learner/documents', form, { headers: { 'Content-Type': 'multipart/form-data' } })
    userDocs.value.unshift(res.data)
    showDocUpload.value = false
    docTitle.value = ''
    if (docFileInput.value) docFileInput.value.value = ''
  } catch (e) {
    docError.value = e.response?.data?.detail ?? 'Ошибка загрузки'
  } finally {
    docUploading.value = false
  }
}

async function deleteDoc(id) {
  if (!confirm('Удалить документ?')) return
  try {
    await api.delete(`/learner/documents/${id}`)
    userDocs.value = userDocs.value.filter(d => d.id !== id)
  } catch {
    alert('Ошибка удаления')
  }
}

function workerCardUrl() {
  return `${window.location.origin}/verify/worker/${verifyToken.value}`
}

function generateQr() {
  if (!qrCanvas.value || !verifyToken.value) return
  QRCode.toCanvas(qrCanvas.value, workerCardUrl(), {
    width: 220,
    margin: 1,
    color: { dark: '#1e3a5f', light: '#ffffff' },
  })
}

function downloadQrPng() {
  if (!qrCanvas.value) return
  const dataUrl = qrCanvas.value.toDataURL('image/png')
  const a = document.createElement('a')
  a.href = dataUrl
  a.download = `qr-${meData.value?.full_name ?? 'worker'}.png`
  a.click()
}

function printPlasticCard() {
  if (!qrCanvas.value || !verifyToken.value) return
  const qrDataUrl = qrCanvas.value.toDataURL('image/png')
  const fullName = meData.value?.full_name ?? ''
  const position = meData.value?.position ?? ''
  const orgName = meData.value?.organization_name ?? ''
  const url = workerCardUrl()

  const win = window.open('', '_blank', 'width=500,height=350')
  win.document.write(`<!DOCTYPE html>
<html><head>
  <meta charset="utf-8">
  <title>Карточка работника</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    @page { size: 85.6mm 54mm; margin: 0; }
    html, body { width:85.6mm; height:54mm; overflow:hidden; }
    .card {
      width:85.6mm; height:54mm;
      display:flex; font-family:Arial,sans-serif;
    }
    .stripe {
      background:#1d4ed8; color:#fff;
      width:22mm; display:flex; flex-direction:column;
      align-items:center; justify-content:center; padding:3mm;
    }
    .qr { width:15mm; height:15mm; border-radius:2px; }
    .brand { font-size:6.5pt; font-weight:bold; text-align:center;
             letter-spacing:.5px; margin-top:2mm; line-height:1.2; }
    .body {
      flex:1; padding:4mm 4mm 3mm 4mm;
      display:flex; flex-direction:column; justify-content:space-between;
    }
    .label { font-size:5pt; color:#9ca3af; text-transform:uppercase;
             letter-spacing:.5px; margin-bottom:.5mm; }
    .title { font-size:5.5pt; font-weight:bold; color:#374151; margin-bottom:2mm; }
    .name { font-size:9pt; font-weight:bold; color:#111827; line-height:1.2; }
    .pos  { font-size:6pt; color:#4b5563; margin-top:1mm; }
    .org  { font-size:5.5pt; color:#6b7280; margin-top:.5mm; }
    .hint { font-size:5pt; color:#9ca3af; }
    .divider { height:.2mm; background:#e5e7eb; margin:2mm 0; }
  </style>
</head><body>
<div class="card">
  <div class="stripe">
    <img src="${qrDataUrl}" class="qr">
    <div class="brand">ÖZEN<br>PROM</div>
  </div>
  <div class="body">
    <div>
      <div class="label">удостоверение работника</div>
      <div class="divider"></div>
      <div class="name">${fullName}</div>
      <div class="pos">${position}</div>
      <div class="org">${orgName}</div>
    </div>
    <div class="hint">Отсканируйте QR для проверки допусков</div>
  </div>
</div>
<script>window.onload=function(){window.print()}<\/script>
</body></html>`)
  win.document.close()
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU')
}

function isExpired(d) {
  if (!d) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return new Date(d + 'T00:00:00') < today
}

function isExpiringSoon(d) {
  if (!d) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expires = new Date(d + 'T00:00:00')
  const diff = expires - today
  return diff >= 0 && diff < 90 * 24 * 60 * 60 * 1000
}

function typeClass(code) {
  return {
    biot: 'bg-blue-100 text-blue-700',
    ptm: 'bg-orange-100 text-orange-700',
    prombez: 'bg-purple-100 text-purple-700',
  }[code] ?? 'bg-gray-100 text-gray-600'
}
</script>
