<template>
  <div>
    <header class="page-head">
      <h1 class="page-title">Мои курсы</h1>
      <p v-if="!loading && courses.length" class="page-sub">
        <template v-if="todoCount">Осталось пройти: <strong>{{ todoCount }}</strong> из {{ courses.length }}</template>
        <template v-else>Все курсы пройдены — удостоверения появятся после подписания протокола комиссией.</template>
      </p>
    </header>

    <!-- Загрузка -->
    <div v-if="loading" class="grid gap-3 sm:grid-cols-2">
      <div v-for="i in 2" :key="i" class="course-card">
        <span class="skel" style="width: 5.5rem; height: 1.25rem; border-radius: 999px;" />
        <span class="skel mt-4" style="width: 70%; height: 1.1rem;" />
        <span class="skel mt-2" style="width: 45%; height: 0.85rem;" />
        <span class="skel mt-5" style="width: 100%; height: 2.6rem; border-radius: 0.65rem;" />
      </div>
    </div>

    <!-- Пусто -->
    <div v-else-if="!courses.length" class="empty">
      <BookOpen :size="28" :stroke-width="1.6" class="empty__icon" />
      <p class="empty__title">Курсы пока не назначены</p>
      <p class="empty__text">Когда администратор добавит вас в поток обучения, курсы появятся здесь.</p>
    </div>

    <!-- Список -->
    <div v-else class="grid gap-3 sm:grid-cols-2">
      <RouterLink
        v-for="a in sortedCourses"
        :key="a.id"
        :to="`/my/courses/${a.id}`"
        class="course-card course-card--link"
        :class="`is-${a.status}`"
      >
        <div class="flex items-center justify-between gap-3">
          <span class="status" :class="`status--${a.status}`">
            <component :is="STATUS[a.status]?.icon || Circle" :size="14" :stroke-width="2.4" />
            {{ STATUS[a.status]?.label || a.status }}
          </span>
          <span class="discipline">{{ a.discipline?.name }}</span>
        </div>

        <h2 class="course-name">{{ a.course?.name }}</h2>
        <p v-if="a.course?.description" class="course-desc">{{ a.course.description }}</p>

        <div class="course-foot">
          <span v-if="bestScore(a) !== null" class="score">
            Лучший результат:
            <strong :class="a.status === 'passed' ? 'text-emerald-700' : 'text-gray-900'">{{ bestScore(a) }}%</strong>
          </span>
          <span v-else class="score">Тест ещё не проходили</span>
          <span class="cta" :class="{ 'cta--quiet': a.status === 'passed' || a.status === 'failed' }">
            {{ STATUS[a.status]?.cta || 'Открыть' }}
            <ChevronRight :size="16" :stroke-width="2.4" />
          </span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { BookOpen, ChevronRight, Circle, CircleCheck, CircleX, Clock } from 'lucide-vue-next'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'

const toast = useToast()
const courses = ref([])
const loading = ref(true)

const STATUS = {
  assigned: { label: 'Назначен', icon: Circle, cta: 'Начать', order: 1 },
  in_progress: { label: 'В процессе', icon: Clock, cta: 'Продолжить', order: 0 },
  failed: { label: 'Не сдан', icon: CircleX, cta: 'Подробнее', order: 2 },
  passed: { label: 'Сдан', icon: CircleCheck, cta: 'Открыть', order: 3 },
}

// Сначала то, что нужно сделать: в процессе → назначенные → не сданные → сданные.
const sortedCourses = computed(() =>
  [...courses.value].sort((a, b) => (STATUS[a.status]?.order ?? 9) - (STATUS[b.status]?.order ?? 9)),
)
const todoCount = computed(() => courses.value.filter(a => a.status === 'assigned' || a.status === 'in_progress').length)

onMounted(async () => {
  try {
    courses.value = (await api.get('/learner/me/courses')).data
  } catch (e) {
    toast.error(apiErrorMessage(e))
  } finally {
    loading.value = false
  }
})

function bestScore(a) {
  const scores = (a.attempts || []).map(x => x.score_percent).filter(s => s !== null && s !== undefined)
  return scores.length ? Math.max(...scores) : null
}
</script>

<style scoped>
.page-head { margin-bottom: 1.25rem; }
.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.015em;
  color: #101828;
}
.page-sub { margin-top: 0.3rem; font-size: 0.9rem; color: #5b6475; text-wrap: pretty; }

.course-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #e7e9ee;
  border-radius: 0.9rem;
  padding: 1.1rem 1.15rem 1rem;
  text-decoration: none;
  color: inherit;
}
.course-card--link {
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}
.course-card--link:hover {
  border-color: #c9d3e3;
  box-shadow: 0 6px 18px -10px rgba(31, 58, 92, 0.35);
  transform: translateY(-1px);
}
.course-card--link:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }
/* Требующие действия — с синей полосой слева, чтобы читались первыми. */
.course-card.is-assigned, .course-card.is-in_progress { box-shadow: inset 3px 0 0 #2563eb; }

.status {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem 0.2rem 0.45rem;
  border-radius: 999px;
}
.status--assigned { background: #eef3fb; color: #1f4f96; }
.status--in_progress { background: #fff4e0; color: #9a5b00; }
.status--passed { background: #e7f6ee; color: #11683f; }
.status--failed { background: #fdecec; color: #a12a1f; }

.discipline {
  font-size: 0.75rem;
  color: #8a93a3;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.course-name {
  margin-top: 0.8rem;
  font-size: 1.05rem;
  font-weight: 650;
  line-height: 1.35;
  color: #101828;
  text-wrap: balance;
}
.course-desc {
  margin-top: 0.25rem;
  font-size: 0.85rem;
  color: #5b6475;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.course-foot {
  margin-top: auto;
  padding-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.score { font-size: 0.8rem; color: #6b7280; }
.score strong { font-variant-numeric: tabular-nums; }
.cta {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  padding: 0.5rem 0.75rem 0.5rem 0.9rem;
  border-radius: 0.65rem;
  background: #2563eb;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}
.cta--quiet { background: #f1f3f6; color: #1f3a5c; }

.empty {
  background: #fff;
  border: 1px dashed #d5dae3;
  border-radius: 0.9rem;
  padding: 2.5rem 1.25rem;
  text-align: center;
}
.empty__icon { margin: 0 auto 0.75rem; color: #8a93a3; }
.empty__title { font-weight: 600; color: #101828; }
.empty__text { margin-top: 0.3rem; font-size: 0.875rem; color: #6b7280; max-width: 26rem; margin-inline: auto; }
</style>
