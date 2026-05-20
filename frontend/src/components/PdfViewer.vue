<template>
  <!-- Android: width only (parent content-area is the scroll container for multipage) -->
  <!-- iOS: height:100% (internal flex layout with its own scroll) -->
  <!-- Desktop: height:100% (iframe fills) -->
  <div :style="isAndroid ? 'width:100%;' : 'width:100%;height:100%;'">
    <div v-if="loading" style="padding:40px 0;text-align:center;color:#6b7280;font-size:14px;">
      Загрузка PDF...
    </div>
    <div v-else-if="error" style="padding:40px 16px;text-align:center;">
      <span style="font-size:40px;">&#9888;&#65039;</span>
      <p style="color:#f87171;font-size:14px;margin-top:8px;">{{ error }}</p>
    </div>

    <!-- iOS: single-page PDF.js with zoom and page navigation.
         iframe inside position:fixed does NOT scroll on iOS — known WebKit limitation.
         PDF.js single-page avoids canvas GPU memory limits (no blank pages). -->
    <div v-else-if="isIOS" style="height:100%;display:flex;flex-direction:column;">
      <!-- Controls -->
      <div style="display:flex;align-items:center;gap:8px;padding:6px 10px;background:#e5e7eb;flex-shrink:0;">
        <button @click="zoomOut"
          style="width:32px;height:32px;font-size:20px;border-radius:6px;background:#fff;border:1px solid #d1d5db;display:flex;align-items:center;justify-content:center;cursor:pointer;">−</button>
        <span style="font-size:13px;color:#374151;min-width:40px;text-align:center;">{{ Math.round(zoom*100) }}%</span>
        <button @click="zoomIn"
          style="width:32px;height:32px;font-size:20px;border-radius:6px;background:#fff;border:1px solid #d1d5db;display:flex;align-items:center;justify-content:center;cursor:pointer;">+</button>
        <div style="flex:1;"></div>
        <button @click="prevPage" :disabled="currentPage <= 1"
          style="padding:4px 12px;border-radius:6px;background:#fff;border:1px solid #d1d5db;font-size:13px;cursor:pointer;opacity:1;"
          :style="currentPage <= 1 ? 'opacity:0.35;cursor:default;' : ''">◀</button>
        <span style="font-size:13px;color:#374151;">{{ currentPage }} / {{ totalPages }}</span>
        <button @click="nextPage" :disabled="currentPage >= totalPages"
          style="padding:4px 12px;border-radius:6px;background:#fff;border:1px solid #d1d5db;font-size:13px;cursor:pointer;"
          :style="currentPage >= totalPages ? 'opacity:0.35;cursor:default;' : ''">▶</button>
      </div>
      <!-- Debug status — remove after fix confirmed -->
      <div style="font-size:10px;color:#666;padding:2px 10px;background:#f9fafb;flex-shrink:0;">{{ iosStatus }}</div>
      <!-- Scrollable canvas area -->
      <div style="flex:1;min-height:0;overflow:auto;-webkit-overflow-scrolling:touch;display:flex;justify-content:center;align-items:flex-start;background:#f3f4f6;padding:8px 0;">
        <canvas ref="iosCanvas" style="display:block;flex-shrink:0;"/>
      </div>
    </div>

    <!-- Desktop: direct URL iframe (Chrome/Firefox/Edge built-in PDF viewer) -->
    <iframe
      v-else-if="isDesktop"
      :src="directUrl"
      style="width:100%;height:100%;border:none;display:block;"
    />

    <!-- Android: multi-page PDF.js (parent content-area scrolls) -->
    <div
      v-else
      ref="androidContainer"
      style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:12px 4px;"
    >
      <canvas
        v-for="n in pageCount"
        :key="n"
        :ref="el => mountAndroidCanvas(el, n)"
        style="display:block;"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import api from '@/services/api'

const isAndroid = /Android/i.test(navigator.userAgent)
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
const isDesktop = !isAndroid && !isIOS

const props = defineProps({
  materialId: { type: String, required: true },
})

// Desktop: direct URL iframe
const directUrl = computed(() => {
  const token = localStorage.getItem('access_token') || ''
  return `/api/v1/learner/materials/${props.materialId}/view?token=${encodeURIComponent(token)}`
})

const loading = ref(true)
const error = ref(null)

// ── iOS state ──────────────────────────────────────
const iosCanvas = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)
const zoom = ref(1.0)   // 1.0 = fit to screen width
const iosStatus = ref('init')
let iosPdfDoc = null

