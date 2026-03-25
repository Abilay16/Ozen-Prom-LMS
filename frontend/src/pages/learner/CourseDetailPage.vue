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
      <ul class="space-y-3">
        <li v-for="mat in assignment.course?.materials" :key="mat.id" class="flex items-center gap-3">
          <span class="text-xl">{{ materialIcon(mat.material_type) }}</span>
          <div class="flex-1">
            <div class="font-medium text-sm">{{ mat.title }}</div>
            <div class="text-xs text-gray-400">{{ mat.material_type }}</div>
          </div>
          <a
            v-if="mat.file_path"
            :href="`/api/v1/learner/materials/${mat.id}/download`"
            class="text-sm text-brand-mid hover:underline"
          >Скачать</a>
          <a v-else-if="mat.url" :href="mat.url" target="_blank" class="text-sm text-brand-mid hover:underline">Открыть</a>
        </li>
      </ul>
    </div>

    <!-- Test section -->
    <div class="card">
      <h2 class="font-semibold text-lg mb-2">Тест</h2>
      <div v-if="assignment.status === 'passed'" class="text-green-600 font-medium mb-4">✓ Тест пройден</div>
      <div v-else-if="assignment.status === 'failed'" class="text-red-500 font-medium mb-4">Попытки исчерпаны</div>
      <div v-else>
        <p class="text-sm text-gray-600 mb-4">После изучения материалов пройдите тест для завершения курса.</p>
        <button @click="startTest" :disabled="starting" class="btn-primary">
          {{ starting ? 'Запуск...' : 'Начать тест' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()
const assignment = ref(null)
const loading = ref(true)
const starting = ref(false)

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
    router.push(`/my/test/${data.attempt_id}`)
  } finally {
    starting.value = false
  }
}

function materialIcon(type) {
  const icons = { video_file: '🎬', video_url: '▶️', pdf: '📄', docx: '📝', image: '🖼️', external_link: '🔗' }
  return icons[type] || '📎'
}
function statusBadge(s) {
  return { assigned: 'badge-assigned', in_progress: 'badge-progress', passed: 'badge-passed', failed: 'badge-failed' }[s] || 'badge-assigned'
}
function statusLabel(s) {
  return { assigned: 'Назначен', in_progress: 'В процессе', passed: 'Сдан ✓', failed: 'Не сдан' }[s] || s
}
</script>
