<template>
  <!-- Пластиковая карта работника 85,6 × 54 мм по макету «1КАРТА».
       Фон — картинка макета 1579 × 996 px; поверх в тех же пикселях:
       фото (вместо силуэта), ФИО на линиях, должность, QR в белом квадрате. -->
  <div ref="frameEl" class="worker-card-frame" :style="{ height: `${H * scale}px` }">
    <div ref="cardEl" class="worker-card" :style="{ transform: `scale(${scale})` }">
      <img :src="bgUrl" class="bg" alt="" draggable="false" />

      <img v-if="photoUrl && photoOk" :src="photoUrl" class="photo" alt="" @error="photoOk = false" />

      <div class="line line--1" :style="{ fontSize: `${fit(nameLine1, 46, 18)}px` }">{{ nameLine1 }}</div>
      <div class="line line--2" :style="{ fontSize: `${fit(nameLine2, 40, 22)}px` }">{{ nameLine2 }}</div>
      <div v-if="position" class="position">{{ position }}</div>

      <img v-if="qrDataUrl" :src="qrDataUrl" class="qr" alt="QR-код карточки работника" />
    </div>
  </div>
</template>

<script setup>
import '@fontsource-variable/manrope/wght.css'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import bgUrl from '@/assets/cards/worker-card-bg.jpg'

const props = defineProps({
  fullName: { type: String, default: '' },
  position: { type: String, default: '' },
  photoUrl: { type: String, default: '' },
  qrDataUrl: { type: String, default: '' },
})

const W = 1579
const H = 996
defineExpose({ W, H, node: () => cardEl.value })

const photoOk = ref(true)

// Фамилия — на первой линии, имя и отчество — на второй.
const parts = computed(() => (props.fullName || '').trim().split(/\s+/))
const nameLine1 = computed(() => parts.value[0] || '')
const nameLine2 = computed(() => parts.value.slice(1).join(' '))

// Длинное ФИО уменьшаем, чтобы влезло в линию (~496 px).
function fit(text, base, maxChars) {
  const len = (text || '').length
  return Math.round(base * Math.min(1, maxChars / Math.max(len, 1)))
}

const frameEl = ref(null)
const cardEl = ref(null)
const scale = ref(0.3)
let ro = null
onMounted(() => {
  const update = () => { scale.value = Math.min(1, (frameEl.value?.clientWidth || W) / W) }
  update()
  ro = new ResizeObserver(update)
  ro.observe(frameEl.value)
})
onBeforeUnmount(() => ro?.disconnect())
</script>

<style scoped>
.worker-card-frame {
  width: 100%;
  position: relative;
  overflow: hidden;
  border-radius: 4.2%/6.6%;
  box-shadow: 0 12px 30px -14px rgba(15, 40, 90, 0.45);
}
.worker-card {
  position: absolute;
  top: 0;
  left: 0;
  width: 1579px;
  height: 996px;
  transform-origin: top left;
  font-family: 'Manrope Variable', 'Manrope', 'Inter Variable', Arial, sans-serif;
  color: #0b2a5b;
}
.bg { position: absolute; inset: 0; width: 100%; height: 100%; user-select: none; }

.photo {
  position: absolute;
  left: 68px;
  top: 278px;
  width: 402px;
  height: 494px;
  object-fit: cover;
  object-position: center top;
  border-radius: 30px;
}

.line {
  position: absolute;
  left: 519px;
  width: 496px;
  white-space: nowrap;
  line-height: 1;
  letter-spacing: -0.01em;
}
/* Текст стоит на линии (линии на 488 и 595 px) */
.line--1 { bottom: calc(996px - 476px); font-weight: 800; }
.line--2 { bottom: calc(996px - 583px); font-weight: 700; }

.position {
  position: absolute;
  left: 519px;
  width: 496px;
  top: 612px;
  font-size: 27px;
  font-weight: 600;
  line-height: 1.25;
  color: #1f4f96;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Белый квадрат 1084–1518 × 247–687 px */
.qr {
  position: absolute;
  left: 1106px;
  top: 272px;
  width: 390px;
  height: 390px;
  image-rendering: pixelated;
}
</style>
