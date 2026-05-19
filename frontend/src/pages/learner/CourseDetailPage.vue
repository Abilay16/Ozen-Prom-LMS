<template>
  <div v-if="loading" class="text-gray-500">Загрузка...</div>
  <div v-else-if="assignment">
    <!-- Back -->
    <RouterLink to="/my/courses" class="text-sm text-brand-mid hover:underline mb-4 inline-block">← Мои курсы</RouterLink>

    <div class="card mb-6">
      <div class="flex items-center justify-between mb-4">
        <span :class="statusBadge(assignment.status)">{{ statusLabel(assignment.status) }}</span>
        <span class="text-sm text-gray-400">{{ assignment.discipline?.name }}</span>
      </div>
      <h1 class="text-2xl font-bold mb-2">{{ assignment.course?.name }}</h1>
      <p class="text-gray-600">{{ assignment.course?.description }}</p>
    </div>

    <!-- Materials -->
    <div class="card mb-6">
      <h2 class="font-semibold text-lg mb-4">Материалы курса</h2>
      <div v-if="!assignment.course?.materials?.length" class="text-gray-400 text-sm">Материалы не добавлены</div>
      <div class="space-y-2">
        <div
          v-for="(mat, idx) in assignment.course?.materials"
          :key="mat.id"
          class="flex items-center gap-3 p-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <span class="text-2xl flex-shrink-0">{{ materialIcon(mat.material_type) }}</span>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-sm truncate">{{ mat.title }}</div>
            <div class="text-xs text-gray-400">{{ matTypeLabel(mat.material_type) }}</div>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <!-- External link -->
            <a
              v-if="mat.material_type === 'external_link' && mat.url"
              :href="mat.url"
              target="_blank"
              class="text-xs px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg font-medium"
            >Открыть ↗</a>
            <!-- Viewable or downloadable file -->
            <template v-else>
              <button
                @click="openViewer(idx)"
                class="text-xs px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg font-medium"
              >👁 Открыть</button>
              <button
                v-if="mat.file_path"
                @click="downloadMaterial(mat)"
                class="text-xs text-gray-500 hover:text-gray-700 px-2 py-1.5 hover:underline"
              >↓ Скачать</button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Test section -->
    <div class="card">
      <h2 class="font-semibold text-lg mb-2">Тест</h2>
      <div v-if="assignment.status === 'passed'" class="text-green-600 font-medium mb-4">
        ✓ Тест пройден
        <span v-if="assignment.course?.test?.pass_score" class="text-sm text-gray-400 ml-2">(проходной балл: {{ assignment.course.test.pass_score }}%)</span>
      </div>
      <div v-else-if="assignment.status === 'failed'" class="text-red-500 font-medium mb-4">
        Попытки исчерпаны ({{ completedAttempts }} из {{ assignment.course.test?.max_attempts || '∞' }})
      </div>
      <div v-else>
        <p class="text-sm text-gray-600 mb-3">После изучения материалов пройдите тест для завершения курса.</p>
        <div v-if="assignment.course?.test" class="text-sm text-gray-500 mb-4 flex gap-4">
          <span>Попытка <strong>{{ completedAttempts + 1 }}</strong> из <strong>{{ assignment.course.test.max_attempts > 0 ? assignment.course.test.max_attempts : '∞' }}</strong></span>
          <span>Проходной балл: <strong>{{ assignment.course.test.pass_score }}%</strong></span>
          <span v-if="assignment.course.test.time_limit_minutes > 0">Время: <strong>{{ assignment.course.test.time_limit_minutes }} мин</strong></span>
        </div>
        <button @click="startTest" :disabled="starting" class="btn-primary">
          {{ starting ? 'Запуск...' : 'Начать тест' }}
        </button>
      </div>
    </div>

    <!-- ========== FULLSCREEN MATERIAL VIEWER ========== -->
    <teleport to="body">
      <div v-if="viewerOpen" class="fixed inset-0 z-50 flex flex-col bg-black">
        <!-- Header -->
        <div class="flex items-center gap-3 px-4 py-3 bg-gray-900 text-white flex-shrink-0">
          <span class="text-xl flex-shrink-0">{{ materialIcon(currentMat.material_type) }}</span>
          <div class="flex-1 min-w-0">
            <div class="font-medium text-sm truncate">{{ currentMat.title }}</div>
            <div class="text-xs text-gray-400">{{ matTypeLabel(currentMat.material_type) }}</div>
          </div>
          <span class="text-xs text-gray-400 flex-shrink-0">{{ viewerIndex + 1 }} / {{ allMaterials.length }}</span>
          <button @click="closeViewer" class="flex-shrink-0 w-8 h-8 flex items-center justify-center text-gray-300 hover:text-white text-xl leading-none">×</button>
        </div>

        <!-- Content area -->
        <div class="flex-1 min-h-0 bg-gray-100 relative overflow-hidden">
          <!-- PDF: rendered by PDF.js (works on Android, iOS, Desktop) -->
          <PdfViewer
            v-if="currentViewerType === 'pdf'"
            :material-id="String(currentMat.id)"
            class="w-full h-full"
          />

          <!-- Image -->
          <div
            v-else-if="currentViewerType === 'image' && viewerSrcs[currentMat.id]"
            class="w-full h-full flex items-center justify-center overflow-auto p-4 bg-gray-800"
          >
            <img :src="viewerSrcs[currentMat.id]" class="max-w-full max-h-full object-contain rounded" alt="" />
          </div>

          <!-- Video file -->
          <div v-else-if="currentViewerType === 'video' && viewerSrcs[currentMat.id]" class="w-full h-full flex items-center justify-center bg-black">
            <video
              :src="viewerSrcs[currentMat.id]"
              controls
              preload="metadata"
              playsinline
              class="w-full h-full object-contain"
            ></video>
          </div>

          <!-- YouTube embed -->
          <iframe
            v-else-if="currentMat.material_type === 'video_url' && youtubeId(currentMat.url)"
            :src="`https://www.youtube.com/embed/${youtubeId(currentMat.url)}`"
            class="w-full h-full border-0"
            allowfullscreen
          ></iframe>

          <!-- Other video URL -->
          <div v-else-if="currentMat.material_type === 'video_url' && currentMat.url" class="flex flex-col items-center justify-center h-full gap-4 text-white">
            <span class="text-5xl">▶️</span>
            <a :href="currentMat.url" target="_blank" class="text-blue-400 underline text-sm">Открыть видео в новой вкладке ↗</a>
          </div>

          <!-- Loading spinner -->
          <div v-else-if="viewerLoadingMap[currentMat.id]" class="flex items-center justify-center h-full text-gray-500">
            <span class="text-sm">Загрузка...</span>
          </div>

          <!-- Not previewable: ppt/pptx/docx — PDF sidecar not ready yet or unsupported -->
          <div v-else class="flex flex-col items-center justify-center h-full gap-3 px-6 text-center">
            <span class="text-6xl">{{ materialIcon(currentMat.material_type) }}</span>
            <p class="text-base font-semibold text-gray-700">{{ currentMat.title }}</p>
            <template v-if="isOfficefile(currentMat)">
              <p class="text-sm text-gray-500">
                Файл <strong>{{ fileExtLabel(currentMat) }}</strong> — PDF-версия ещё создаётся на сервере.
              </p>
              <p class="text-xs text-gray-400">Попробуйте открыть через несколько секунд или скачайте файл.</p>
              <div class="flex gap-3 mt-2">
                <button @click="retryLoad(currentMat)" class="px-5 py-2 bg-gray-700 text-white rounded-lg text-sm font-medium hover:bg-gray-600">
                  ↺ Обновить
                </button>
                <button v-if="currentMat.file_path" @click="downloadMaterial(currentMat)" class="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                  ↓ Скачать
                </button>
              </div>
            </template>
            <template v-else>
              <p class="text-sm text-gray-500">
                Формат <strong>{{ fileExtLabel(currentMat) }}</strong> не поддерживает просмотр в браузере.
              </p>
              <button v-if="currentMat.file_path" @click="downloadMaterial(currentMat)" class="mt-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                ↓ Скачать и открыть
              </button>
            </template>
          </div>
        </div>

        <!-- Footer navigation -->
        <div class="flex items-center justify-between px-4 py-3 bg-gray-900 flex-shrink-0">
          <button
            @click="prevMaterial"
            :disabled="viewerIndex === 0"
            class="px-5 py-2 rounded-lg text-sm font-medium border border-gray-600 text-white hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >← Назад</button>

          <button
            v-if="currentMat.file_path"
            @click="downloadMaterial(currentMat)"
            class="text-xs text-gray-400 hover:text-white transition-colors"
          >↓ Скачать</button>
          <span v-else></span>

          <button
            @click="nextMaterial"
            :disabled="viewerIndex === allMaterials.length - 1"
            class="px-5 py-2 rounded-lg text-sm font-medium border border-gray-600 text-white hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >Вперёд →</button>
        </div>
      </div>
    </teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import api from '@/services/api'
