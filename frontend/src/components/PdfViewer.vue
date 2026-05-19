<template>
  <div ref="container" style="width: 100%;">
    <div v-if="loading" style="padding: 40px 0; text-align: center; color: #6b7280; font-size: 14px;">
      Загрузка PDF...
    </div>
    <div v-else-if="error" style="padding: 40px 16px; text-align: center;">
      <div style="font-size: 40px;">⚠️</div>
      <p style="color: #f87171; font-size: 14px; margin-top: 8px;">{{ error }}</p>
    </div>
    <div v-else style="display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 12px 4px;">
      <canvas
        v-for="n in pageCount"
        :key="n"
        :ref="el => mountCanvas(el, n)"
        style="display: block;"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
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
  // The parent content-area is the scrollable container — its width equals
  // window.innerWidth on mobile (full-screen modal). Use the parent's
  // clientWidth if available, fall back to window.innerWidth.
  const parent = container.value?.parentElement
  const w = (parent?.clientWidth > 10 ? parent.clientWidth : null)
    ?? (container.value?.clientWidth > 10 ? container.value.clientWidth : null)
    ?? window.innerWidth
  return Math.max(w, 200) - 8
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

onMounted(() => {
  // Use requestAnimationFrame so iOS Safari has finished its initial layout
  // pass before we measure dimensions and kick off rendering.
  requestAnimationFrame(() => {
    if (!destroyed) load()
  })
})
onUnmounted(() => {
  destroyed = true
  pdfDoc?.destroy()
})
watch(() => props.materialId, load)
</script>
