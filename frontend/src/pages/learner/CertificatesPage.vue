<template>
  <div>
    <header class="page-head">
      <h1 class="page-title">Удостоверения</h1>
      <p class="page-sub">Удостоверения, документы и медосмотр — всё, что проверяющий увидит по вашему QR-коду.</p>
    </header>

    <!-- Карточка работника: на телефоне QR сверху, кнопки во всю ширину -->
    <section class="panel worker">
      <div class="worker__qr">
        <canvas ref="qrCanvas" class="worker__canvas" aria-label="QR-код карточки работника"></canvas>
      </div>
      <div class="worker__body">
        <h2 class="section-title"><QrCode :size="18" :stroke-width="2" /> Карточка работника</h2>
        <p class="muted">Покажите этот QR проверяющему — он увидит все ваши допуски без входа в систему.</p>
        <div class="worker__actions">
          <button type="button" class="btn btn--primary" :disabled="!verifyToken" @click="downloadQrPng">
            <Download :size="17" /> Сохранить QR
          </button>
          <button type="button" class="btn btn--ghost" :disabled="!verifyToken" @click="openCard">
            <IdCard :size="17" /> Карта работника
          </button>
        </div>
      </div>
    </section>

    <!-- Карта работника 85,6 × 54 мм: предпросмотр, печать, PDF -->
    <Modal v-model="cardOpen" title="Карта работника" max-width="max-w-xl">
      <WorkerCard
        ref="cardRef"
        :full-name="meData?.full_name"
        :position="meData?.position"
        :photo-url="meData?.photo_url"
        :qr-data-url="cardQr"
      />
      <p class="muted mt-3">
        Размер 85,6 × 54 мм — как банковская карта.
        <template v-if="!meData?.photo_url">Фото пока не загружено — его добавляет администратор.</template>
      </p>
      <template #footer>
        <button type="button" class="btn btn--primary flex-1" :disabled="!!cardBusy" @click="cardAction('pdf')">
          <Download :size="17" /> {{ cardBusy === 'pdf' ? 'Готовим PDF…' : 'Скачать PDF' }}
        </button>
        <button type="button" class="btn btn--ghost flex-1" :disabled="!!cardBusy" @click="cardAction('print')">
          <Printer :size="17" /> {{ cardBusy === 'print' ? 'Готовим…' : 'Печать' }}
        </button>
      </template>
    </Modal>

    <!-- Удостоверения -->
    <h2 class="group-title">Выданные удостоверения</h2>
    <div v-if="loading" class="space-y-2">
      <span v-for="i in 2" :key="i" class="skel" style="display:block; width: 100%; height: 5.5rem; border-radius: 0.9rem;" />
    </div>
    <div v-else-if="certs.length === 0" class="empty">
      <Award :size="26" :stroke-width="1.6" class="empty__icon" />
      <p class="empty__title">Удостоверений пока нет</p>
      <p class="empty__text">Они появятся здесь после сдачи теста и подписания протокола комиссией.</p>
    </div>
    <div v-else class="space-y-2">
      <RouterLink
        v-for="c in certs"
        :key="c.id"
        :to="`/my/certificates/${c.id}`"
        class="cert"
        :class="`cert--${certState(c.valid_until)}`"
      >
        <div class="cert__main">
          <div class="cert__chips">
            <span class="type-chip" :class="typeClass(c.training_type?.code)">{{ c.training_type?.name_short ?? 'Удостоверение' }}</span>
            <span class="state-chip">
              <component :is="STATE[certState(c.valid_until)].icon" :size="13" :stroke-width="2.4" />
              {{ STATE[certState(c.valid_until)].label }}
            </span>
          </div>
          <div class="cert__name">{{ c.training_type?.name_ru ?? 'Проверка знаний' }}</div>
          <div class="cert__meta">
            <span>№ <span class="font-mono">{{ c.certificate_number }}</span></span>
            <span>до {{ formatDate(c.valid_until) }}</span>
          </div>
        </div>
        <ChevronRight :size="20" class="cert__chev" />
      </RouterLink>
    </div>

    <!-- Прочие документы -->
    <section class="panel mt-6">
      <div class="flex items-center justify-between gap-3 mb-3">
        <h2 class="section-title"><Paperclip :size="18" :stroke-width="2" /> Прочие документы</h2>
        <button v-if="!showDocUpload" type="button" class="btn btn--ghost btn--sm" @click="showDocUpload = true">
          <Upload :size="16" /> Загрузить
        </button>
      </div>
      <p class="muted mb-3">Например, удостоверения, выданные в другом учебном центре. Их тоже увидит проверяющий по QR.</p>

      <div v-if="showDocUpload" class="upload">
        <label class="field">
          <span class="field__label">Название документа</span>
          <input v-model="docTitle" type="text" placeholder="Например: Удостоверение по электробезопасности" class="input-field" />
        </label>
        <label class="field">
          <span class="field__label">Файл — PDF, фото, Word или Excel, до 20 МБ</span>
          <input
            ref="docFileInput" type="file" accept=".pdf,.png,.jpg,.jpeg,.gif,.webp,.doc,.docx,.xls,.xlsx"
            class="w-full text-sm text-gray-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 file:text-sm file:font-medium"
          />
        </label>
        <p v-if="docError" class="text-sm text-red-600">{{ docError }}</p>
        <div class="flex gap-2">
          <button type="button" class="btn btn--primary" :disabled="docUploading" @click="uploadDoc">
            {{ docUploading ? 'Загружаем…' : 'Сохранить' }}
          </button>
          <button type="button" class="btn btn--ghost" @click="showDocUpload = false; docTitle = ''; docError = ''; docFileInput && (docFileInput.value = '')">
            Отмена
          </button>
        </div>
      </div>

      <p v-if="userDocs.length === 0 && !showDocUpload" class="text-sm text-gray-400">Документы не загружены</p>
      <ul v-else-if="userDocs.length" class="docs">
        <li v-for="d in userDocs" :key="d.id" class="doc">
          <FileText :size="20" :stroke-width="1.8" class="doc__icon" />
          <div class="doc__text">
            <div class="doc__title">{{ d.title }}</div>
            <div class="doc__meta">{{ d.original_filename }} · {{ formatDate(d.uploaded_at) }}</div>
          </div>
          <button type="button" class="icon-btn" :title="`Скачать «${d.title}»`" :aria-label="`Скачать «${d.title}»`" @click="downloadDoc(d)">
            <Download :size="18" />
          </button>
          <button type="button" class="icon-btn icon-btn--danger" :title="`Удалить «${d.title}»`" :aria-label="`Удалить «${d.title}»`" @click="deleteDoc(d.id)">
            <Trash2 :size="18" />
          </button>
        </li>
      </ul>
    </section>

    <!-- Медосмотр -->
    <section class="panel">
      <h2 class="section-title mb-3"><Stethoscope :size="18" :stroke-width="2" /> Медицинский осмотр</h2>
      <p v-if="medExams.length === 0" class="text-sm text-gray-400">Данных о медосмотре нет</p>
      <div v-else class="space-y-2">
        <div v-for="m in medExams" :key="m.id" class="med">
          <div class="flex items-center justify-between gap-3">
            <span class="text-sm text-gray-600">Осмотр {{ formatDate(m.exam_date) }}</span>
            <span class="fit" :class="m.fit_for_work === true ? 'fit--ok' : m.fit_for_work === false ? 'fit--bad' : ''">
              {{ m.fit_for_work === true ? 'Годен' : m.fit_for_work === false ? 'Не годен' : 'Не указано' }}
            </span>
          </div>
          <dl class="med__rows">
            <div v-if="m.position"><dt>Должность</dt><dd>{{ m.position }}</dd></div>
            <div v-if="m.workplace"><dt>Объект / участок</dt><dd>{{ m.workplace }}</dd></div>
            <div v-if="m.icd10_group"><dt>МКБ-10</dt><dd>{{ m.icd10_group }}</dd></div>
          </dl>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import QRCode from 'qrcode'
