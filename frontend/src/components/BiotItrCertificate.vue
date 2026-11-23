<template>
  <!-- Сертификат БиОТ для ИТР (срок 3 года).
       Фон (рамка, «СЕРТИФИКАТ», реквизиты, подписант, город) — растровый
       снимок макета заказчика; поверх него в тех же координатах (в pt,
       лист A4 альбомный 842.25 × 595.5) подставляются ФИО, дата, курс,
       печать ЭЦП председателя и QR. -->
  <div ref="frameEl" class="biot-cert-frame" :style="{ height: frameHeight }">
    <div class="biot-cert" :style="{ transform: `scale(${scale})` }">
      <img :src="bgUrl" class="bg" alt="" draggable="false" />

      <!-- ФИО -->
      <div class="name" :style="{ fontSize: nameFontSize }">{{ cert.full_name }}</div>

      <!-- Курс: слева по-казахски, справа по-русски -->
      <div class="course course--kz">
        “Еңбекті қорғау және қауіпсіздігі” курсы<br />
        бойынша оқу бағдарламасын өткендігін<br />
        куәландырады.
      </div>
      <div class="course course--ru">
        успешно закончил (а) программу<br />
        обучения по курсу<br />
        “Безопасность и охрана труда”
      </div>

      <!-- Дата экзамена -->
      <div class="date">
        <div>20<u>{{ yy }}</u>&nbsp; жыл &nbsp;<u>&nbsp;{{ day }}&nbsp; {{ monthKz }}</u></div>
        <div><u>{{ day }} {{ monthRu }}&nbsp; год</u> 20<u>{{ yy }}</u></div>
      </div>

      <!-- ЭЦП председателя комиссии -->
      <div v-if="chairSignature" class="stamp">
        <SignatureStamp
          compact
          :serial="chairSignature.signer_cert_serial"
          :owner="chairSignature.signer_cert_owner"
          :valid-from="chairSignature.signer_cert_valid_from"
          :valid-to="chairSignature.signer_cert_valid_to"
          :signed-at="chairSignature.signed_at"
        />
      </div>

      <!-- QR + номер -->
      <div class="qr">
        <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR" />
        <div class="qr-num">№ {{ cert.certificate_number }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Шрифты макета сертификата грузятся только вместе с сертификатом.
// cyrillic-ext — казахские буквы (қ, ә, ө, ұ, ү, і, ғ, ң, һ).
import '@fontsource/lora/cyrillic-400.css'
import '@fontsource/lora/cyrillic-ext-400.css'
import '@fontsource/lora/latin-400.css'
import '@fontsource/lora/cyrillic-400-italic.css'
import '@fontsource/lora/cyrillic-ext-400-italic.css'
import '@fontsource/lora/latin-400-italic.css'
import '@fontsource/noto-sans/cyrillic-400.css'
import '@fontsource/noto-sans/cyrillic-ext-400.css'
import '@fontsource/noto-sans/latin-400.css'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import SignatureStamp from '@/components/SignatureStamp.vue'
import bgUrl from '@/assets/certificates/biot-itr-bg.jpg'

const props = defineProps({
  cert: { type: Object, required: true },
  protocol: { type: Object, default: null },
  qrDataUrl: { type: String, default: '' },
})

// Лист в pt; на экране 1pt = 4/3 px.
const PAGE_W_PX = 842.25 * 4 / 3
const PAGE_RATIO = 595.5 / 842.25

const chairSignature = computed(() =>
  props.protocol?.commission_members?.find(m => m.role === 'chair' && m.signer_cert_serial) || null
)

const MONTHS_RU = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
const MONTHS_KZ = ['қаңтар', 'ақпан', 'наурыз', 'сәуір', 'мамыр', 'маусым', 'шілде', 'тамыз', 'қыркүйек', 'қазан', 'қараша', 'желтоқсан']

const examDate = computed(() => {
  const d = props.protocol?.exam_date || props.cert?.issued_date
  return d ? new Date(d + 'T00:00:00') : null
})
const day = computed(() => examDate.value ? String(examDate.value.getDate()) : '__')
const yy = computed(() => examDate.value ? String(examDate.value.getFullYear()).slice(2) : '__')
const monthRu = computed(() => examDate.value ? MONTHS_RU[examDate.value.getMonth()] : '______')
const monthKz = computed(() => examDate.value ? MONTHS_KZ[examDate.value.getMonth()] : '______')

// В макете влезает ~33 символа ФИО при 28pt; длинные ФИО уменьшаем.
const nameFontSize = computed(() => {
  const len = (props.cert?.full_name || '').length
  return `${(28.1 * Math.min(1, 33 / Math.max(len, 1))).toFixed(2)}pt`
})

// Масштаб под ширину контейнера на экране.
const frameEl = ref(null)
const scale = ref(1)
const frameHeight = computed(() => `${PAGE_W_PX * PAGE_RATIO * scale.value}px`)
let ro = null

// Альбомный A4 без полей — только пока сертификат на странице
// (в общий CSS не кладём, иначе повернёт печать всех удостоверений).
let pageStyle = null

onMounted(() => {
  const update = () => {
    const w = frameEl.value?.clientWidth || PAGE_W_PX
    scale.value = Math.min(1, w / PAGE_W_PX)
  }
  update()
  ro = new ResizeObserver(update)
  ro.observe(frameEl.value)

  pageStyle = document.createElement('style')
  // Отступы страниц-обёрток (VerifyPage и т.п.) иначе сдвигают лист
  // и выталкивают край фона на второй пустой лист.
  pageStyle.textContent = `
    @page { size: A4 landscape; margin: 0; }
    @media print {
      html, body { margin: 0 !important; padding: 0 !important; height: 595.5pt !important; overflow: hidden !important; }
      #app > * { max-height: 595.5pt !important; overflow: hidden !important; }
      .biot-cert-frame { position: fixed !important; top: 0 !important; left: 0 !important; z-index: 10; }
    }`
  document.head.appendChild(pageStyle)
})

onBeforeUnmount(() => {
  ro?.disconnect()
  pageStyle?.remove()
})
</script>

<style scoped>
.biot-cert-frame {
  width: 100%;
  max-width: 1123px;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 30px -12px rgba(0, 0, 0, 0.25);
}
.biot-cert {
  position: absolute;
  top: 0;
  left: 0;
  width: 842.25pt;
  height: 595.5pt;
  transform-origin: top left;
  color: #000;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  user-select: none;
}

.name {
  position: absolute;
  left: 60pt;
  right: 60pt;
  top: 243pt;
  text-align: center;
  font-family: 'Noto Sans', 'Segoe UI', Arial, sans-serif;
  line-height: 1.4;
  white-space: nowrap;
  text-decoration: underline;
  text-decoration-thickness: 2.2pt;
  text-underline-offset: 4pt;
}

.course {
  position: absolute;
  top: 312pt;
  width: 320pt;
  text-align: center;
  font-family: 'Lora', Georgia, 'Times New Roman', serif;
  font-size: 13pt;
  line-height: 21pt;
}
.course--kz { left: 95.5pt; }   /* центр ≈ 255.5pt */
.course--ru { left: 428pt; }    /* центр ≈ 588pt   */

.date {
  position: absolute;
  left: 115pt;
  width: 200pt;
  top: 474pt;
  text-align: center;
  font-family: 'Lora', Georgia, 'Times New Roman', serif;
  font-style: italic;
  font-size: 13pt;
  line-height: 16.5pt;
}
.date u {
  text-decoration-thickness: 0.75pt;
  text-underline-offset: 2pt;
}

.stamp {
  position: absolute;
  /* поверх линии подписи (482–586pt, y≈425pt), между
     «…учебного центра» и «Аяпбергенов А.А» */
  left: 467pt;
  top: 396pt;
  transform: scale(0.85);
  transform-origin: top left;
}
.stamp :deep(.signature-stamp) {
  background: rgba(255, 255, 255, 0.75);
}

.qr {
  position: absolute;
  left: 312pt;
  top: 438pt;
  width: 64pt;
  text-align: center;
}
.qr img {
  width: 50pt;
  height: 50pt;
  margin: 0 auto;
  display: block;
}
.qr-num {
  font-family: 'Lora', Georgia, serif;
  font-size: 5.5pt;
  margin-top: 1.5pt;
  white-space: nowrap;
  color: #333;
}

@media print {
  .biot-cert-frame {
    max-width: none;
    width: 842.25pt !important;
    height: 595.5pt !important;
    box-shadow: none;
  }
  .biot-cert { transform: none !important; }
}
</style>
