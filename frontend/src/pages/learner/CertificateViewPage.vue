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
    <div v-if="cert && !loading" id="certificate">

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- ПромБез certificate (ID-card format, 2-column)          -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <template v-if="isPromBez">
        <div style="font-family:'Times New Roman',serif; font-size:12pt; color:#000; max-width:800px; margin:0 auto; border:2px solid #333;">

          <!-- Title row -->
          <div style="background:#1a3a5c; color:#fff; text-align:center; padding:8px 16px; font-size:13pt; font-weight:bold; letter-spacing:0.5px;">
            Удостоверение о проверке знаний по вопросам промышленной безопасности
          </div>

          <!-- Legal notice -->
          <div style="font-size:8pt; color:#555; font-style:italic; padding:4px 16px; border-bottom:1px solid #ccc;">
            Сноска. Приложение 5 – в редакции приказа Министра по чрезвычайным ситуациям РК от 07.10.2025 № 442 (вводится в действие с 01.01.2026).
          </div>

          <!-- Main 2-column body -->
          <div style="display:grid; grid-template-columns:1fr 1fr; border-top:2px solid #333;">

            <!-- LEFT PANEL (Panel 1 — main cert info) -->
            <div style="padding:16px; border-right:2px solid #333;">
              <div style="font-size:10pt; margin-bottom:6px;">
                <strong>1. КУӘЛІК / УДОСТОВЕРЕНИЕ № </strong>
                <span style="font-family:monospace; letter-spacing:1px;">{{ cert.certificate_number }}</span>
              </div>
              <div style="font-size:9pt; color:#555; margin-bottom:4px;">Берілді / Выдано</div>
              <div style="font-size:12pt; font-weight:bold; border-bottom:1px solid #333; padding-bottom:2px; margin-bottom:4px;">
                {{ cert.full_name }}
              </div>
              <div style="font-size:8pt; color:#555; margin-bottom:8px;">(Т.А.Ә / Ф.И.О. (при его наличии))</div>

              <div style="font-size:9pt; border-bottom:1px solid #aaa; padding-bottom:2px; margin-bottom:4px; min-height:20px;">
                {{ cert.organization_name || '' }}
              </div>
              <div style="font-size:8pt; color:#555; margin-bottom:8px;">(жұмыс орны / место работы)</div>

              <div style="font-size:9pt; border-bottom:1px solid #aaa; padding-bottom:2px; margin-bottom:4px; min-height:20px;">
                {{ cert.position || '' }}
              </div>
              <div style="font-size:8pt; color:#555; margin-bottom:12px;">(лауазымы / должность)</div>

              <!-- Photo + course info -->
              <div style="display:flex; gap:12px; margin-top:8px;">
                <div style="width:80px; height:100px; border:1px solid #aaa; flex-shrink:0; overflow:hidden; display:flex; align-items:center; justify-content:center;">
                  <img v-if="cert.photo_url" :src="cert.photo_url" style="width:100%; height:100%; object-fit:cover;" alt="Фото" />
                  <span v-else style="font-size:8pt; color:#aaa; text-align:center;">М.Ф.<br/>фото</span>
                </div>
                <div style="flex:1; font-size:9pt; line-height:1.6;">
                  <div>Ол/он (она) {{ examYear }}ж (г).</div>
                  <div>«{{ examDay }}» {{ examMonth }}</div>
                  <div style="margin-top:4px;">Курсын тыңдады / прослушал(а) курс</div>
                  <div style="border-bottom:1px solid #aaa; min-height:18px; margin-top:4px; font-weight:bold;">
                    {{ cert.training_type?.name_ru || 'Промышленная безопасность' }}
                  </div>
                </div>
              </div>

              <!-- Learning org -->
              <div style="margin-top:12px; border-top:1px solid #aaa; padding-top:6px;">
                <div style="font-size:9pt; border-bottom:1px solid #aaa; min-height:18px; padding-bottom:2px;">
                  Озен-Пром ЛМС
                </div>
                <div style="font-size:8pt; color:#555;">(оқыту ұйымы/орталығының атауы / наименование учебной организации/центра)</div>
              </div>
            </div>

            <!-- RIGHT PANEL (Panel 2 — protocol/validity/signature) -->
            <div style="padding:16px;">
              <div style="font-size:9pt; margin-bottom:8px; line-height:1.5;">
                <strong>2. Тұрақты жұмыс істейтін емтихандық комиссияның хаттамасы /</strong><br/>
                Протокол постоянно действующей экзаменационной комиссии
                № <span style="font-weight:bold;">{{ protocol ? protocol.protocol_number : '___' }}</span>
              </div>

              <div style="font-size:9pt; margin-bottom:8px;">
                «{{ examDay }}» {{ examMonth }} {{ examYear }} г.
              </div>

              <div style="font-size:9pt; margin-bottom:8px;">
                Действительно до
                <span style="font-weight:bold; color:#1a7a1a;">{{ formatDate(cert.valid_until) }}</span>
                <br/>
                <span style="font-size:8pt; color:#555;">дейін жарамды</span>
              </div>

              <div style="margin-top:16px; font-size:9pt;">
                <div>Комиссия төрағасы / Председатель комиссии</div>
                <div style="margin-top:8px;">
                  <!-- EDS stamp for chair -->
                  <template v-if="chairSignature">
                    <SignatureStamp
                      :serial="chairSignature.signer_cert_serial"
                      :owner="chairSignature.signer_cert_owner"
                      :valid-from="chairSignature.signer_cert_valid_from"
                      :valid-to="chairSignature.signer_cert_valid_to"
                      :signed-at="chairSignature.signed_at"
                    />
                  </template>
                  <div v-else style="border-bottom:1px solid #333; width:160px; height:28px;"></div>
                </div>
                <div style="font-size:8pt; color:#555; margin-top:2px;">(м.о. / м.п.) (қолы / подпись)</div>
              </div>

              <!-- QR code -->
              <div style="margin-top:20px; text-align:right;">
                <img v-if="qrDataUrl" :src="qrDataUrl" width="70" height="70" alt="QR" style="display:inline-block;" />
                <div v-else style="width:70px; height:70px; border:1px solid #ccc; display:inline-block;"></div>
                <div style="font-size:8pt; color:#999; margin-top:2px;">Для проверки / Тексеру үшін</div>
              </div>
            </div>

          </div>

          <!-- Footer -->
          <div style="padding:6px 16px; border-top:1px solid #ccc; font-size:8pt; color:#aaa; text-align:center;">
            Электронное удостоверение. Проверить подлинность: <strong>{{ verifyUrl }}</strong>
          </div>
        </div>
      </template>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- ПТМ certificate (книжка, 2-страничный разворот)              -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <template v-else-if="isPtm">
        <div style="font-family:'Times New Roman',serif; font-size:11pt; color:#000; max-width:780px; margin:0 auto;">

          <!-- Cover title (outer) -->
          <div style="text-align:center; border:2px solid #333; padding:20px 32px 16px; margin-bottom:0;">
            <div style="font-size:13pt; font-weight:bold; text-align:center; line-height:1.4;">
              Удостоверение
            </div>
            <div style="font-size:11pt; font-style:italic; line-height:1.5; margin-top:4px;">
              по проверке знаний в области пожарной безопасности<br>
              в объеме пожарно-технического минимума
            </div>
          </div>

          <!-- Inner spread (2-column) -->
          <div style="display:grid; grid-template-columns:1fr 1fr; border:2px solid #333; border-top:none;">

            <!-- LEFT: main cert info -->
            <div style="padding:20px 24px; border-right:2px solid #333;">

              <!-- Org name -->
              <div style="min-height:40px; border-bottom:1px solid #333; padding-bottom:4px; margin-bottom:2px; font-size:10pt;">
                {{ cert.organization_name || '' }}
              </div>
              <div style="font-size:8pt; color:#555; margin-bottom:14px; text-align:center;">(полное наименование организации)</div>

              <!-- Sub-title -->
              <div style="font-weight:bold; text-align:center; font-size:11pt; margin-bottom:4px;">
                Удостоверение
              </div>
              <div style="text-align:center; font-size:10pt; margin-bottom:16px;">
                по пожарно-техническому минимуму №&nbsp;<strong style="font-family:monospace;">{{ cert.certificate_number }}</strong>
              </div>

              <!-- FIO -->
              <div style="display:flex; align-items:baseline; gap:8px; margin-bottom:2px; font-size:10pt;">
                <span style="white-space:nowrap;"> Выдано</span>
                <span style="border-bottom:1px solid #333; flex:1; min-height:20px; font-weight:bold; padding-bottom:2px;">
                  {{ cert.full_name }}
                </span>
              </div>
              <div style="font-size:8pt; color:#555; margin-bottom:12px; text-align:center;">(фамилия, имя, отчество (при его наличии))</div>

              <!-- Position -->
              <div style="display:flex; align-items:baseline; gap:8px; margin-bottom:2px; font-size:10pt;">
                <span style="white-space:nowrap;">Должность</span>
                <span style="border-bottom:1px solid #333; flex:1; min-height:20px; padding-bottom:2px;">
                  {{ cert.position || '' }}
                </span>
              </div>
              <div style="font-size:8pt; color:#555; margin-bottom:12px;"></div>

              <!-- Workplace -->
              <div style="display:flex; align-items:baseline; gap:8px; margin-bottom:2px; font-size:10pt;">
                <span style="white-space:nowrap;">Место работы</span>
                <span style="border-bottom:1px solid #333; flex:1; min-height:20px; padding-bottom:2px;">
                  {{ cert.organization_name || '' }}
                </span>
              </div>
              <div style="font-size:8pt; color:#555; margin-bottom:16px;"></div>

              <!-- Photo placeholder -->
              <div style="display:flex; justify-content:center; margin-top:16px;">
                <div style="width:80px; height:100px; border:1px solid #aaa; overflow:hidden; display:flex; align-items:center; justify-content:center;">
                  <img v-if="cert.photo_url" :src="cert.photo_url" style="width:100%; height:100%; object-fit:cover;" alt="Фото" />
                  <span v-else style="font-size:8pt; color:#aaa; text-align:center; line-height:1.4;">Фото цветное<br>(3x4)</span>
                </div>
              </div>
            </div>

            <!-- RIGHT: knowledge check record -->
            <div style="padding:20px 24px;">
              <div style="font-weight:bold; font-size:11pt; text-align:center; margin-bottom:12px;">
                Сведения о проверках знаний
              </div>

              <!-- Exam subject -->
              <div style="font-size:10pt; margin-bottom:4px; line-height:1.6;">
                В том, что он (она) сдал (сдала) экзамены на знание
              </div>
              <div style="border-bottom:1px solid #333; min-height:20px; font-weight:bold; padding-bottom:2px; margin-bottom:12px; font-size:10pt;">
                {{ cert.training_type?.name_ru || 'пожарной безопасности' }}
              </div>

              <!-- Protocol basis -->
              <div style="font-size:10pt; line-height:1.8; margin-bottom:12px;">
                <div>
                  Основание: Протокол №
                  <strong>{{ protocol ? stripLeadingNr(protocol.protocol_number) : '______' }}</strong>
                  от <strong>{{ protocol ? formatDate(protocol.exam_date) : '___' }}</strong> {{ examYear }} г.
                </div>
              </div>

              <!-- Valid until -->
              <div style="font-size:10pt; margin-bottom:16px;">
                Действительно до
                <span :style="isExpired ? 'color:red; font-weight:bold;' : 'font-weight:bold;'">
                  {{ formatDate(cert.valid_until) }}
                  <span v-if="isExpired"> (истекло)</span>
                </span>
                {{ validUntilYear }} г.
              </div>

              <!-- Head of training center signature -->
              <div style="margin-top:24px; font-size:10pt;">
                <div style="margin-bottom:8px;">Руководитель</div>
                <div style="font-size:8pt; color:#555; margin-bottom:8px;">
                  (учебного центра)
                </div>
                <template v-if="chairSignature">
                  <SignatureStamp
                    :serial="chairSignature.signer_cert_serial"
                    :owner="chairSignature.signer_cert_owner"
                    :valid-from="chairSignature.signer_cert_valid_from"
                    :valid-to="chairSignature.signer_cert_valid_to"
                    :signed-at="chairSignature.signed_at"
                  />
                </template>
                <div v-else style="border-bottom:1px solid #333; width:160px; height:28px;"></div>
                <div style="font-size:8pt; color:#555; margin-top:2px;">(фамилия, имя, отчество (при его наличии))</div>
              </div>

              <!-- QR code -->
              <div style="margin-top:20px; text-align:right;">
                <img v-if="qrDataUrl" :src="qrDataUrl" width="70" height="70" alt="QR" style="display:inline-block;" />
                <div v-else style="width:70px; height:70px; border:1px solid #ccc; display:inline-block;"></div>
                <div style="font-size:8pt; color:#999; margin-top:2px;">Для проверки</div>
              </div>
            </div>

          </div>

          <!-- Footer -->
          <div style="border:2px solid #333; border-top:none; padding:5px 16px; font-size:8pt; color:#aaa; text-align:center;">
            Электронное удостоверение. Проверить подлинность: <strong>{{ verifyUrl }}</strong>
          </div>
        </div>
      </template>

      <!-- ═══════════════════════════════════════════════════════ -->
      <!-- БиОТ / default certificate template                      -->
      <!-- ═══════════════════════════════════════════════════════ -->
      <template v-else>
        <div class="max-w-2xl mx-auto bg-white shadow-lg print:shadow-none"
             style="border: 3px double #1a3a5c; padding: 40px 48px; font-family: 'Times New Roman', serif;">

      <!-- Header -->
      <div class="text-center mb-6">
        <div style="font-size:11px; letter-spacing:1px; text-transform:uppercase; color:#1a3a5c; font-weight:bold;">
          Қазақстан Республикасы &nbsp;|&nbsp; Республика Казахстан
        </div>
        <h1 style="font-size:22px; font-weight:bold; margin-top:10px; color:#1a3a5c; letter-spacing:1px;">
          УДОСТОВЕРЕНИЕ
        </h1>
        <div style="font-size:13px; color:#555; font-style:italic; margin-top:4px; line-height:1.5;">
          по проверке знаний правил, норм и инструкций<br>
          по безопасности и охране труда
        </div>
        <div style="margin-top:8px; font-size:13px; color:#333;">
          № <strong style="font-family:monospace; letter-spacing:1px;">{{ cert.certificate_number }}</strong>
        </div>
      </div>

      <hr style="border-color:#1a3a5c; border-width:1px; margin:16px 0;" />

      <!-- Main content -->
      <div style="font-size:14px; line-height:2; color:#222;">
        <p style="margin-bottom:6px;">
          Выдано: <strong style="font-size:16px;">{{ cert.full_name }}</strong>
        </p>
        <p style="margin-bottom:6px;">
          Должность: <strong>{{ cert.position || '—' }}</strong>
        </p>
        <p style="margin-bottom:6px;">
          Место работы: <strong>{{ cert.organization_name || '—' }}</strong>
        </p>
        <p style="margin-bottom:6px;">
          в том, что он(а) сдал(а) экзамены на знание <strong>{{ cert.training_type?.name_ru ?? 'требований безопасности' }}</strong>
        </p>
      </div>

      <!-- Protocol basis -->
      <div v-if="protocol" style="font-size:13px; margin-top:12px; margin-bottom:16px; color:#333;">
        Основание: Протокол № <strong>{{ stripLeadingNr(protocol.protocol_number) }}</strong>
        от <strong>{{ formatDate(protocol.exam_date) }}</strong>
        <span v-if="protocol.check_type"> ({{ protocol.check_type }})</span>
      </div>

      <hr style="border-color:#1a3a5c; border-width:1px; margin:16px 0;" />

      <!-- Dates row -->
      <div style="display:flex; justify-content:space-between; font-size:13px; color:#333; margin-bottom:16px;">
        <div>
          <div style="color:#777; font-size:11px;">Дата выдачи / Берілген күні</div>
          <div style="font-weight:bold;">{{ formatDate(cert.issued_date) }}</div>
        </div>
        <div style="text-align:center;">
          <div style="color:#777; font-size:11px;">Действительно до / Жарамды</div>
          <div :style="isExpired ? 'color:red;font-weight:bold;' : 'color:#1a7a1a;font-weight:bold;'">
            {{ formatDate(cert.valid_until) }}
            <span v-if="isExpired"> (истекло)</span>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="color:#777; font-size:11px;">№ удостоверения</div>
          <div style="font-size:9px; font-family:monospace; font-weight:bold;">{{ cert.certificate_number }}</div>
        </div>
      </div>

      <!-- Commission signatures (all members) -->
      <div v-if="protocol && protocol.commission_members?.length" style="margin-top:20px; font-size:13px;">
        <div v-for="m in protocol.commission_members" :key="m.id" style="margin-bottom:16px;">
          <div style="font-weight:600; margin-bottom:4px;">
            {{ m.role === 'chair' ? 'Председатель экзаменационной комиссии' : 'Член комиссии' }}
            <span v-if="m.position_title" style="font-weight:normal; color:#555;"> — {{ m.position_title }}</span>
          </div>
          <!-- EDS stamp -->
          <div v-if="m.signer_cert_serial" style="margin:4px 0 4px 16px;">
            <SignatureStamp
              :serial="m.signer_cert_serial"
              :owner="m.signer_cert_owner"
              :valid-from="m.signer_cert_valid_from"
              :valid-to="m.signer_cert_valid_to"
              :signed-at="m.signed_at"
            />
          </div>
          <div v-else style="border-bottom:1px solid #999; width:200px; margin:8px 0 4px 16px;"></div>
          <div style="color:#333; margin-left:16px;">{{ m.full_name }}</div>
        </div>
      </div>

      <!-- Fallback stamp (chair only) if no protocol loaded -->
      <div v-else-if="chairSignature" style="margin-top:20px; display:flex; justify-content:flex-end;">
        <SignatureStamp
          :serial="chairSignature.signer_cert_serial"
          :owner="chairSignature.signer_cert_owner"
          :valid-from="chairSignature.signer_cert_valid_from"
          :valid-to="chairSignature.signer_cert_valid_to"
          :signed-at="chairSignature.signed_at"
        />
      </div>

      <!-- QR code (bottom-right) -->
      <div style="display:flex; justify-content:flex-end; margin-top:24px;">
        <div style="text-align:center;">
          <img v-if="qrDataUrl" :src="qrDataUrl" width="80" height="80" alt="QR" style="display:block;" />
          <div v-else style="width:80px; height:80px; border:1px solid #ccc;"></div>
          <div style="font-size:9px; color:#999; margin-top:3px;">Для проверки</div>
        </div>
      </div>

      <!-- Footer -->
      <div style="margin-top:24px; text-align:center; font-size:10px; color:#aaa; border-top:1px solid #eee; padding-top:8px;">
        Электронное удостоверение. Проверить подлинность: <strong>{{ verifyUrl }}</strong>
      </div>
    </div>
      </template><!-- /v-else БиОТ -->

    </div><!-- /id="certificate" -->
  </div><!-- /min-h-screen -->
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import SignatureStamp from '@/components/SignatureStamp.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const cert = ref(null)
const loading = ref(true)
const chairSignature = ref(null)
const protocol = ref(null)
const qrDataUrl = ref('')

