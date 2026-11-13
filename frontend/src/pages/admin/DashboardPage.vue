<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="page-title">Дашборд</h1>
        <p class="page-subtitle">{{ greeting }}</p>
      </div>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      <StatTile
        v-for="(tile, i) in tiles" :key="tile.key"
        :icon="tile.icon" :tone="tile.tone" :label="tile.label"
        :value="loading ? null : tile.value"
        :style="{ animationDelay: `${i * 45}ms` }"
      />
    </div>

    <div class="card">
      <h2 class="font-semibold mb-4">Быстрые действия</h2>
      <div class="grid sm:grid-cols-3 gap-3">
        <RouterLink to="/admin/batches" class="action-card">
          <span class="action-icon action-icon--primary">
            <svg viewBox="0 0 20 20" fill="none"><path d="M3 5a2 2 0 0 1 2-2h3l1.5 2H15a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
          </span>
          <span>
            <span class="action-title">Новый поток обучения</span>
            <span class="action-hint">Загрузить сотрудников и назначить курсы</span>
          </span>
        </RouterLink>
        <RouterLink to="/admin/courses" class="action-card">
          <span class="action-icon action-icon--violet">
            <svg viewBox="0 0 20 20" fill="none"><path d="M3 5.5 10 3l7 2.5v7L10 15l-7-2.5v-7Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M3 5.5 10 8l7-2.5M10 8v7" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
          </span>
          <span>
            <span class="action-title">Управление курсами</span>
            <span class="action-hint">Материалы, тесты, дисциплины</span>
          </span>
        </RouterLink>
        <RouterLink to="/admin/exports" class="action-card">
          <span class="action-icon action-icon--teal">
            <svg viewBox="0 0 20 20" fill="none"><path d="M10 3v9m0 0-3-3m3 3 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 14v1a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </span>
          <span>
            <span class="action-title">Выгрузить отчёт</span>
            <span class="action-hint">Прогресс и результаты в Excel</span>
          </span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import StatTile from '@/components/StatTile.vue'

const toast = useToast()
const stats = ref({ users: 0, batches: 0, passed: 0, inProgress: 0, failed: 0 })
const loading = ref(true)

const fullName = localStorage.getItem('full_name') || ''
const greeting = computed(() => fullName ? `Добро пожаловать, ${fullName}` : 'Обзор системы')

const tiles = computed(() => [
  { key: 'users', icon: 'users', tone: 'primary', label: 'Пользователей', value: stats.value.users },
  { key: 'batches', icon: 'batches', tone: 'violet', label: 'Потоков', value: stats.value.batches },
  { key: 'passed', icon: 'check', tone: 'good', label: 'Сдали', value: stats.value.passed },
  { key: 'inProgress', icon: 'clock', tone: 'warning', label: 'В процессе', value: stats.value.inProgress },
  { key: 'failed', icon: 'x', tone: 'critical', label: 'Не сдали', value: stats.value.failed },
])

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/progress/stats')
    stats.value.users = data.users || 0
    stats.value.batches = data.batches || 0
    stats.value.passed = data.passed || 0
    stats.value.inProgress = data.in_progress || 0
    stats.value.failed = data.failed || 0
  } catch {
    toast.error('Не удалось загрузить статистику')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-title { font-size: 1.5rem; font-weight: 700; color: #101828; }
.page-subtitle { font-size: 0.875rem; color: #667085; margin-top: 0.1rem; }

.action-card {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.9rem;
  border: 1px solid #eef1f5;
  border-radius: 0.75rem;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}
.action-card:hover {
  border-color: #dbe6fb;
  box-shadow: 0 6px 18px -10px rgba(16,24,40,0.18);
  transform: translateY(-1px);
}
.action-icon {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.1rem;
  height: 2.1rem;
  border-radius: 0.6rem;
}
.action-icon svg { width: 18px; height: 18px; }
.action-icon--primary { background: #eff6ff; color: #2563EB; }
.action-icon--violet { background: #f5f3ff; color: #7c3aed; }
.action-icon--teal { background: #ecfdf5; color: #0d9488; }

.action-title { display: block; font-size: 0.875rem; font-weight: 600; color: #1d2939; }
.action-hint { display: block; font-size: 0.775rem; color: #98a2b3; margin-top: 0.1rem; }

@media (prefers-reduced-motion: reduce) {
  .stat-tile, .stat-skel { animation: none; }
}
</style>
