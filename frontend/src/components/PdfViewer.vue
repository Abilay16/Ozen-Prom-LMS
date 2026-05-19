<template>
  <div
    ref="container"
    style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; overflow-y: scroll; overflow-x: auto; -webkit-overflow-scrolling: touch; overscroll-behavior: contain; background: #f3f4f6;"
  >
    <div v-if="loading" class="flex items-center justify-center min-h-full text-gray-500 text-sm">
      Загрузка PDF...
    </div>
    <div v-else-if="error" class="flex flex-col items-center justify-center min-h-full gap-3 px-4 text-center">
      <span class="text-4xl">⚠️</span>
      <p class="text-red-400 text-sm">{{ error }}</p>
    </div>
    <div v-else class="flex flex-col items-center gap-2 py-3">
      <canvas
        v-for="n in pageCount"
        :key="n"
        :ref="el => mountCanvas(el, n)"
        style="display: block; max-width: 100%;"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import api from '@/services/api'

// Lazy-load pdfjs to avoid bloating the initial bundle
let pdfjsLib = null
async function getPdfJs() {
  if (!pdfjsLib) {
    pdfjsLib = await import('pdfjs-dist')
    // Use the bundled worker (Vite resolves the URL at build time)
    pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
      'pdfjs-dist/build/pdf.worker.min.mjs',
      import.meta.url
    ).href
  }
  return pdfjsLib
}

const props = defineProps({
  materialId: { type: String, required: true },
})

const container = ref(null)
const loading = ref(true)
const error = ref(null)
const pageCount = ref(0)

let pdfDoc = null
let destroyed = false
const canvasMap = {} // page number (1-based) → HTMLCanvasElement

function mountCanvas(el, n) {
  if (!el) return
  canvasMap[n] = el
  if (pdfDoc) renderPage(n)
}

function getContainerWidth() {
  // getBoundingClientRect is reliable on iOS inside fixed modals;
  // clientWidth can return 0 when layout isn't settled yet.
  const rect = container.value?.getBoundingClientRect?.()
  const w = rect?.width || container.value?.clientWidth || 0
  return Math.max(w > 0 ? w : window.innerWidth, 200) - 8
}

async function renderPage(n) {
  const canvas = canvasMap[n]
  if (!canvas || !pdfDoc) return
  try {
    const page = await pdfDoc.getPage(n)
    const containerWidth = getContainerWidth()
    const baseViewport = page.getViewport({ scale: 1 })
    const dpr = window.devicePixelRatio || 1
    const scale = (containerWidth / baseViewport.width) * dpr
    const viewport = page.getViewport({ scale })

    canvas.width = viewport.width
    canvas.height = viewport.height
    canvas.style.width = `${containerWidth}px`
    canvas.style.height = `${Math.round(viewport.height / dpr)}px`
    canvas.style.maxWidth = '100%'

    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise
  } catch {
    // ignore single-page render errors
  }
}

async function load() {
  if (!props.materialId) return
  loading.value = true
  error.value = null
  pageCount.value = 0
  Object.keys(canvasMap).forEach(k => delete canvasMap[k])
  if (pdfDoc) { pdfDoc.destroy(); pdfDoc = null }

  try {
    const lib = await getPdfJs()
    const { data } = await api.get(`/learner/materials/${props.materialId}/view`, {
      responseType: 'arraybuffer',
    })
    if (destroyed) return
    pdfDoc = await lib.getDocument({ data }).promise
    if (destroyed) return
    pageCount.value = pdfDoc.numPages
    loading.value = false
  } catch {
    if (!destroyed) {
      error.value = 'Не удалось загрузить PDF'
      loading.value = false
    }
  }
}

onMounted(async () => {
  // Wait one frame so the container has been laid out and
  // getBoundingClientRect() returns the correct width on iOS Safari.
  await nextTick()
  load()
})
onUnmounted(() => {
  destroyed = true
  pdfDoc?.destroy()
})
watch(() => props.materialId, load)
</script>