const isPrintMode = computed(() => route.meta?.printMode === true)
const isPromBez = computed(() => cert.value?.training_type?.code === 'prombez')
const isPtm = computed(() => cert.value?.training_type?.code === 'ptm')

const MONTHS_RU = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

const _examDateStr = computed(() => protocol.value?.exam_date || cert.value?.issued_date || null)
const examDay = computed(() => {
  const d = _examDateStr.value
  if (!d) return '__'
  return String(new Date(d + 'T00:00:00').getDate()).padStart(2, '0')
})
const examMonth = computed(() => {
  const d = _examDateStr.value
  if (!d) return '______'
  return MONTHS_RU[new Date(d + 'T00:00:00').getMonth()]
})
const examYear = computed(() => {
  const d = _examDateStr.value
  if (!d) return '20__'
  return new Date(d + 'T00:00:00').getFullYear()
})

const validUntilDay = computed(() => {
  const d = cert.value?.valid_until
  if (!d) return '__'
  return String(new Date(d + 'T00:00:00').getDate()).padStart(2, '0')
})
const validUntilMonth = computed(() => {
  const d = cert.value?.valid_until
  if (!d) return '______'
  return MONTHS_RU[new Date(d + 'T00:00:00').getMonth()]
})
const validUntilYear = computed(() => {
  const d = cert.value?.valid_until
  if (!d) return '20__'
  return new Date(d + 'T00:00:00').getFullYear()
})

const isExpired = computed(() => {
  if (!cert.value?.valid_until) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return new Date(cert.value.valid_until + 'T00:00:00') < today
})

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
        const chair = protoRes.data.commission_members?.find(
          m => m.role === 'chair' && m.signer_cert_serial
        )
        if (chair) chairSignature.value = chair
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

function stripLeadingNr(s) {
  return s ? s.replace(/^[№#]\ */, '') : s
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

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
