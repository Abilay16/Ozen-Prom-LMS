<template>
  <!-- Single root. Height 100% only when using iframe (iOS/Desktop) so it fills the content-area. -->
  <div :style="useIframe ? 'width:100%;height:100%;' : 'width:100%;'">
    <div v-if="loading" style="padding:40px 0;text-align:center;color:#6b7280;font-size:14px;">
      Загрузка PDF...
    </div>
    <div v-else-if="error" style="padding:40px 16px;text-align:center;">
      <div style="font-size:40px;">⚠️</div>
      <p style="color:#f87171;font-size:14px;margin-top:8px;">{{ error }}</p>
    </div>
    <!-- iOS Safari & Desktop: native PDF rendering inside iframe via blob URL.
         Safari has a built-in PDF engine that supports pinch-zoom and scroll. -->
    <iframe
      v-else-if="useIframe"
      :src="blobUrl"
      style="width:100%;height:100%;border:none;display:block;"
    />
    <!-- Android: PDF.js canvas rendering (works reliably, no iframe PDF support) -->
    <div
      v-else
      ref="container"
      style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:12px 4px;"
    >
      <canvas
        v-for="n in pageCount"
        :key="n"
        :ref="el => mountCanvas(el, n)"
        style="display:block;"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import api from '@/services/api'

// iOS Safari: use native iframe + blob URL.
// It renders PDFs natively with pinch-zoom and proper scroll.
// Android Chrome: use PDF.js (iframe PDF support is unreliable on Android).
// Desktop: also use iframe — Chrome/Firefox/Edge have a built-in PDF viewer.
const isAndroid = /Android/i.test(navigator.userAgent)
const useIframe = !isAndroid

const props = defineProps({
  materialId: { type: String, required: true },
})

const loading = ref(true)
const error = ref(null)
const blobUrl = ref(null)   // used when useIframe
const pageCount = ref(0)    // used when !useIframe (PDF.js)
const container = ref(null) // used when !useIframe

let pdfjsLib = null
async function getPdfJs() {
  if (!pdfjsLib) {
    pdfjsLib = await import('pdfjs-dist')
    pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
      'pdfjs-dist/build/pdf.worker.min.mjs',
      import.meta.url
    ).href
  }
  return pdfjsLib
}

let pdfDoc = null
let destroyed = false
const canvasMap = {}

function mountCanvas(el, n) {
  if (!el) return
  canvasMap[n] = el
  if (pdfDoc) renderPage(n)
}

async function renderPage(n) {
  const canvas = canvasMap[n]
  if (!canvas || !pdfDoc) return
  try {
    const page = await pdfDoc.getPage(n)
    const parent = container.value?.parentElement
    const w = (parent?.clientWidth > 10 ? parent.clientWidth : null)
      ?? (container.value?.clientWidth > 10 ? container.value.clientWidth : null)
      ?? window.innerWidth
    const containerWidth = Math.max(w, 200) - 8
    const baseViewport = page.getViewport({ scale: 1 })
    const dpr = window.devicePixelRatio || 1
    const scale = (containerWidth / baseViewport.width) * dpr
    const viewport = page.getViewport({ scale })
    canvas.width = viewport.width
    canvas.height = viewport.height
    canvas.style.width = `${containerWidth}px`
    canvas.style.height = `${Math.round(viewport.height / dpr)}px`
    await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise
  } catch { /* ignore single-page errors */ }
}

async function load() {
  if (!props.materialId) return
  loading.value = true
  error.value = null

  // Clean up previous state
  if (blobUrl.value) { URL.revokeObjectURL(blobUrl.value); blobUrl.value = null }
  pageCount.value = 0
  Object.keys(canvasMap).forEach(k => delete canvasMap[k])
  if (pdfDoc) { pdfDoc.destroy(); pdfDoc = null }

  try {
    // Fetch as blob — works for both paths; Axios sends Authorization header correctly
    const { data: blob } = await api.get(`/learner/materials/${props.materialId}/view`, {
      responseType: 'blob',
    })
    if (destroyed) return

    if (useIframe) {
      // iOS / Desktop: create an object URL and let the browser render natively
      blobUrl.value = URL.createObjectURL(blob)
      loading.value = false
    } else {
      // Android: parse with PDF.js
      const lib = await getPdfJs()
      if (destroyed) return
      const arrayBuffer = await blob.arrayBuffer()
      if (destroyed) return
      pdfDoc = await lib.getDocument({ data: arrayBuffer }).promise
      if (destroyed) return
      pageCount.value = pdfDoc.numPages
      loading.value = false
    }
  } catch {
    if (!destroyed) {
      error.value = 'Не удалось загрузить PDF'
      loading.value = false
    }
  }
}

onMounted(() => { requestAnimationFrame(() => { if (!destroyed) load() }) })
onUnmounted(() => {
  destroyed = true
  if (blobUrl.value) URL.revokeObjectURL(blobUrl.value)
  pdfDoc?.destroy()
})
watch(() => props.materialId, load)
</script>
