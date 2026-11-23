<template>
  <div v-if="loading" class="space-y-3">
    <span class="skel" style="width: 6rem; height: 0.9rem;" />
    <div class="panel"><span class="skel" style="width: 60%; height: 1.4rem;" /><span class="skel mt-3" style="width: 85%; height: 0.9rem;" /></div>
    <div class="panel"><span class="skel" style="width: 100%; height: 3rem;" /></div>
  </div>

  <div v-else-if="!assignment" class="panel text-center text-gray-500">
    Курс не найден.
    <RouterLink to="/my/courses" class="block mt-2 text-sm font-medium text-blue-700">Вернуться к моим курсам</RouterLink>
  </div>

  <div v-else>
    <RouterLink to="/my/courses" class="back-link">
      <ChevronLeft :size="16" :stroke-width="2.4" /> Мои курсы
    </RouterLink>

    <!-- Курс -->
    <section class="panel hero">
      <div class="flex items-center justify-between gap-3">
        <span class="status" :class="`status--${assignment.status}`">
          <component :is="STATUS[assignment.status]?.icon || Circle" :size="14" :stroke-width="2.4" />
          {{ STATUS[assignment.status]?.label || assignment.status }}
        </span>
        <span class="discipline">{{ assignment.discipline?.name }}</span>
      </div>
      <h1 class="hero__title">{{ assignment.course?.name }}</h1>
      <p v-if="assignment.course?.description" class="hero__desc">{{ assignment.course.description }}</p>
    </section>

    <!-- Шаг 1: материалы -->
    <section class="panel">
      <h2 class="step-title"><span class="step-num">1</span> Изучите материалы</h2>
      <p v-if="!allMaterials.length" class="muted">Материалы к курсу не добавлены — можно сразу переходить к тесту.</p>
      <ul v-else class="materials">
        <li v-for="(mat, idx) in allMaterials" :key="mat.id" class="material">
          <a
            v-if="mat.material_type === 'external_link' && mat.url"
            :href="mat.url" target="_blank" rel="noopener" class="material__main"
          >
            <span class="material__icon"><component :is="materialIcon(mat.material_type)" :size="20" :stroke-width="1.9" /></span>
            <span class="material__text">
              <span class="material__title">{{ mat.title }}</span>
              <span class="material__type">{{ matTypeLabel(mat.material_type) }} · откроется в новой вкладке</span>
            </span>
            <ExternalLink :size="18" class="material__chev" />
          </a>
          <button v-else type="button" class="material__main" @click="openViewer(idx)">
            <span class="material__icon"><component :is="materialIcon(mat.material_type)" :size="20" :stroke-width="1.9" /></span>
            <span class="material__text">
              <span class="material__title">{{ mat.title }}</span>
              <span class="material__type">{{ matTypeLabel(mat.material_type) }}</span>
            </span>
            <ChevronRight :size="18" class="material__chev" />
          </button>
          <button
            v-if="mat.file_path"
            type="button" class="material__dl" :title="`Скачать «${mat.title}»`" :aria-label="`Скачать «${mat.title}»`"
            @click="downloadMaterial(mat)"
          >
            <Download :size="18" :stroke-width="2" />
          </button>
        </li>
      </ul>
    </section>

    <!-- Шаг 2: тест -->
    <section class="panel">
      <h2 class="step-title"><span class="step-num">2</span> Пройдите тест</h2>

      <div v-if="!assignment.course?.test" class="muted">Тест к этому курсу ещё не добавлен. Обратитесь к администратору.</div>

      <div v-else-if="assignment.status === 'passed'" class="outcome outcome--ok">
        <CircleCheck :size="22" :stroke-width="2.2" />
        <div>
          <div class="outcome__title">Тест сдан<template v-if="bestScore !== null"> — {{ bestScore }}%</template></div>
          <div class="outcome__text">Удостоверение появится в разделе «Удостоверения» после подписания протокола комиссией.</div>
        </div>
      </div>

      <div v-else-if="assignment.status === 'failed'" class="outcome outcome--bad">
        <CircleX :size="22" :stroke-width="2.2" />
        <div>
          <div class="outcome__title">Попытки исчерпаны</div>
          <div class="outcome__text">
            Использовано {{ completedAttempts }} из {{ test.max_attempts || '∞' }}<template v-if="bestScore !== null">, лучший результат {{ bestScore }}%</template>.
            Чтобы получить ещё попытку, обратитесь к администратору учебного центра.
          </div>
        </div>
      </div>

      <template v-else>
        <dl class="facts">
          <div><dt>Проходной балл</dt><dd>{{ test.pass_score }}%</dd></div>
          <div><dt>Попытка</dt><dd>{{ completedAttempts + 1 }} из {{ test.max_attempts > 0 ? test.max_attempts : '∞' }}</dd></div>
          <div v-if="test.time_limit_minutes > 0"><dt>Время</dt><dd>{{ test.time_limit_minutes }} мин</dd></div>
        </dl>
        <p v-if="test.time_limit_minutes > 0" class="muted mt-3">
          Таймер запустится сразу после нажатия. Если время выйдет, тест сдастся автоматически с выбранными ответами.
        </p>
        <button type="button" class="start-btn" :disabled="starting" @click="startTest">
          <Loader2 v-if="starting" :size="18" class="animate-spin" />
          {{ starting ? 'Запускаем…' : (completedAttempts ? 'Пройти тест ещё раз' : 'Начать тест') }}
        </button>
      </template>
    </section>

    <!-- ========== FULLSCREEN MATERIAL VIEWER ========== -->
    <teleport to="body">
      <div v-if="viewerOpen" class="fixed inset-0 z-50 flex flex-col bg-black">
        <!-- Header -->
        <div class="flex items-center gap-3 px-4 py-3 bg-gray-900 text-white flex-shrink-0">
          <component :is="materialIcon(currentMat.material_type)" :size="20" class="flex-shrink-0 text-gray-300" />
          <div class="flex-1 min-w-0">
            <div class="font-medium text-sm truncate">{{ currentMat.title }}</div>
            <div class="text-xs text-gray-400">{{ matTypeLabel(currentMat.material_type) }}</div>
          </div>
          <span class="text-xs text-gray-400 flex-shrink-0">{{ viewerIndex + 1 }} / {{ allMaterials.length }}</span>
          <button @click="closeViewer" class="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-lg text-gray-300 hover:text-white hover:bg-white/10" aria-label="Закрыть"><X :size="20" /></button>
        </div>

        <!-- Content area -->
        <!-- iOS Safari requires overflow-y:scroll (not auto) on the actual scrolling element.
             When showing PDF we make this div the scroll container directly. -->
        <div
          class="flex-1 min-h-0 bg-gray-100 relative"
          :style="currentViewerType === 'pdf' && isAndroid
            ? 'overflow-y: scroll; overflow-x: hidden; -webkit-overflow-scrolling: touch; overscroll-behavior: contain;'
            : 'overflow: hidden;'"
        >
          <!-- PDF: rendered by PDF.js (works on Android, iOS, Desktop) -->
          <PdfViewer
            v-if="currentViewerType === 'pdf'"
            :material-id="String(currentMat.id)"
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
            <PlayCircle :size="48" :stroke-width="1.5" />
            <a :href="currentMat.url" target="_blank" class="text-blue-400 underline text-sm">Открыть видео в новой вкладке ↗</a>
          </div>

          <!-- Loading spinner -->
          <div v-else-if="viewerLoadingMap[currentMat.id]" class="flex items-center justify-center h-full text-gray-500">
            <span class="text-sm">Загрузка...</span>
          </div>

          <!-- Not previewable: ppt/pptx/docx — PDF sidecar not ready yet or unsupported -->
          <div v-else class="flex flex-col items-center justify-center h-full gap-3 px-6 text-center">
            <component :is="materialIcon(currentMat.material_type)" :size="48" :stroke-width="1.4" class="text-gray-400" />
            <p class="text-base font-semibold text-gray-700">{{ currentMat.title }}</p>
            <template v-if="isOfficefile(currentMat)">
              <p class="text-sm text-gray-500">
                Файл <strong>{{ fileExtLabel(currentMat) }}</strong> — PDF-версия ещё создаётся на сервере.
              </p>
              <p class="text-xs text-gray-400">Попробуйте открыть через несколько секунд или скачайте файл.</p>
              <div class="flex gap-3 mt-2">
                <button @click="retryLoad(currentMat)" class="px-5 py-2 bg-gray-700 text-white rounded-lg text-sm font-medium hover:bg-gray-600">
                  Обновить
                </button>
                <button v-if="currentMat.file_path" @click="downloadMaterial(currentMat)" class="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                  Скачать
                </button>
              </div>
            </template>
            <template v-else>
              <p class="text-sm text-gray-500">
                Формат <strong>{{ fileExtLabel(currentMat) }}</strong> не поддерживает просмотр в браузере.
              </p>
              <button v-if="currentMat.file_path" @click="downloadMaterial(currentMat)" class="mt-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                Скачать и открыть
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
          >Назад</button>

          <button
            v-if="currentMat.file_path"
            @click="downloadMaterial(currentMat)"
            class="text-xs text-gray-400 hover:text-white transition-colors"
          >Скачать</button>
          <span v-else></span>

          <button
            @click="nextMaterial"
            :disabled="viewerIndex === allMaterials.length - 1"
            class="px-5 py-2 rounded-lg text-sm font-medium border border-gray-600 text-white hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >Вперёд</button>
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
import {
  ChevronLeft, ChevronRight, Circle, CircleCheck, CircleX, Clock, Download, ExternalLink,
  FileText, Image as ImageIcon, Link2, Loader2, Paperclip, PlayCircle, Video, X,
} from 'lucide-vue-next'
import { useToast, apiErrorMessage } from '@/composables/useToast'

