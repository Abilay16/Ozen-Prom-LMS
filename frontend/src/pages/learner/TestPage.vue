<template>
  <div>
    <div v-if="loading" class="space-y-3">
      <span class="skel" style="width: 100%; height: 3rem; border-radius: 0.75rem;" />
      <span class="skel" style="width: 100%; height: 10rem; border-radius: 0.9rem;" />
    </div>

    <div v-else-if="submitted">
      <ResultPage :result="result" />
    </div>

    <div v-else>
      <!-- Закреплённая полоса: прогресс и таймер всегда на виду -->
      <div class="test-bar">
        <div class="test-bar__row">
          <span class="test-bar__count">{{ answered }} / {{ total }} ответов</span>
          <span v-if="timeLeft > 0" class="timer" :class="timerClass" role="timer" :aria-label="`Осталось ${timerLabel}`">
            <Timer :size="16" :stroke-width="2.2" /> {{ timerLabel }}
          </span>
        </div>
        <div class="progress" role="progressbar" :aria-valuenow="answered" aria-valuemin="0" :aria-valuemax="total">
          <span class="progress__fill" :style="{ width: total ? `${(answered / total) * 100}%` : '0%' }" />
        </div>
      </div>

      <form @submit.prevent="requestSubmit">
        <div
          v-for="(q, idx) in testData.questions"
          :key="q.id"
          :id="`q-${q.id}`"
          class="question"
          :class="{ 'question--missed': showMissed && !answers[q.id] }"
          role="radiogroup"
          :aria-labelledby="`q-title-${q.id}`"
        >
          <div class="question__head">
            <span class="question__num">Вопрос {{ idx + 1 }} из {{ total }}</span>
            <span :id="`q-title-${q.id}`" class="question__text">{{ q.text }}</span>
          </div>
          <div class="options">
            <label
              v-for="opt in q.options"
              :key="opt.id"
              class="option"
              :class="{ 'is-selected': answers[q.id] === opt.id }"
            >
              <input v-model="answers[q.id]" type="radio" :name="q.id" :value="opt.id" class="option__input" />
              <span class="option__dot" aria-hidden="true" />
              <span class="option__text">{{ opt.text }}</span>
            </label>
          </div>
        </div>

        <div class="submit-bar">
          <span class="submit-bar__hint">
            <template v-if="unanswered.length">Без ответа: {{ unanswered.length }}</template>
            <template v-else>Все вопросы отвечены</template>
          </span>
          <button type="submit" :disabled="submitting" class="submit-bar__btn">
            <Loader2 v-if="submitting" :size="18" class="animate-spin" />
            {{ submitting ? 'Отправляем…' : 'Завершить тест' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import ResultPage from './ResultPage.vue'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { Loader2, Timer } from 'lucide-vue-next'

const toast = useToast()
const { confirm } = useConfirm()
const showMissed = ref(false)

const route = useRoute()
const router = useRouter()

const testData = ref(null)
const loading = ref(true)
const submitting = ref(false)
const submitted = ref(false)
const result = ref(null)
const answers = ref({})

const KEY_DATA = 'testData_' + route.params.attemptId
const KEY_END = 'testEndTime_' + route.params.attemptId
const KEY_ANSWERS = 'testAnswers_' + route.params.attemptId

// Timer. Оставшееся время всегда считаем от фиксированного момента окончания:
// в фоновой вкладке/на заблокированном телефоне setInterval срабатывает реже,
// и счётчик «минус секунда за тик» отставал от реального времени (а сервер
// проверяет лимит по своим часам).
const timeLeft = ref(0)   // seconds remaining
let timerInterval = null

function startTimer(endTime) {
  const tick = () => {
    timeLeft.value = Math.max(0, Math.ceil((endTime - Date.now()) / 1000))
    if (timeLeft.value <= 0) {
      clearInterval(timerInterval)
      submitTest(true)
    }
  }
  tick()
  timerInterval = setInterval(tick, 1000)
}

const timerLabel = computed(() => {
  if (!timeLeft.value) return ''
  const m = Math.floor(timeLeft.value / 60)
  const s = timeLeft.value % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const timerClass = computed(() => {
  if (timeLeft.value <= 60) return 'timer--danger'
  if (timeLeft.value <= 180) return 'timer--warn'
  return ''
})

onMounted(async () => {
  // testData is passed via router state; sessionStorage is the F5 fallback
  const state = history.state
  if (state?.testData) {
    testData.value = state.testData
    sessionStorage.setItem(KEY_DATA, JSON.stringify(state.testData))
  } else {
    const stored = sessionStorage.getItem(KEY_DATA)
    if (stored) {
      try { testData.value = JSON.parse(stored) } catch { router.replace('/my/courses'); return }
    } else {
      router.replace('/my/courses')
      return
    }
  }

  // Ответы переживают перезагрузку страницы (раньше F5 стирал все выбранные ответы).
  try { answers.value = JSON.parse(sessionStorage.getItem(KEY_ANSWERS) || '{}') } catch { answers.value = {} }

  loading.value = false

  // Start timer if test has a time limit
  const limitMinutes = testData.value?.time_limit_minutes
  if (limitMinutes > 0) {
    let endTime = Number(sessionStorage.getItem(KEY_END))
    if (!endTime) {
      endTime = Date.now() + limitMinutes * 60 * 1000
      sessionStorage.setItem(KEY_END, String(endTime))
    }
    // Если время вышло, пока страница была закрыта, — сдаём то, что есть,
    // а не бросаем попытку незавершённой (она бы навсегда осталась «в процессе»).
    startTimer(endTime)
  }
})

onUnmounted(() => clearInterval(timerInterval))

watch(answers, val => {
  try { sessionStorage.setItem(KEY_ANSWERS, JSON.stringify(val)) } catch {}
}, { deep: true })

const total = computed(() => testData.value?.questions?.length || 0)
const answered = computed(() => (testData.value?.questions || []).filter(q => answers.value[q.id]).length)
const unanswered = computed(() =>
  (testData.value?.questions || []).map((q, i) => ({ id: q.id, n: i + 1 })).filter(q => !answers.value[q.id]),
)

// Сдача вручную: если есть вопросы без ответа — показываем какие и спрашиваем.
async function requestSubmit() {
  if (submitting.value) return
  if (unanswered.value.length) {
    showMissed.value = true
    const nums = unanswered.value.map(q => q.n)
    const list = nums.length > 6 ? `${nums.slice(0, 6).join(', ')} и ещё ${nums.length - 6}` : nums.join(', ')
    const ok = await confirm({
      message: `Нет ответа на ${nums.length === 1 ? 'вопрос' : 'вопросы'} № ${list}. Они будут засчитаны как неверные. Завершить тест?`,
      confirmText: 'Завершить',
      cancelText: 'Вернуться к вопросам',
    })
    if (!ok) {
      document.getElementById(`q-${unanswered.value[0].id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      return
    }
  }
  submitTest(false)
}

async function submitTest(isAutoSubmit = false) {
  if (submitting.value) return
  submitting.value = true
  clearInterval(timerInterval)
  try {
    const payload = testData.value.questions.map(q => ({
      question_id: q.id,
      option_id: answers.value[q.id] || null,
    }))
    const { data } = await api.post(`/learner/me/tests/${route.params.attemptId}/submit`, { answers: payload })
    result.value = data
    submitted.value = true
    // Чистим черновик только после успешной сдачи: если сеть упала,
    // ответы и таймер останутся и можно повторить отправку.
    for (const k of [KEY_DATA, KEY_END, KEY_ANSWERS]) sessionStorage.removeItem(k)
  } catch (e) {
    if (!isAutoSubmit) toast.error(apiErrorMessage(e))
    else router.replace('/my/courses')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.test-bar {
  position: sticky;
  top: 3.5rem; /* под шапкой кабинета */
  z-index: 20;
  margin: -1.25rem -1rem 1rem;
  padding: 0.7rem 1rem 0.6rem;
  background: rgba(246, 247, 249, 0.95);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid #e7e9ee;
}
@media (min-width: 640px) { .test-bar { margin: -2rem -1.5rem 1.25rem; padding: 0.8rem 1.5rem 0.7rem; } }
.test-bar__row { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.test-bar__count { font-size: 0.875rem; font-weight: 600; color: #1f3a5c; font-variant-numeric: tabular-nums; }
.timer {
  display: inline-flex; align-items: center; gap: 0.35rem;
  font-size: 0.95rem; font-weight: 700; font-variant-numeric: tabular-nums;
  padding: 0.2rem 0.6rem; border-radius: 999px; background: #eef3fb; color: #1f3a5c;
}
.timer--warn { background: #fff4e0; color: #9a5b00; }
.timer--danger { background: #fdecec; color: #b42318; animation: pulse 1.2s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: 0.6; } }
.progress { margin-top: 0.55rem; height: 4px; border-radius: 999px; background: #e3e7ee; overflow: hidden; }
.progress__fill { display: block; height: 100%; background: #2563eb; border-radius: inherit; transition: width 0.25s ease; }

.question {
  background: #fff; border: 1px solid #e7e9ee; border-radius: 0.9rem;
  padding: 1rem 1rem 1.05rem; margin: 0 0 0.75rem; min-width: 0;
  scroll-margin-top: 7rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
@media (min-width: 640px) { .question { padding: 1.25rem 1.4rem; } }
.question--missed { border-color: #f4b4ad; box-shadow: inset 3px 0 0 #e5484d; }
.question__head { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.8rem; padding: 0; }
.question__num { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: #8a93a3; }
.question__text { font-size: 1rem; font-weight: 600; line-height: 1.45; color: #101828; text-wrap: pretty; }

.options { display: flex; flex-direction: column; gap: 0.5rem; }
.option {
  position: relative; display: flex; align-items: flex-start; gap: 0.75rem;
  padding: 0.8rem 0.9rem; min-height: 3rem;
  border: 1.5px solid #e3e7ee; border-radius: 0.7rem; cursor: pointer;
  transition: border-color 0.12s ease, background-color 0.12s ease;
}
.option:hover { border-color: #c9d3e3; }
.option.is-selected { border-color: #2563eb; background: #eff5ff; }
.option__input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.option__dot {
  width: 1.15rem; height: 1.15rem; margin-top: 0.1rem; flex-shrink: 0;
  border-radius: 999px; border: 2px solid #b4bccb; background: #fff;
  transition: border-color 0.12s ease, box-shadow 0.12s ease;
}
.option.is-selected .option__dot { border-color: #2563eb; box-shadow: inset 0 0 0 3px #fff, inset 0 0 0 10px #2563eb; }
.option:has(.option__input:focus-visible) { outline: 2px solid #2563eb; outline-offset: 2px; }
.option__text { font-size: 0.95rem; line-height: 1.45; color: #1f2937; }

.submit-bar {
  position: sticky; bottom: 0; z-index: 20;
  margin: 1rem -1rem 0; padding: 0.75rem 1rem calc(0.75rem + env(safe-area-inset-bottom));
  display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
  background: rgba(255, 255, 255, 0.96); backdrop-filter: blur(6px);
  border-top: 1px solid #e7e9ee;
}
@media (min-width: 640px) {
  .submit-bar { margin: 1rem 0 0; bottom: 1rem; border: 1px solid #e7e9ee; border-radius: 0.9rem; padding: 0.75rem 1rem; box-shadow: 0 8px 24px -14px rgba(16, 24, 40, 0.35); }
}
.submit-bar__hint { font-size: 0.85rem; color: #6b7280; }
.submit-bar__btn {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.75rem 1.25rem; border-radius: 0.7rem;
  background: #2563eb; color: #fff; font-weight: 650; white-space: nowrap;
}
.submit-bar__btn:hover:not(:disabled) { background: #1d4ed8; }
.submit-bar__btn:disabled { opacity: 0.6; }
.submit-bar__btn:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }
</style>
