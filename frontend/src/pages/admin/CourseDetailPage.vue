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
                  <option value="pdf">PDF</option>
                  <option value="video">Видео (URL)</option>
                  <option value="presentation">Презентация</option>
                  <option value="other">Прочее</option>
                </select>
              </div>
              <div v-if="matForm.material_type === 'video'">
                <label class="text-sm font-medium text-gray-700">URL видео</label>
                <input v-model="matForm.url" class="input-field mt-1" placeholder="https://..." />
              </div>
              <div v-else>
                <label class="text-sm font-medium text-gray-700">Файл</label>
                <input ref="matFileInput" type="file" @change="e => matFile = e.target.files[0]" class="input-field mt-1" />
              </div>
            </div>
            <div class="flex gap-3 mt-4">
              <button @click="uploadMaterial" class="btn-primary">Загрузить</button>
              <button @click="materialModal = false" class="btn-secondary">Отмена</button>
            </div>
          </div>
        </div>

        <ul class="space-y-2">
          <li v-for="m in materials" :key="m.id" class="flex items-center justify-between p-2 rounded bg-gray-50">
            <div>
              <span class="font-medium text-sm">{{ m.title }}</span>
              <span class="ml-2 text-xs text-gray-400">{{ m.material_type }}</span>
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
const wordInput = ref(null)
const wordWarnings = ref([])
const matForm = ref({ title: '', material_type: 'pdf', url: '' })
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
  const fd = new FormData()
  fd.append('title', matForm.value.title)
  fd.append('material_type', matForm.value.material_type)
  if (matForm.value.url) fd.append('url', matForm.value.url)
  if (matFile.value) fd.append('file', matFile.value)
  await api.post(`/admin/materials/courses/${courseId}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  materialModal.value = false
  const { data } = await api.get(`/admin/courses/${courseId}/materials`)
  materials.value = data
}

async function deleteMaterial(id) {
  if (!confirm('Удалить материал?')) return
  await api.delete(`/admin/materials/${id}`)
  const { data } = await api.get(`/admin/courses/${courseId}/materials`)
  materials.value = data
}

async function createTest() {
  const { data } = await api.post(`/admin/tests/courses/${courseId}`, { pass_score: 70, max_attempts: 3 })
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