const toast = useToast()

// Android Chrome needs PDF.js (canvas, scrollable parent).
// iOS Safari and Desktop use native iframe rendering (scroll inside iframe).
const isAndroid = /Android/i.test(navigator.userAgent)

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
const test = computed(() => assignment.value?.course?.test || {})
const bestScore = computed(() => {
  const scores = (assignment.value?.attempts || []).map(a => a.score_percent).filter(s => s !== null && s !== undefined)
  return scores.length ? Math.max(...scores) : null
})

const STATUS = {
  assigned: { label: 'Назначен', icon: Circle },
  in_progress: { label: 'В процессе', icon: Clock },
  passed: { label: 'Сдан', icon: CircleCheck },
  failed: { label: 'Не сдан', icon: CircleX },
}

onMounted(async () => {
  try {
    const { data } = await api.get(`/learner/me/courses/${route.params.id}`)
    assignment.value = data
  } catch (e) {
    if (e.response?.status !== 404) toast.error(apiErrorMessage(e))
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
    toast.error(apiErrorMessage(e))
  } finally {
    starting.value = false
  }
}

function materialIcon(type) {
  return { video_file: Video, video_url: PlayCircle, pdf: FileText, docx: FileText, image: ImageIcon, external_link: Link2 }[type] || Paperclip
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
    // Название + расширение исходного файла: без расширения телефон не знает, чем открыть.
    const ext = fileExt(mat)
    const name = (mat.title || 'material').replace(/[\\/:*?"<>|]+/g, ' ').trim()
    a.download = ext && !name.toLowerCase().endsWith('.' + ext) ? `${name}.${ext}` : name
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    toast.error('Не удалось скачать файл')
  }
}

</script>

<style scoped>
.panel {
  background: #fff;
  border: 1px solid #e7e9ee;
  border-radius: 0.9rem;
  padding: 1.15rem;
  margin-bottom: 0.85rem;
}
@media (min-width: 640px) { .panel { padding: 1.4rem 1.5rem; } }

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  margin-bottom: 0.85rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #1f4f96;
  text-decoration: none;
}
.back-link:hover { text-decoration: underline; }

.status {
  display: inline-flex; align-items: center; gap: 0.3rem;
  font-size: 0.75rem; font-weight: 600;
  padding: 0.2rem 0.55rem 0.2rem 0.45rem; border-radius: 999px;
}
.status--assigned { background: #eef3fb; color: #1f4f96; }
.status--in_progress { background: #fff4e0; color: #9a5b00; }
.status--passed { background: #e7f6ee; color: #11683f; }
.status--failed { background: #fdecec; color: #a12a1f; }
.discipline { font-size: 0.75rem; color: #8a93a3; text-align: right; }

.hero__title {
  margin-top: 0.8rem;
  font-size: 1.4rem; font-weight: 700; line-height: 1.25; letter-spacing: -0.015em;
  color: #101828; text-wrap: balance;
}
.hero__desc { margin-top: 0.4rem; color: #4b5565; font-size: 0.925rem; text-wrap: pretty; }

.step-title {
  display: flex; align-items: center; gap: 0.6rem;
  font-size: 1.05rem; font-weight: 650; color: #101828; margin-bottom: 0.85rem;
}
.step-num {
  width: 1.6rem; height: 1.6rem; border-radius: 999px;
  display: grid; place-items: center;
  background: #1f3a5c; color: #fff; font-size: 0.8rem; font-weight: 700;
}
.muted { font-size: 0.875rem; color: #6b7280; text-wrap: pretty; }

.materials { display: flex; flex-direction: column; gap: 0.5rem; }
.material {
  display: flex; align-items: stretch;
  border: 1px solid #e7e9ee; border-radius: 0.75rem; overflow: hidden;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}
.material:hover { border-color: #c9d3e3; }
.material__main {
  flex: 1; min-width: 0;
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.7rem 0.8rem; text-align: left; text-decoration: none; color: inherit;
}
.material__main:hover { background: #f8fafc; }
.material__icon {
  width: 2.4rem; height: 2.4rem; border-radius: 0.6rem; flex-shrink: 0;
  display: grid; place-items: center; background: #eef3fb; color: #1f4f96;
}
.material__text { display: flex; flex-direction: column; min-width: 0; }
.material__title { font-weight: 550; font-size: 0.9rem; color: #101828; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.material__type { font-size: 0.75rem; color: #8a93a3; }
.material__chev { margin-left: auto; color: #a3abb8; flex-shrink: 0; }
.material__dl {
  width: 3rem; flex-shrink: 0;
  display: grid; place-items: center;
  border-left: 1px solid #eef0f4; color: #4b5565;
}
.material__dl:hover { background: #f1f3f6; color: #1f3a5c; }
.material__main:focus-visible, .material__dl:focus-visible, .start-btn:focus-visible { outline: 2px solid #2563eb; outline-offset: -2px; }

.facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr)); gap: 0.5rem; }
.facts > div { background: #f6f7f9; border-radius: 0.65rem; padding: 0.6rem 0.75rem; }
.facts dt { font-size: 0.72rem; color: #6b7280; }
.facts dd { font-size: 1rem; font-weight: 650; color: #101828; font-variant-numeric: tabular-nums; }

.start-btn {
  margin-top: 1rem; width: 100%;
  display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem;
  padding: 0.85rem 1.25rem; border-radius: 0.75rem;
  background: #2563eb; color: #fff; font-weight: 650; font-size: 1rem;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}
.start-btn:hover:not(:disabled) { background: #1d4ed8; box-shadow: 0 6px 16px -8px rgba(37, 99, 235, 0.7); }
.start-btn:disabled { opacity: 0.6; }
@media (min-width: 640px) { .start-btn { width: auto; min-width: 14rem; } }

.outcome { display: flex; gap: 0.75rem; align-items: flex-start; border-radius: 0.75rem; padding: 0.85rem 1rem; }
.outcome--ok { background: #e7f6ee; color: #11683f; }
.outcome--bad { background: #fdecec; color: #a12a1f; }
.outcome__title { font-weight: 650; }
.outcome__text { margin-top: 0.15rem; font-size: 0.85rem; color: #374151; text-wrap: pretty; }
</style>
