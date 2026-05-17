<template>
  <div v-if="loading" class="flex items-center justify-center min-h-screen text-gray-400">
    Загрузка...
  </div>
  <div v-else-if="error" class="flex items-center justify-center min-h-screen text-red-500">
    {{ error }}
  </div>
  <div v-else class="print-page">
    <!-- Print / Back bar (hidden when printing) -->
    <div class="no-print flex gap-3 p-4 bg-gray-100 border-b">
      <button @click="router.push(`/admin/protocols/${route.params.id}`)" class="text-sm text-gray-600 hover:text-gray-800">← Назад к протоколу</button>
      <button @click="doPrint()" class="text-sm bg-blue-600 text-white px-4 py-1.5 rounded hover:bg-blue-700">🖨 Печать</button>
      <button @click="doSavePdf()" class="text-sm bg-green-600 text-white px-4 py-1.5 rounded hover:bg-green-700">⬇ Скачать PDF</button>
    </div>

    <!-- Official protocol document -->
    <div class="protocol-doc">

      <!-- ════════════════════════════════════════════════ -->
      <!-- ПромБез protocol template                        -->
      <!-- ════════════════════════════════════════════════ -->
      <template v-if="isPromBez">

        <!-- Header -->
        <div class="text-center mb-4">
          <div class="font-bold text-base uppercase">
            ПРОТОКОЛ № {{ p.protocol_number }}
          </div>
        </div>

        <!-- Organization -->
        <div class="mb-4 text-sm border-b border-black pb-1">
          {{ p.organization?.name || p.batch?.name || '_______________________________________________' }}
        </div>

        <!-- Date -->
        <div class="mb-4 text-sm">
          «{{ examDay }}» {{ examMonth }} {{ examYear }} года
        </div>

        <!-- Commission -->
        <div class="mb-4 text-sm">
          <div class="font-semibold mb-1">Комиссия в составе:</div>
          <div v-for="m in p.commission_members" :key="m.id" class="mb-1">
            <span class="font-medium">{{ m.role === 'chair' ? 'Председатель:' : 'Член комиссии:' }}</span>
            {{ m.full_name }}<span v-if="m.position_title"> – {{ m.position_title }}</span>
          </div>
          <div class="text-xs text-gray-400">Фамилия, имя, отчество (при его наличии)</div>
        </div>

        <!-- Body text -->
        <div class="mb-4 text-sm leading-relaxed">
          Провели проверку знаний в объеме требований промышленной безопасности
          установленных Законами и нормативными правовыми актами Республики Казахстан*:
        </div>

        <!-- Regulatory docs (if any) -->
        <div v-if="p.regulatory_docs" class="mb-4 text-xs">
          <div v-for="(doc, i) in regulatoryDocsList" :key="i" class="ml-2">{{ i + 1 }}. {{ doc }}</div>
        </div>

        <!-- Participants table (PromBez columns) -->
        <table class="w-full text-xs border-collapse mb-6">
          <thead>
            <tr class="bg-gray-100">
              <th class="border border-gray-700 px-2 py-2 text-center w-8">№ п./п.</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Фамилия, имя, отчество<br>(при его наличии)</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Должность</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Образование</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Заключение комиссии<br>(сдал, не сдал)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(part, i) in p.participants" :key="part.id" class="h-8">
              <td class="border border-gray-700 px-2 py-2 text-center">{{ i + 1 }}.</td>
              <td class="border border-gray-700 px-2 py-2">{{ part.full_name }}</td>
              <td class="border border-gray-700 px-2 py-2">{{ part.position || '' }}</td>
              <td class="border border-gray-700 px-2 py-2">{{ part.education || '' }}</td>
              <td class="border border-gray-700 px-2 py-2 text-center">
                {{ part.result === 'passed' ? 'сдал(а)' : part.result === 'failed' ? 'не сдал(а)' : '' }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Signatures -->
        <div class="text-sm space-y-6">
          <div v-for="m in p.commission_members" :key="'sig-' + m.id">
            <div class="flex items-start gap-6">
              <div class="min-w-[240px] font-medium shrink-0">
                {{ m.role === 'chair' ? 'Председатель комиссии:' : 'Члены комиссии:' }}
              </div>
              <div class="flex-1">
                <div v-if="m.signer_cert_serial" class="eds-stamp mb-1">
                  <div class="eds-stamp-inner">
                    <div class="eds-title">ДОКУМЕНТ ПОДПИСАН<br>ЭЛЕКТРОННОЙ ПОДПИСЬЮ</div>
                    <div class="eds-line">Серия: {{ m.signer_cert_serial }}</div>
                    <div class="eds-line">Владелец: {{ m.signer_cert_owner }}</div>
                    <div class="eds-line" v-if="m.signer_cert_valid_from && m.signer_cert_valid_to">
                      Срок: {{ fmtDate(m.signer_cert_valid_from) }} — {{ fmtDate(m.signer_cert_valid_to) }}
                    </div>
                    <div class="eds-line" v-if="m.signed_at">Подписано: {{ fmtDateTime(m.signed_at) }}</div>
                  </div>
                </div>
                <div v-else class="signature-line"></div>
                <div class="mt-1 text-gray-700">{{ initials(m.full_name) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footnote -->
        <div class="mt-8 text-xs text-gray-500 leading-snug border-t pt-3">
          *Протокол содержит перечень всех законодательных и нормативных правовых актов,
          которые отражают вопросы промышленной безопасности с учетом специфики
          и отраслевой принадлежности обучаемой организации и всех видов специальностей
          персонала, включенного в настоящий протокол.
        </div>

      </template>

      <!-- ════════════════════════════════════════════════ -->
      <!-- ПТМ protocol template                            -->
      <!-- ════════════════════════════════════════════════ -->
      <template v-else-if="isPtm">

        <!-- Header -->
        <div class="text-center mb-6">
          <div class="font-bold text-base uppercase leading-snug">
            ПРОТОКОЛ № {{ p.protocol_number }}
          </div>
          <div class="text-sm mt-1 leading-snug">
            заседания квалификационной комиссии<br>
            по проверке знаний по пожарной безопасности в объеме<br>
            пожарно-технического минимума
          </div>
        </div>

        <!-- Organization -->
        <div class="mb-6 text-sm border-b border-black pb-1 min-h-[22px]">
          {{ p.organization?.name || p.batch?.name || '' }}
        </div>

        <!-- Basis text -->
        <div class="mb-4 text-sm leading-relaxed">
          В соответствии с приказом (распоряжением)
          <span v-if="p.order_number"> № {{ p.order_number }}</span>
          <span v-if="p.order_date"> от «{{ orderDay }}» {{ orderMonth }} {{ orderYear }} г.</span>
          квалификационная комиссия в составе:
        </div>

        <!-- Commission -->
        <div class="mb-4 text-sm">
          <div v-for="m in p.commission_members" :key="m.id" class="mb-2">
            <div class="flex gap-2 items-baseline">
              <span class="font-medium shrink-0 min-w-[200px]">
                {{ m.role === 'chair' ? 'председатель' : 'член комиссии' }}
              </span>
              <span class="border-b border-black flex-1">
                {{ m.full_name }}<span v-if="m.position_title">, {{ m.position_title }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Exam text -->
        <div class="mb-6 text-sm leading-relaxed">
          «{{ examDay }}» {{ examMonth }} {{ examYear }} г. приняла экзамен по пожарной безопасности в
          объеме пожарно-технического минимума и установила следующие результаты:
        </div>

        <!-- Participants table (PTM columns) -->
        <table class="w-full text-xs border-collapse mb-6">
          <thead>
            <tr class="bg-gray-100">
              <th class="border border-gray-700 px-1 py-2 text-center w-7">№ п/п</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Фамилия, имя, отчество<br>(при его наличии)</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Должность</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Организация<br>(цех, участок)</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Причина<br>обучения</th>
              <th class="border border-gray-700 px-2 py-2 text-center">Отметка о проверке знаний<br>(прошел, не прошел)</th>
              <th class="border border-gray-700 px-2 py-2 text-center w-14">Подпись</th>
            </tr>
            <tr class="text-center text-xs text-gray-500">
              <th class="border border-gray-700 px-1 py-1">1</th>
              <th class="border border-gray-700 px-1 py-1">2</th>
              <th class="border border-gray-700 px-1 py-1">3</th>
              <th class="border border-gray-700 px-1 py-1">4</th>
              <th class="border border-gray-700 px-1 py-1">5</th>
              <th class="border border-gray-700 px-1 py-1">6</th>
              <th class="border border-gray-700 px-1 py-1">7</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(part, i) in p.participants" :key="part.id" class="h-8">
              <td class="border border-gray-700 px-1 py-2 text-center">{{ i + 1 }}</td>
              <td class="border border-gray-700 px-2 py-2">{{ part.full_name }}</td>
              <td class="border border-gray-700 px-2 py-2">{{ part.position || '' }}</td>
              <td class="border border-gray-700 px-2 py-2">{{ part.organization_name || p.organization?.name || '' }}</td>
              <td class="border border-gray-700 px-2 py-2 text-center">{{ p.check_type || '' }}</td>
              <td class="border border-gray-700 px-2 py-2 text-center">
                {{ part.result === 'passed' ? 'прошел(а)' : part.result === 'failed' ? 'не прошел(а)' : '' }}
              </td>
              <td class="border border-gray-700 px-2 py-2"></td>
            </tr>
          </tbody>
        </table>

        <!-- Signatures -->
        <div class="text-sm space-y-5 mt-4">
          <div v-for="m in p.commission_members" :key="'sig-' + m.id">
            <div class="flex items-start gap-6">
              <div class="min-w-[240px] font-medium shrink-0">
                {{ m.role === 'chair' ? 'Председатель комиссии' : 'Члены комиссии' }}
              </div>
              <div class="flex-1">
                <div v-if="m.signer_cert_serial" class="eds-stamp mb-1">
                  <div class="eds-stamp-inner">
                    <div class="eds-title">ДОКУМЕНТ ПОДПИСАН<br>ЭЛЕКТРОННОЙ ПОДПИСЬЮ</div>
                    <div class="eds-line">Серия: {{ m.signer_cert_serial }}</div>
                    <div class="eds-line">Владелец: {{ m.signer_cert_owner }}</div>
                    <div class="eds-line" v-if="m.signer_cert_valid_from && m.signer_cert_valid_to">
                      Срок: {{ fmtDate(m.signer_cert_valid_from) }} — {{ fmtDate(m.signer_cert_valid_to) }}
                    </div>
                    <div class="eds-line" v-if="m.signed_at">Подписано: {{ fmtDateTime(m.signed_at) }}</div>
                  </div>
                </div>
                <div v-else class="signature-line"></div>
                <div class="mt-1 text-gray-700">{{ m.full_name }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- date -->
        <div class="mt-6 text-sm">
          «{{ examDay }}» {{ examMonth }} {{ examYear }} г.
        </div>

      </template>

      <!-- ════════════════════════════════════════════════ -->
      <!-- БиОТ / default protocol template                 -->
      <!-- ════════════════════════════════════════════════ -->
      <template v-else>

        <!-- Header -->
        <div class="text-center mb-6">
          <div class="font-bold text-base uppercase leading-snug">
            ПРОТОКОЛ № {{ p.protocol_number }}
          </div>
          <div class="text-sm mt-1">
            заседания экзаменационной комиссии по проверке знаний {{ protocolSubtitle }}
          </div>
          <div class="text-sm mt-2">
            «{{ examDay }}» {{ examMonth }} {{ examYear }} г.
          </div>
        </div>

        <!-- Commission composition -->
        <div class="mb-4 text-sm">
          <div v-for="m in p.commission_members" :key="m.id" class="mb-3">
            <div class="flex gap-2 items-start">
              <span class="shrink-0 font-medium min-w-[220px]">
                {{ m.role === 'chair' ? 'Председатель комиссии:' : 'Член комиссии:' }}
              </span>
              <span>{{ m.full_name }}<span v-if="m.position_title"> – {{ m.position_title }}</span></span>
            </div>
          </div>
        </div>

        <!-- Basis text -->
        <div v-if="p.order_number || p.check_type" class="mb-4 text-sm leading-relaxed border-l-4 border-gray-300 pl-3">
          На основании приказа
          <span v-if="p.order_date"> от «{{ orderDay }}» {{ orderMonth }} {{ orderYear }} года</span>
          <span v-if="p.order_number"> № {{ p.order_number }}</span>
          приняла экзамен и установила:
          <span v-if="p.check_type" class="font-semibold italic">{{ p.check_type }}</span>
          вид проверки знаний.
        </div>

        <!-- Regulatory docs -->
        <div v-if="p.regulatory_docs" class="mb-4 text-sm">
          <div class="font-medium mb-1">Нормативные документы:</div>
          <div v-for="(doc, i) in regulatoryDocsList" :key="i" class="ml-4">{{ i + 1 }}. {{ doc }}</div>
        </div>

        <!-- Participants table -->
        <table class="w-full text-xs border-collapse mb-6">
          <thead>
            <tr class="bg-gray-100">
              <th class="border border-gray-400 px-2 py-1 text-center w-8">№</th>
              <th class="border border-gray-400 px-2 py-1 text-left">ФИО</th>
              <th class="border border-gray-400 px-2 py-1 text-left">Организация</th>
              <th class="border border-gray-400 px-2 py-1 text-left">Должность</th>
              <th class="border border-gray-400 px-2 py-1 text-center">Отметка о проверке знаний</th>
              <th class="border border-gray-400 px-2 py-1 text-center">Примечание</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(part, i) in p.participants" :key="part.id">
              <td class="border border-gray-400 px-2 py-1 text-center">{{ i + 1 }}</td>
              <td class="border border-gray-400 px-2 py-1">{{ part.full_name }}</td>
              <td class="border border-gray-400 px-2 py-1">{{ part.organization_name || '' }}</td>
              <td class="border border-gray-400 px-2 py-1">{{ part.position || '' }}</td>
              <td class="border border-gray-400 px-2 py-1 text-center">
                {{ part.result === 'passed' ? 'Прошёл(а)' : part.result === 'failed' ? 'Не прошёл(а)' : '' }}
              </td>
              <td class="border border-gray-400 px-2 py-1"></td>
            </tr>
          </tbody>
        </table>

        <!-- Signatures -->
        <div class="text-sm space-y-6">
          <div v-for="m in p.commission_members" :key="'sig-' + m.id">
            <div class="flex items-start gap-6">
              <div class="min-w-[220px] font-medium shrink-0">
                {{ m.role === 'chair' ? 'Председатель комиссии' : 'Член комиссии' }}
              </div>
              <div class="flex-1">
                <!-- EDS stamp (if signed) -->
                <div v-if="m.signer_cert_serial" class="eds-stamp mb-1">
                  <div class="eds-stamp-inner">
                    <div class="eds-title">ДОКУМЕНТ ПОДПИСАН<br>ЭЛЕКТРОННОЙ ПОДПИСЬЮ</div>
                    <div class="eds-line">Серия: {{ m.signer_cert_serial }}</div>
                    <div class="eds-line">Владелец: {{ m.signer_cert_owner }}</div>
                    <div class="eds-line" v-if="m.signer_cert_valid_from && m.signer_cert_valid_to">
                      Срок: {{ fmtDate(m.signer_cert_valid_from) }} — {{ fmtDate(m.signer_cert_valid_to) }}
                    </div>
                    <div class="eds-line" v-if="m.signed_at">Подписано: {{ fmtDateTime(m.signed_at) }}</div>
                  </div>
                </div>
                <!-- Handwritten line if not signed -->
                <div v-else class="signature-line"></div>
                <!-- Name -->
                <div class="mt-1 text-gray-700">{{ initials(m.full_name) }}</div>
              </div>
            </div>
          </div>
        </div>

      </template>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const p = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await api.get(`/admin/protocols/${route.params.id}`)
    p.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
})

const MONTHS = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
]

function parseDateParts(d) {
  if (!d) return {}
  const dt = new Date(d + 'T00:00:00')
  return { day: String(dt.getDate()).padStart(2, '0'), month: MONTHS[dt.getMonth()], year: dt.getFullYear() }
}

const examDay = computed(() => parseDateParts(p.value?.exam_date).day)
const examMonth = computed(() => parseDateParts(p.value?.exam_date).month)
const examYear = computed(() => parseDateParts(p.value?.exam_date).year)

const orderDay = computed(() => parseDateParts(p.value?.order_date).day)
const orderMonth = computed(() => parseDateParts(p.value?.order_date).month)
const orderYear = computed(() => parseDateParts(p.value?.order_date).year)

const regulatoryDocsList = computed(() =>
  (p.value?.regulatory_docs || '').split('\n').map(s => s.trim()).filter(Boolean)
)

const SUBTITLE_MAP = {
  biot:    'по безопасности и охране труда работников',
  ptm:     'по пожарно-техническому минимуму',
  prombez: 'по промышленной безопасности',
  elektro: 'по электробезопасности',
}
const protocolSubtitle = computed(() => {
  const tt = p.value?.training_type
  if (!tt) return ''
  return SUBTITLE_MAP[tt.code] || tt.name_ru
})

const isPromBez = computed(() => p.value?.training_type?.code === 'prombez')
const isPtm = computed(() => p.value?.training_type?.code === 'ptm')

function initials(fullName) {
  if (!fullName) return ''
  const parts = fullName.trim().split(/\s+/)
  if (parts.length === 1) return parts[0]
  return parts[0] + ' ' + parts.slice(1).map(n => n[0] + '.').join('')
}

function fmtDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function fmtDateTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function doPrint() {
  window.print()
}

function doSavePdf() {
  const prev = document.title
  document.title = `Протокол_${p.value?.protocol_number || route.params.id}`
  window.print()
  document.title = prev
}
</script>

<style scoped>
.print-page {
  font-family: 'Times New Roman', serif;
  font-size: 12pt;
  color: #000;
}

.protocol-doc {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 60px;
  background: #fff;
}

.signature-line {
  display: inline-block;
  width: 180px;
  border-bottom: 1px solid #000;
  height: 28px;
  vertical-align: bottom;
}

.eds-stamp {
  display: inline-block;
}

.eds-stamp-inner {
  border: 2px solid #16a34a;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 8pt;
  color: #15803d;
  max-width: 280px;
}

.eds-title {
  font-weight: bold;
  font-size: 8pt;
  text-align: center;
  margin-bottom: 4px;
  line-height: 1.2;
}

.eds-line {
  font-size: 7.5pt;
  line-height: 1.4;
}

@media print {
  .no-print {
    display: none !important;
  }

  .print-page {
    margin: 0;
    padding: 0;
  }

  .protocol-doc {
    padding: 20mm 20mm;
    max-width: 100%;
  }

  @page {
    size: A4 portrait;
    margin: 0;
  }
}
</style>