import PdfViewer from '@/components/PdfViewer.vue'

const route = useRoute()
const router = useRouter()
const assignment = ref(null)
const loading = ref(true)
const starting = ref(false)

// Viewer state
const viewerOpen = ref(false)
const viewerIndex = ref(0)
const viewerSrcs = ref({})
const viewerLoadingMap = ref({})

const allMaterials = computed(() => assignment.value?.course?.materials ?? [])
const currentMat = computed(() => allMaterials.value[viewerIndex.value] ?? {})

// Overridden when an office file (ppt/docx) turns out to have a converted PDF preview
const viewerTypeOverride = ref({})

// Detect actual viewable type — prefers override (set after HEAD check reveals PDF sidecar)
const currentViewerType = computed(() =>
  viewerTypeOverride.value[currentMat.value.id] ?? fileViewerType(currentMat.value)
)

function fileExt(mat) {
  if (!mat?.file_path) return ''
  return mat.file_path.split('.').pop().toLowerCase()
}

function fileViewerType(mat) {
  const ext = fileExt(mat)
  if (ext === 'pdf') return 'pdf'
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return 'image'
  if (['mp4', 'webm', 'ogv', 'mov'].includes(ext)) return 'video'
  return null // ppt, pptx, doc, docx, zip, etc. — not viewable inline
}

