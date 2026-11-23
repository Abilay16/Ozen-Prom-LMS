<template>
  <div class="result">
    <div v-if="loading" class="panel">
      <span class="skel mx-auto" style="width: 8rem; height: 8rem; border-radius: 999px;" />
      <span class="skel mx-auto mt-4" style="width: 60%; height: 1.3rem;" />
    </div>

    <div v-else-if="!data" class="panel text-center text-gray-500">
      Результат не найден.
      <RouterLink to="/my/courses" class="block mt-2 text-sm font-medium text-blue-700">К моим курсам</RouterLink>
    </div>

    <template v-else>
      <section class="panel summary" :class="data.passed ? 'is-pass' : 'is-fail'">
        <!-- Кольцо: доля правильных ответов, отметка — проходной балл -->
        <div class="score-ring" role="img" :aria-label="`Результат ${data.score_percent}%, проходной ${data.pass_score}%`">
          <svg viewBox="0 0 120 120" class="score-ring__svg">
            <circle cx="60" cy="60" r="52" class="score-ring__track" />
            <circle
              cx="60" cy="60" r="52" class="score-ring__value"
              :style="{ strokeDasharray: `${C} ${C}`, strokeDashoffset: C * (1 - (data.score_percent || 0) / 100) }"
            />
            <line
              v-if="data.pass_score"
              x1="60" y1="2" x2="60" y2="16" class="score-ring__mark"
              :transform="`rotate(${data.pass_score * 3.6} 60 60)`"
            />
          </svg>
          <span class="score-ring__label">{{ data.score_percent }}%</span>
        </div>

        <h1 class="summary__title">
          <component :is="data.passed ? CircleCheck : CircleX" :size="24" :stroke-width="2.3" />
          {{ data.passed ? 'Тест сдан!' : 'Тест не сдан' }}
        </h1>
        <p class="summary__text">
          <template v-if="data.passed">
            Курс завершён. Удостоверение появится в разделе «Удостоверения» после подписания протокола комиссией.
          </template>
          <template v-else>
            Нужно набрать не меньше {{ data.pass_score }}%. Повторите материалы курса и попробуйте ещё раз,
            если остались попытки.
          </template>
        </p>
      </section>

      <section class="panel">
        <dl class="rows">
          <div><dt>Правильных ответов</dt><dd>{{ data.score }} из {{ data.max_score }}</dd></div>
          <div><dt>Проходной балл</dt><dd>{{ data.pass_score }}%</dd></div>
          <div v-if="data.finished_at"><dt>Завершён</dt><dd>{{ formatDate(data.finished_at) }}</dd></div>
        </dl>
      </section>

      <div class="actions">
        <RouterLink
          v-if="!data.passed && data.assignment_id"
          :to="`/my/courses/${data.assignment_id}`"
          class="btn btn--primary"
        >
          <RotateCcw :size="18" /> Вернуться к курсу
        </RouterLink>
        <RouterLink to="/my/courses" class="btn" :class="data.passed || !data.assignment_id ? 'btn--primary' : 'btn--ghost'">
          К моим курсам
        </RouterLink>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { CircleCheck, CircleX, RotateCcw } from 'lucide-vue-next'
import api from '@/services/api'

// Используется двумя способами: внутри страницы теста (результат передан
// пропсом) и по прямой ссылке /my/result/:attemptId — тогда загружаем сами
// (раньше по прямой ссылке страница показывала пустые проценты).
const props = defineProps({ result: { type: Object, default: null } })
const route = useRoute()

const C = 2 * Math.PI * 52
const data = ref(props.result)
const loading = ref(!props.result)

onMounted(async () => {
  if (data.value) return
  try {
    data.value = (await api.get(`/learner/me/tests/${route.params.attemptId}/result`)).data
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
})

function formatDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.result { max-width: 32rem; margin: 0 auto; }
.panel {
  background: #fff;
  border: 1px solid #e7e9ee;
  border-radius: 0.9rem;
  padding: 1.25rem;
  margin-bottom: 0.85rem;
}

.summary { text-align: center; padding: 1.75rem 1.25rem 1.5rem; }
.summary.is-pass { box-shadow: inset 0 3px 0 #16a34a; }
.summary.is-fail { box-shadow: inset 0 3px 0 #dc2626; }

.score-ring { position: relative; width: 8.5rem; height: 8.5rem; margin: 0 auto; }
.score-ring__svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.score-ring__track { fill: none; stroke: #eef0f4; stroke-width: 10; }
.score-ring__value {
  fill: none; stroke-width: 10; stroke-linecap: round;
  transition: stroke-dashoffset 0.9s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.is-pass .score-ring__value { stroke: #16a34a; }
.is-fail .score-ring__value { stroke: #dc2626; }
.score-ring__mark { stroke: #1f3a5c; stroke-width: 2.5; stroke-linecap: round; }
.score-ring__label {
  position: absolute; inset: 0; display: grid; place-items: center;
  font-size: 1.9rem; font-weight: 800; letter-spacing: -0.02em; color: #101828;
  font-variant-numeric: tabular-nums;
}

.summary__title {
  margin-top: 1rem;
  display: inline-flex; align-items: center; gap: 0.45rem;
  font-size: 1.45rem; font-weight: 750; letter-spacing: -0.015em;
}
.is-pass .summary__title { color: #11683f; }
.is-fail .summary__title { color: #a12a1f; }
.summary__text { margin: 0.45rem auto 0; max-width: 26rem; font-size: 0.925rem; color: #4b5565; text-wrap: pretty; }

.rows > div { display: flex; justify-content: space-between; gap: 1rem; padding: 0.6rem 0; border-bottom: 1px solid #f1f3f6; }
.rows > div:last-child { border-bottom: 0; }
.rows dt { color: #6b7280; font-size: 0.9rem; }
.rows dd { font-weight: 650; color: #101828; font-variant-numeric: tabular-nums; }

.actions { display: flex; flex-direction: column; gap: 0.5rem; }
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 0.45rem;
  padding: 0.8rem 1rem; border-radius: 0.75rem; font-weight: 650; text-decoration: none;
}
.btn--primary { background: #2563eb; color: #fff; }
.btn--primary:hover { background: #1d4ed8; }
.btn--ghost { background: #fff; border: 1px solid #d5dae3; color: #1f3a5c; }
.btn--ghost:hover { background: #f6f7f9; }
.btn:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }

@media (prefers-reduced-motion: reduce) { .score-ring__value { transition: none; } }
</style>
