<template>
  <div>
    <div v-if="loading" class="text-gray-500">Загрузка теста...</div>

    <div v-else-if="submitted">
      <ResultPage :result="result" />
    </div>

    <div v-else>
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-xl font-bold">Тест</h1>
        <div class="flex items-center gap-4">
          <span v-if="timeLeft > 0" :class="timerColor" class="text-lg tabular-nums">⏱ {{ timerLabel }}</span>
          <span class="text-sm text-gray-500">{{ answered }} / {{ testData.total_questions }} ответов</span>
        </div>
      </div>

      <form @submit.prevent="() => submitTest(false)">
        <div
          v-for="(q, idx) in testData.questions"
          :key="q.id"
          class="card mb-4"
        >
          <p class="font-medium mb-3">{{ idx + 1 }}. {{ q.text }}</p>
          <div class="space-y-2">
            <label
              v-for="opt in q.options"
              :key="opt.id"
              class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors"
              :class="answers[q.id] === opt.id ? 'border-brand-mid bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
            >
              <input
                type="radio"
                :name="q.id"
                :value="opt.id"
                v-model="answers[q.id]"
                class="text-brand-mid"
              />
              <span class="text-sm">{{ opt.text }}</span>
            </label>
          </div>
        </div>

        <div class="card sticky bottom-4 flex items-center justify-between">
          <span class="text-sm text-gray-500">Ответили на {{ answered }} из {{ testData.total_questions }}</span>
          <button
            type="button"
            @click="() => submitTest(false)"
            :disabled="submitting"
            class="btn-primary"
          >
            {{ submitting ? 'Отправка...' : 'Завершить тест' }}
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

const toast = useToast()

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

const timerColor = computed(() => {
  if (timeLeft.value <= 60) return 'text-red-600 font-bold animate-pulse'
  if (timeLeft.value <= 180) return 'text-yellow-600 font-semibold'
  return 'text-gray-600'
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

const answered = computed(() => Object.keys(answers.value).length)

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