function fileExtLabel(mat) {
  const ext = fileExt(mat)
  const labels = {
    ppt: 'PowerPoint (.ppt)', pptx: 'PowerPoint (.pptx)',
    doc: 'Word (.doc)', docx: 'Word (.docx)',
    xls: 'Excel (.xls)', xlsx: 'Excel (.xlsx)',
    zip: 'ZIP Архив', rar: 'RAR Архив',
  }
  return labels[ext] || (ext ? `.${ext}` : 'неизвестный формат')
}

const completedAttempts = computed(() =>
  assignment.value?.attempts?.filter(a => a.status === 'completed').length ?? 0
)

onMounted(async () => {
  try {
    const { data } = await api.get(`/learner/me/courses/${route.params.id}`)
    assignment.value = data
  } finally {
    loading.value = false
  }
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  // Revoke any blob URLs to avoid memory leaks
  Object.values(viewerSrcs.value).forEach(src => {
    if (src && src.startsWith('blob:')) URL.revokeObjectURL(src)
  })
})

function onKey(e) {
  if (!viewerOpen.value) return
  if (e.key === 'Escape') closeViewer()
  if (e.key === 'ArrowRight') nextMaterial()
  if (e.key === 'ArrowLeft') prevMaterial()
}

async function openViewer(idx) {
  viewerIndex.value = idx
  viewerOpen.value = true
  document.body.style.overflow = 'hidden'
  await loadSrc(allMaterials.value[idx])
}

function closeViewer() {
  viewerOpen.value = false
  document.body.style.overflow = ''
}

async function nextMaterial() {
  if (viewerIndex.value >= allMaterials.value.length - 1) return
  viewerIndex.value++
  await loadSrc(allMaterials.value[viewerIndex.value])
}

async function prevMaterial() {
  if (viewerIndex.value <= 0) return
  viewerIndex.value--
  await loadSrc(allMaterials.value[viewerIndex.value])
}

const _OFFICE_EXTS = ['ppt', 'pptx', 'doc', 'docx']

