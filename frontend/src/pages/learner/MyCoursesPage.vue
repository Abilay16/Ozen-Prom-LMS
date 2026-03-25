<template>
  <div>
    <h1 class="text-2xl font-bold mb-6">Мои курсы</h1>

    <div v-if="loading" class="text-gray-500">Загрузка...</div>

    <div v-else-if="courses.length === 0" class="card text-center py-12 text-gray-400">
      Курсы не назначены
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="assignment in courses"
        :key="assignment.id"
        class="card hover:shadow-md transition-shadow"
      >
        <div class="flex items-start justify-between mb-3">
          <span :class="statusBadge(assignment.status)">{{ statusLabel(assignment.status) }}</span>
          <span class="text-xs text-gray-400">{{ assignment.discipline?.name }}</span>
        </div>
        <h3 class="font-semibold text-gray-900 mb-1">{{ assignment.course?.name }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ assignment.course?.description }}</p>
        <RouterLink
          :to="`/my/courses/${assignment.id}`"
          class="btn-primary text-sm inline-block"
        >
          Перейти к курсу →
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'

const courses = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/learner/me/courses')
    courses.value = data
  } finally {
    loading.value = false
  }
})

function statusBadge(status) {
  const map = {
    assigned: 'badge-assigned',
    in_progress: 'badge-progress',
    passed: 'badge-passed',
    failed: 'badge-failed',
  }
  return map[status] || 'badge-assigned'
}

function statusLabel(status) {
  const map = {
    assigned: 'Назначен',
    in_progress: 'В процессе',
    passed: 'Сдан ✓',
    failed: 'Не сдан',
  }
  return map[status] || status
}
</script>