async function renderIOSPage() {
  if (!iosPdfDoc) { iosStatus.value = 'no-doc'; return }
  if (!iosCanvas.value) { iosStatus.value = 'no-canvas'; return }
  iosStatus.value = 'rendering p' + currentPage.value
  try {
    const page = await iosPdfDoc.getPage(currentPage.value)
    const baseViewport = page.getViewport({ scale: 1 })
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const containerWidth = (window.innerWidth || 375) - 16
    const fitScale = containerWidth / baseViewport.width
    const renderScale = fitScale * zoom.value * dpr
    const cssWidth = Math.round(baseViewport.width * fitScale * zoom.value)
    const cssHeight = Math.round(baseViewport.height * fitScale * zoom.value)
    const vp = page.getViewport({ scale: renderScale })
    const canvas = iosCanvas.value
    canvas.width = vp.width
    canvas.height = vp.height
    canvas.style.width = cssWidth + 'px'
    canvas.style.height = cssHeight + 'px'
    const ctx = canvas.getContext('2d')
    if (!ctx) { iosStatus.value = 'err:no-ctx'; return }
    await page.render({ canvasContext: ctx, viewport: vp }).promise
    iosStatus.value = 'ok p' + currentPage.value + ' ' + cssWidth + 'x' + cssHeight
  } catch(e) {
    iosStatus.value = 'err:' + (e && e.message ? e.message.slice(0,60) : String(e))
    console.error('[PdfViewer iOS] render error:', e)
  }
}

function prevPage() { if (currentPage.value > 1) { currentPage.value--; renderIOSPage() } }
function nextPage() { if (currentPage.value < totalPages.value) { currentPage.value++; renderIOSPage() } }
function zoomIn()  { zoom.value = Math.min(zoom.value * 1.4, 4); renderIOSPage() }
function zoomOut() { zoom.value = Math.max(zoom.value / 1.4, 0.5); renderIOSPage() }

// ── Android state ──────────────────────────────────
const pageCount = ref(0)
const androidContainer = ref(null)
const androidCanvasMap = {}
let androidPdfDoc = null

function mountAndroidCanvas(el, n) {
  if (!el) return
  androidCanvasMap[n] = el
  if (androidPdfDoc) renderAndroidPage(n)
}

async function renderAndroidPage(n) {
  const canvas = androidCanvasMap[n]
  if (!canvas || !androidPdfDoc) return
  try {
    const page = await androidPdfDoc.getPage(n)
    const parent = androidContainer.value?.parentElement
    const w = (parent?.clientWidth > 10 ? parent.clientWidth : null)
      ?? (androidContainer.value?.clientWidth > 10 ? androidContainer.value.clientWidth : null)
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

// ── Shared ──────────────────────────────────────────
let pdfjsLib = null
let destroyed = false

async function getPdfJs() {
  if (!pdfjsLib) {
    pdfjsLib = await import('pdfjs-dist')
    pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
      'pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url
    ).href
  }
  return pdfjsLib
}

async function load() {
  if (!props.materialId) return
  loading.value = true
  error.value = null
  currentPage.value = 1
  zoom.value = 1.0
  totalPages.value = 0
  pageCount.value = 0
  Object.keys(androidCanvasMap).forEach(k => delete androidCanvasMap[k])
  iosPdfDoc?.destroy(); iosPdfDoc = null
  androidPdfDoc?.destroy(); androidPdfDoc = null

  if (isDesktop) {
    loading.value = false
    return
  }

  try {
    const lib = await getPdfJs()
    if (destroyed) return
    const { data: blob } = await api.get(`/learner/materials/${props.materialId}/view`, { responseType: 'blob' })
    if (destroyed) return
    const buf = await blob.arrayBuffer()
    if (destroyed) return

    if (isIOS) {
      iosPdfDoc = await lib.getDocument({ data: buf }).promise
      if (destroyed) return
      totalPages.value = iosPdfDoc.numPages
      loading.value = false
      // watch(iosCanvas) below fires when canvas enters the DOM and calls renderIOSPage()
    } else {
      androidPdfDoc = await lib.getDocument({ data: buf }).promise
      if (destroyed) return
      pageCount.value = androidPdfDoc.numPages
      loading.value = false
    }
  } catch(e) {
    console.error('[PdfViewer] load error:', e)
    if (!destroyed) { error.value = 'Не удалось загрузить PDF'; loading.value = false }
  }
}

// flush:'post' ensures the watch fires AFTER Vue has written the canvas element to the DOM.
// Default flush:'pre' fires before DOM update — canvas may not exist yet on Safari.
watch(iosCanvas, (el) => {
  if (el && iosPdfDoc) renderIOSPage()
}, { flush: 'post' })

// Backup: if watch(iosCanvas) misses (can happen on Safari), this catches the transition.
watch(loading, (val) => {
  if (!val && isIOS && iosPdfDoc) {
    nextTick(() => { if (iosCanvas.value) renderIOSPage() })
  }
})

onMounted(() => { requestAnimationFrame(() => { if (!destroyed) load() }) })
onUnmounted(() => {
  destroyed = true
  iosPdfDoc?.destroy()
  androidPdfDoc?.destroy()
})
watch(() => props.materialId, load)
</script>