function isOfficefile(mat) {
  return _OFFICE_EXTS.includes(fileExt(mat))
}

async function loadSrc(mat) {
  if (!mat?.id) return
  if (mat.id in viewerSrcs.value) return // already checked (may be null = not previewable)
  if (mat.material_type === 'external_link' || mat.material_type === 'video_url') return
  if (!mat.file_path) return

  const vtype = fileViewerType(mat)
  const token = localStorage.getItem('access_token')

  if (vtype === 'video') {
    // Video stream still uses token-in-URL (HTML5 video can't send custom headers)
    viewerSrcs.value = { ...viewerSrcs.value, [mat.id]: `/api/v1/learner/materials/${mat.id}/stream?token=${token}` }
  } else if (vtype === 'pdf') {
    // PdfViewer fetches internally via Authorization header — just mark as ready
    viewerSrcs.value = { ...viewerSrcs.value, [mat.id]: true }
  } else if (vtype === 'image') {
    // Fetch image as blob so token never appears in the URL
    try {
      const { data } = await api.get(`/learner/materials/${mat.id}/view`, { responseType: 'blob' })
      viewerSrcs.value = { ...viewerSrcs.value, [mat.id]: URL.createObjectURL(data) }
    } catch {
      viewerSrcs.value = { ...viewerSrcs.value, [mat.id]: null }
    }
  } else if (_OFFICE_EXTS.includes(fileExt(mat))) {
    // Office file: check if server has the converted PDF sidecar ready
    viewerLoadingMap.value = { ...viewerLoadingMap.value, [mat.id]: true }
    try {
      await api.head(`/learner/materials/${mat.id}/view`)
      // PDF sidecar is ready — show via PdfViewer
      viewerSrcs.value = { ...viewerSrcs.value, [mat.id]: true }
      viewerTypeOverride.value = { ...viewerTypeOverride.value, [mat.id]: 'pdf' }
    } catch {
      // Still converting or conversion failed — show placeholder
      viewerSrcs.value = { ...viewerSrcs.value, [mat.id]: null }
    } finally {
      viewerLoadingMap.value = { ...viewerLoadingMap.value, [mat.id]: false }
    }
  } else {
    // zip, rar, etc. — not previewable
    viewerSrcs.value = { ...viewerSrcs.value, [mat.id]: null }
  }
}

async function retryLoad(mat) {
  // Clear cache and re-check (for when conversion was still in progress)
  const newSrcs = { ...viewerSrcs.value }
  const newOverrides = { ...viewerTypeOverride.value }
  delete newSrcs[mat.id]
  delete newOverrides[mat.id]
  viewerSrcs.value = newSrcs
  viewerTypeOverride.value = newOverrides
  await loadSrc(mat)
}

async function startTest() {
  starting.value = true
  try {
    const { data } = await api.post(`/learner/me/courses/${route.params.id}/start-test`)
    sessionStorage.setItem('testData_' + data.attempt_id, JSON.stringify(data))
    router.push({ path: `/my/test/${data.attempt_id}`, state: { testData: data } })
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    starting.value = false
  }
}

function materialIcon(type) {
  const icons = { video_file: '🎬', video_url: '▶️', pdf: '📄', docx: '📝', image: '🖼️', external_link: '🔗' }
  return icons[type] || '📎'
}

function matTypeLabel(type) {
  return { pdf: 'PDF документ', image: 'Изображение', video_file: 'Видеофайл', docx: 'Word документ', video_url: 'Видео', external_link: 'Внешняя ссылка' }[type] || type
}

function youtubeId(url) {
  if (!url) return null
  const m = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/)
  return m ? m[1] : null
}

async function downloadMaterial(mat) {
  try {
    const { data } = await api.get(`/learner/materials/${mat.id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = mat.title || 'file'
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    alert('Не удалось скачать файл')
  }
}

function statusBadge(s) {
  return { assigned: 'badge-assigned', in_progress: 'badge-progress', passed: 'badge-passed', failed: 'badge-failed' }[s] || 'badge-assigned'
}
function statusLabel(s) {
  return { assigned: 'Назначен', in_progress: 'В процессе', passed: 'Сдан ✓', failed: 'Не сдан' }[s] || s
}
</script>
