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
      <div class="space-y-4">
        <div v-for="mat in assignment.course?.materials" :key="mat.id">
          <!-- Video embed for YouTube/Vimeo -->
          <div v-if="mat.material_type === 'video_url' && mat.url">
            <div class="font-medium text-sm mb-2">{{ materialIcon(mat.material_type) }} {{ mat.title }}</div>
            <div v-if="youtubeId(mat.url)" class="aspect-video rounded overflow-hidden bg-black">
              <iframe
                :src="`https://www.youtube.com/embed/${youtubeId(mat.url)}`"
                class="w-full h-full"
                frameborder="0"
                allowfullscreen
              ></iframe>
            </div>
            <a v-else :href="mat.url" target="_blank" class="text-sm text-brand-mid hover:underline">Открыть видео ↗</a>
          </div>
          <!-- External link -->
          <div v-else-if="mat.material_type === 'external_link' && mat.url" class="flex items-center gap-3">
            <span class="text-xl">{{ materialIcon(mat.material_type) }}</span>
            <div class="flex-1">
              <div class="font-medium text-sm">{{ mat.title }}</div>
            </div>
            <a :href="mat.url" target="_blank" class="text-sm text-brand-mid hover:underline">Открыть ↗</a>
          </div>
          <!-- Downloadable file -->
          <div v-else class="flex items-center gap-3">
            <span class="text-xl">{{ materialIcon(mat.material_type) }}</span>
            <div class="flex-1">
              <div class="font-medium text-sm">{{ mat.title }}</div>
              <div class="text-xs text-gray-400">{{ mat.material_type }}</div>
            </div>
            <a
              v-if="mat.file_path"
              href="#"
              @click.prevent="downloadMaterial(mat)"
              class="text-sm text-brand-mid hover:underline"
            >Скачать</a>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const assignment = ref(null)
const loading = ref(true)
const starting = ref(false)

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
})

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

function youtubeId(url) {
  if (!url) return null
  // Handles youtube.com/watch?v=ID, youtu.be/ID, youtube.com/embed/ID
  const m = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/)
  return m ? m[1] : null
}

async function downloadMaterial(mat) {
  try {
    const { data, headers } = await api.get(`/learner/materials/${mat.id}/download`, { responseType: 'blob' })
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