import api from '@/services/api'
import { RouterLink } from 'vue-router'
import {
  Award, ChevronRight, CircleCheck, CircleX, Clock, Download, FileText, IdCard, Paperclip,
  Printer, QrCode, Stethoscope, Trash2, Upload,
} from 'lucide-vue-next'
import Modal from '@/components/Modal.vue'
import WorkerCard from '@/components/WorkerCard.vue'
import { downloadWorkerCardPdf, printWorkerCard, workerCardImage } from '@/utils/certificatePdf'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'

const toast = useToast()
const { confirm } = useConfirm()

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

// Скачивание через API с токеном: раньше это была обычная ссылка, сервер
// без токена отвечал 401 — свой документ скачать было нельзя.
async function downloadDoc(d) {
  try {
    const { data } = await api.get(`/learner/documents/${d.id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = d.original_filename || d.title || 'document'
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) {
    toast.error(apiErrorMessage(e))
  }
}

function certState(validUntil) {
  if (isExpired(validUntil)) return 'expired'
  if (isExpiringSoon(validUntil)) return 'soon'
  return 'ok'
}

const STATE = {
  ok: { label: 'Действует', icon: CircleCheck },
  soon: { label: 'Скоро истекает', icon: Clock },
  expired: { label: 'Истекло', icon: CircleX },
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
  const ok = await confirm({ message: 'Удалить документ?', danger: true, confirmText: 'Удалить' })
  if (!ok) return
  try {
    await api.delete(`/learner/documents/${id}`)
    userDocs.value = userDocs.value.filter(d => d.id !== id)
    toast.success('Документ удалён')
  } catch {
    toast.error('Ошибка удаления')
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

// ── Карта работника ─────────────────────────────────────────────────────────
const cardOpen = ref(false)
const cardRef = ref(null)
const cardQr = ref('')
const cardBusy = ref('')

async function openCard() {
  if (!verifyToken.value) return
  if (!cardQr.value) {
    cardQr.value = await QRCode.toDataURL(workerCardUrl(), {
      width: 780, margin: 0, errorCorrectionLevel: 'M',
      color: { dark: '#0b2a5b', light: '#ffffff' },
    })
  }
  cardOpen.value = true
}

async function cardAction(kind) {
  const card = cardRef.value
  if (!card) return
  cardBusy.value = kind
  try {
    const img = await workerCardImage(card.node(), card.W, card.H)
    if (kind === 'pdf') {
      await downloadWorkerCardPdf(img, `Карта_${(meData.value?.full_name || 'работника').replace(/\s+/g, '_')}`)
    } else {
      printWorkerCard(img)
    }
  } catch {
    toast.error('Не удалось подготовить карту. Попробуйте ещё раз.')
  } finally {
    cardBusy.value = ''
  }
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

<style scoped>
.page-head { margin-bottom: 1.1rem; }
.page-title { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.015em; color: #101828; }
.page-sub { margin-top: 0.3rem; font-size: 0.9rem; color: #5b6475; text-wrap: pretty; }
.panel { background: #fff; border: 1px solid #e7e9ee; border-radius: 0.9rem; padding: 1.15rem; margin-bottom: 0.85rem; }
@media (min-width: 640px) { .panel { padding: 1.35rem 1.5rem; } }
.section-title { display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; font-weight: 650; color: #101828; }
.section-title svg { color: #1f4f96; }
.group-title { margin: 1.4rem 0 0.6rem; font-size: 0.78rem; font-weight: 650; letter-spacing: 0.05em; text-transform: uppercase; color: #6b7280; }
.muted { font-size: 0.875rem; color: #6b7280; text-wrap: pretty; }

/* Карточка работника */
.worker { display: flex; flex-direction: column; align-items: center; gap: 1rem; text-align: center; }
.worker__canvas { width: 168px !important; height: 168px !important; border-radius: 0.6rem; border: 1px solid #e7e9ee; display: block; }
.worker__body { width: 100%; display: flex; flex-direction: column; align-items: center; gap: 0.4rem; }
.worker__actions { margin-top: 0.5rem; width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
@media (min-width: 640px) {
  .worker { flex-direction: row; align-items: center; text-align: left; gap: 1.5rem; }
  .worker__canvas { width: 132px !important; height: 132px !important; }
  .worker__body { align-items: flex-start; }
  .worker__actions { width: auto; display: flex; }
}

.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.4rem;
  padding: 0.65rem 0.9rem; border-radius: 0.65rem; font-size: 0.875rem; font-weight: 600; white-space: nowrap;
  transition: background-color 0.15s ease;
}
.btn--sm { padding: 0.45rem 0.7rem; }
.btn--primary { background: #2563eb; color: #fff; }
.btn--primary:hover:not(:disabled) { background: #1d4ed8; }
.btn--ghost { background: #fff; border: 1px solid #d5dae3; color: #1f3a5c; }
.btn--ghost:hover:not(:disabled) { background: #f6f7f9; }
.btn:disabled { opacity: 0.5; }
.btn:focus-visible, .icon-btn:focus-visible, .cert:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }

/* Удостоверения */
.cert {
  display: flex; align-items: center; gap: 0.75rem;
  background: #fff; border: 1px solid #e7e9ee; border-radius: 0.9rem;
  padding: 0.9rem 0.9rem 0.9rem 1.05rem; text-decoration: none; color: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.cert:hover { border-color: #c9d3e3; box-shadow: 0 6px 18px -12px rgba(31, 58, 92, 0.4); }
.cert--ok { box-shadow: inset 3px 0 0 #16a34a; }
.cert--soon { box-shadow: inset 3px 0 0 #d97706; }
.cert--expired { box-shadow: inset 3px 0 0 #dc2626; }
.cert__main { flex: 1; min-width: 0; }
.cert__chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.type-chip { padding: 0.12rem 0.5rem; border-radius: 0.4rem; font-size: 0.72rem; font-weight: 650; }
.state-chip { display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.12rem 0.45rem; border-radius: 999px; font-size: 0.72rem; font-weight: 600; }
.cert--ok .state-chip { background: #e7f6ee; color: #11683f; }
.cert--soon .state-chip { background: #fff4e0; color: #9a5b00; }
.cert--expired .state-chip { background: #fdecec; color: #a12a1f; }
.cert__name { margin-top: 0.45rem; font-weight: 600; color: #101828; }
.cert__meta { margin-top: 0.2rem; display: flex; flex-wrap: wrap; gap: 0.25rem 0.9rem; font-size: 0.78rem; color: #6b7280; }
.cert__chev { color: #a3abb8; flex-shrink: 0; }

.empty { background: #fff; border: 1px dashed #d5dae3; border-radius: 0.9rem; padding: 1.75rem 1.25rem; text-align: center; }
.empty__icon { margin: 0 auto 0.6rem; color: #8a93a3; }
.empty__title { font-weight: 600; color: #101828; }
.empty__text { margin-top: 0.25rem; font-size: 0.85rem; color: #6b7280; }

/* Документы */
.upload { display: flex; flex-direction: column; gap: 0.75rem; padding: 0.9rem; margin-bottom: 0.85rem; background: #f6f7f9; border-radius: 0.75rem; }
.field { display: flex; flex-direction: column; gap: 0.3rem; }
.field__label { font-size: 0.8rem; color: #4b5565; }
.docs { display: flex; flex-direction: column; }
.doc { display: flex; align-items: center; gap: 0.7rem; padding: 0.65rem 0; border-top: 1px solid #f1f3f6; }
.doc:first-child { border-top: 0; }
.doc__icon { color: #1f4f96; flex-shrink: 0; }
.doc__text { flex: 1; min-width: 0; }
.doc__title { font-size: 0.9rem; font-weight: 550; color: #101828; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc__meta { font-size: 0.75rem; color: #8a93a3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.icon-btn { width: 2.4rem; height: 2.4rem; flex-shrink: 0; display: grid; place-items: center; border-radius: 0.6rem; color: #4b5565; }
.icon-btn:hover { background: #f1f3f6; color: #1f3a5c; }
.icon-btn--danger:hover { background: #fdecec; color: #b42318; }

/* Медосмотр */
.med { border: 1px solid #eef0f4; border-radius: 0.75rem; padding: 0.75rem 0.85rem; }
.fit { padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.75rem; font-weight: 650; background: #f1f3f6; color: #4b5565; }
.fit--ok { background: #e7f6ee; color: #11683f; }
.fit--bad { background: #fdecec; color: #a12a1f; }
.med__rows { margin-top: 0.45rem; display: flex; flex-direction: column; gap: 0.2rem; }
.med__rows > div { display: flex; gap: 0.5rem; font-size: 0.82rem; }
.med__rows dt { color: #8a93a3; min-width: 7.5rem; }
.med__rows dd { color: #1f2937; }
</style>
