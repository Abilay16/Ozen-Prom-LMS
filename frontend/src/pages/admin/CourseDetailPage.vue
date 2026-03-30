<template>
  <div>
    <RouterLink to="/admin/courses" class="text-blue-600 text-sm hover:underline">&larr; Назад к курсам</RouterLink>
    <div class="mt-4 mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ course?.name || 'Загрузка...' }}</h1>
      <span v-if="course" class="text-sm text-gray-500">{{ course.discipline?.name }}</span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Materials -->
      <div class="card">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-semibold">Материалы</h2>
          <button @click="materialModal = true" class="text-sm text-blue-600 hover:underline">+ Добавить</button>
        </div>

        <!-- Add material modal -->
        <div v-if="materialModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div class="card w-full max-w-md">
            <h2 class="font-semibold mb-4">Новый материал</h2>
            <div class="space-y-3">
              <div>
                <label class="text-sm font-medium text-gray-700">Заголовок</label>
                <input v-model="matForm.title" class="input-field mt-1" />
              </div>
              <div>
                <label class="text-sm font-medium text-gray-700">Тип</label>
                <select v-model="matForm.material_type" class="input-field mt-1">
                  <option value="pdf">PDF документ</option>
                  <option value="video_url">Видео (URL / YouTube)</option>
                  <option value="video_file">Видео (файл)</option>
                  <option value="docx">Презентация / Word</option>
                  <option value="image">Изображение</option>
                  <option value="external_link">Внешняя ссылка</option>
                </select>
              </div>
              <div v-if="matForm.material_type === 'video_url' || matForm.material_type === 'external_link'">
                <label class="text-sm font-medium text-gray-700">{{ matForm.material_type === 'video_url' ? 'URL видео (YouTube, Vimeo...)' : 'URL ссылки' }}</label>
                <input v-model="matForm.url" class="input-field mt-1" placeholder="https://..." />
              </div>
              <div v-else>
                <label class="text-sm font-medium text-gray-700">Файл</label>
                <input ref="matFileInput" type="file" @change="e => matFile = e.target.files[0]" class="input-field mt-1" />
              </div>
            </div>
            <!-- Upload progress -->
            <div v-if="uploading" class="mt-3">
              <div class="flex justify-between text-xs text-gray-500 mb-1">
                <span>Загрузка файла...</span>
                <span>{{ uploadProgress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-blue-600 h-2 rounded-full transition-all duration-200" :style="{ width: uploadProgress + '%' }"></div>
              </div>
            </div>
            <div class="flex gap-3 mt-4">
              <button @click="uploadMaterial" :disabled="uploading" class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
                {{ uploading ? 'Загрузка...' : 'Загрузить' }}
              </button>
              <button @click="materialModal = false" :disabled="uploading" class="btn-secondary disabled:opacity-50">Отмена</button>
            </div>
          </div>
        </div>

        <ul class="space-y-2">
          <li v-for="m in materials" :key="m.id" class="flex items-center justify-between p-2 rounded bg-gray-50">
            <div class="flex items-center gap-2">
              <span>{{ matIcon(m.material_type) }}</span>
              <div>
                <span class="font-medium text-sm">{{ m.title }}</span>
                <span class="ml-2 text-xs text-gray-400">{{ m.material_type }}</span>
              </div>
            </div>
            <button @click="deleteMaterial(m.id)" class="text-red-400 text-xs hover:underline">Удалить</button>
          </li>
          <li v-if="!materials.length" class="text-sm text-gray-400 py-2">Материалы не добавлены</li>
        </ul>
      </div>

      <!-- Test -->
      <div class="card">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-semibold">Тест</h2>
          <button v-if="!test" @click="createTest" class="text-sm text-blue-600 hover:underline">+ Создать тест</button>
        </div>

        <div v-if="test">
          <div class="grid grid-cols-3 gap-2 mb-4 text-sm">
            <div class="p-2 bg-gray-50 rounded text-center">
              <div class="font-bold">{{ test.pass_score }}%</div>
              <div class="text-xs text-gray-400">Порог</div>
            </div>
            <div class="p-2 bg-gray-50 rounded text-center">
              <div class="font-bold">{{ test.max_attempts }}</div>
              <div class="text-xs text-gray-400">Попыток</div>
            </div>
            <div class="p-2 bg-gray-50 rounded text-center">
              <div class="font-bold">{{ test.time_limit_minutes || '∞' }}</div>
              <div class="text-xs text-gray-400">Мин</div>
            </div>
          </div>

          <div class="mb-3 flex items-center justify-between">
            <span class="text-sm font-medium">Вопросы ({{ test.questions?.length || 0 }})</span>
            <div class="flex gap-3">
              <button @click="triggerWordImport" class="text-xs text-green-600 hover:underline">&#128196; Загрузить из Word</button>
              <button @click="questionModal = true" class="text-xs text-blue-600 hover:underline">+ Добавить вопрос</button>
            </div>
          </div>
          <input ref="wordInput" type="file" accept=".docx" class="hidden" @change="importFromWord" />
          <div v-if="wordWarnings.length" class="mb-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
            <div v-for="w in wordWarnings" :key="w">⚠ {{ w }}</div>
          </div>

          <!-- Add question modal -->
          <div v-if="questionModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
            <div class="card w-full max-w-lg">
              <h2 class="font-semibold mb-4">Новый вопрос</h2>
              <div class="space-y-3">
                <div>
                  <label class="text-sm font-medium text-gray-700">Текст вопроса</label>
                  <textarea v-model="qForm.text" rows="2" class="input-field mt-1"></textarea>
                </div>
                <div v-for="(opt, i) in qForm.options" :key="i" class="flex gap-2 items-center">
                  <input v-model="opt.text" class="input-field flex-1" :placeholder="`Вариант ${i+1}`" />
                  <label class="flex items-center gap-1 text-xs">
                    <input type="checkbox" v-model="opt.is_correct" />
                    Верный
                  </label>
                </div>
                <button @click="qForm.options.push({ text: '', is_correct: false })" class="text-xs text-blue-600 hover:underline">+ Вариант</button>
              </div>
              <div class="flex gap-3 mt-4">
                <button @click="addQuestion" class="btn-primary">Добавить</button>
                <button @click="questionModal = false" class="btn-secondary">Отмена</button>
              </div>
            </div>
          </div>

          <ul class="space-y-1">
            <li v-for="(q, i) in test.questions" :key="q.id" class="text-sm p-2 bg-gray-50 rounded">
              <span class="font-medium">{{ i+1 }}. {{ q.text }}</span>
              <span class="ml-1 text-xs text-gray-400">({{ q.options?.length || 0 }} вар.)</span>
            </li>
          </ul>
        </div>
        <div v-else class="text-sm text-gray-400">Тест не создан</div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const courseId = route.params.id

const course = ref(null)
const materials = ref([])
const test = ref(null)
const materialModal = ref(false)
const questionModal = ref(false)
const matFile = ref(null)
const matFileInput = ref(null)
const wordInput = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const wordWarnings = ref([])
const matForm = ref({ title: '', material_type: 'pdf', url: '' })

const MAT_ICONS = {
  pdf: '📄', video_url: '▶️', video_file: '🎬', docx: '📊', image: '🖼️', external_link: '🔗',
}
function matIcon(t) { return MAT_ICONS[t] || '📎' }
const qForm = ref({ text: '', options: [{ text: '', is_correct: false }, { text: '', is_correct: false }, { text: '', is_correct: false }, { text: '', is_correct: true }] })

onMounted(async () => {
  const [c, m, t] = await Promise.allSettled([
    api.get(`/admin/courses/${courseId}`),
    api.get(`/admin/courses/${courseId}/materials`),
    api.get(`/admin/courses/${courseId}/test`),
  ])
  if (c.status === 'fulfilled') course.value = c.value.data
  if (m.status === 'fulfilled') materials.value = m.value.data
  if (t.status === 'fulfilled') test.value = t.value.data
})

async function uploadMaterial() {
  if (!matForm.value.title.trim()) { alert('Введите заголовок'); return }
  const needsFile = !['video_url', 'external_link'].includes(matForm.value.material_type)
  if (needsFile && !matFile.value) { alert('Выберите файл'); return }
  if (!needsFile && !matForm.value.url.trim()) { alert('Введите URL'); return }
  const fd = new FormData()
  fd.append('title', matForm.value.title)
  fd.append('material_type', matForm.value.material_type)
  if (matForm.value.url) fd.append('url', matForm.value.url)
  if (matFile.value) fd.append('file', matFile.value)
  uploading.value = true
  uploadProgress.value = 0
  try {
    await api.post(`/admin/materials/courses/${courseId}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (evt.total) uploadProgress.value = Math.round((evt.loaded / evt.total) * 100)
      }
    })
    materialModal.value = false
    matForm.value = { title: '', material_type: 'pdf', url: '' }
    matFile.value = null
    if (matFileInput.value) matFileInput.value.value = ''
    const { data } = await api.get(`/admin/courses/${courseId}/materials`)
    materials.value = data
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

async function deleteMaterial(id) {
  if (!confirm('Удалить материал?')) return
  await api.delete(`/admin/materials/${id}`)
  const { data } = await api.get(`/admin/courses/${courseId}/materials`)
  materials.value = data
}

async function createTest() {
  const { data } = await api.post(`/admin/tests/courses/${courseId}`, { pass_score: 60, max_attempts: 3 })
  test.value = data
}

function triggerWordImport() {
  wordInput.value?.click()
}

async function importFromWord(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await api.post(
      `/admin/courses/${courseId}/test/import-word`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    test.value = data.test
    wordWarnings.value = data.warnings || []
    alert(`Импортировано вопросов: ${data.imported}`)
  } catch (err) {
    alert('Ошибка импорта: ' + (err.response?.data?.detail || err.message))
  }
  e.target.value = ''
}

async function addQuestion() {
  await api.post(`/admin/tests/${test.value.id}/questions`, qForm.value)
  const { data } = await api.get(`/admin/courses/${courseId}/test`)
  test.value = data
  questionModal.value = false
  qForm.value = { text: '', options: [{ text: '', is_correct: false }, { text: '', is_correct: false }, { text: '', is_correct: false }, { text: '', is_correct: true }] }
}
</script>
