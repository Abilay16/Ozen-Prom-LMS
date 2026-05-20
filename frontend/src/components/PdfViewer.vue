<template>
  <div :style="isAndroid ? 'width:100%;' : 'width:100%;height:100%;'">
    <div v-if="loading" style="padding:40px 0;text-align:center;color:#6b7280;font-size:14px;">
      Загрузка PDF...
    </div>
    <div v-else-if="error" style="padding:40px 16px;text-align:center;">
      <div style="font-size:40px;">&#9888;&#65039;</div>
      <p style="color:#f87171;font-size:14px;margin-top:8px;">{{ error }}</p>
    </div>

    <!-- iOS Safari & Desktop: direct URL in iframe.
         Safari CANNOT render PDFs from blob: URLs — requires a real HTTP URL.
         Chrome/Firefox/Edge also handle direct-URL iframes natively. -->
    <iframe
      v-else-if="!isAndroid"
      :src="directUrl"
      style="width:100%;height:100%;border:none;display:block;"
    />

    <!-- Android Chrome: PDF.js canvas rendering -->
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
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '@/services/api'

const isAndroid = /Android/i.test(navigator.userAgent)

const props = defineProps({
  materialId: { type: String, required: true },
})

// iOS / Desktop: direct URL with token in query param.
// This is the only reliable way to show PDFs in Safari iframe.
const directUrl = computed(() => {
  const token = localStorage.getItem('access_token') || ''
  return `/api/v1/learner/materials/${props.materialId}/view?token=${encodeURIComponent(token)}`
})

const loading = ref(true)
const error = ref(null)

// PDF.js state — Android only
const pageCount = ref(0)
const container = ref(null)
let pdfjsLib = null
let pdfDoc = null
let destroyed = false
const canvasMap = {}

async function getPdfJs() {
  if (!pdfjsLib) {
    pdfjsLib = await import('pdfjs-dist')
    pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
      'pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url
    ).href
  }
  return pdfjsLib
}

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
  } catch { /* ignore */ }
}

function load() {
  if (!props.materialId) return
  loading.value = true
  error.value = null

  if (!isAndroid) {
    // directUrl computed prop handles it; just dismiss the spinner
    loading.value = false
  } else {
    loadAndroid()
  }
}

async function loadAndroid() {
  pageCount.value = 0
  Object.keys(canvasMap).forEach(k => delete canvasMap[k])
  if (pdfDoc) { pdfDoc.destroy(); pdfDoc = null }
  try {
    const lib = await getPdfJs()
    if (destroyed) return
    const { data: blob } = await api.get(`/learner/materials/${props.materialId}/view`, { responseType: 'blob' })
    if (destroyed) return
    const buf = await blob.arrayBuffer()
    if (destroyed) return
    pdfDoc = await lib.getDocument({ data: buf }).promise
    if (destroyed) return
    pageCount.value = pdfDoc.numPages
    loading.value = false
  } catch {
    if (!destroyed) { error.value = 'Не удалось загрузить PDF'; loading.value = false }
  }
}

onMounted(() => { requestAnimationFrame(() => { if (!destroyed) load() }) })
onUnmounted(() => { destroyed = true; pdfDoc?.destroy() })
watch(() => props.materialId, load)
</script>