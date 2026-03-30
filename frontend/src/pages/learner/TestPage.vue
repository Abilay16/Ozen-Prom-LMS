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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import ResultPage from './ResultPage.vue'

const route = useRoute()
const router = useRouter()

const testData = ref(null)
const loading = ref(true)
const submitting = ref(false)
const submitted = ref(false)
const result = ref(null)
const answers = ref({})

// Timer
const timeLeft = ref(0)   // seconds remaining
let timerInterval = null

function startTimer(seconds) {
  timeLeft.value = seconds
  timerInterval = setInterval(() => {
    timeLeft.value--
    sessionStorage.setItem('testEndTime_' + route.params.attemptId, Date.now() + timeLeft.value * 1000)
    if (timeLeft.value <= 0) {
      clearInterval(timerInterval)
      submitTest(true)
    }
  }, 1000)
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
    sessionStorage.setItem('testData_' + route.params.attemptId, JSON.stringify(state.testData))
  } else {
    const stored = sessionStorage.getItem('testData_' + route.params.attemptId)
    if (stored) {
      try { testData.value = JSON.parse(stored) } catch { router.replace('/my/courses'); return }
    } else {
      router.replace('/my/courses')
      return
    }
  }

  // Start timer if test has a time limit
  const limitMinutes = testData.value?.time_limit_minutes
  if (limitMinutes > 0) {
    const savedEnd = sessionStorage.getItem('testEndTime_' + route.params.attemptId)
    let remaining
    if (savedEnd) {
      remaining = Math.max(0, Math.round((Number(savedEnd) - Date.now()) / 1000))
    } else {
      remaining = limitMinutes * 60
      sessionStorage.setItem('testEndTime_' + route.params.attemptId, Date.now() + remaining * 1000)
    }
    if (remaining > 0) startTimer(remaining)
    else { router.replace('/my/courses'); return }
  }

  loading.value = false
})

onUnmounted(() => clearInterval(timerInterval))

const answered = computed(() => Object.keys(answers.value).length)

async function submitTest(isAutoSubmit = false) {
  if (submitting.value) return
  submitting.value = true
  clearInterval(timerInterval)
  sessionStorage.removeItem('testData_' + route.params.attemptId)
  sessionStorage.removeItem('testEndTime_' + route.params.attemptId)
  try {
    const payload = testData.value.questions.map(q => ({
      question_id: q.id,
      option_id: answers.value[q.id] || null,
    }))
    const { data } = await api.post(`/learner/me/tests/${route.params.attemptId}/submit`, { answers: payload })
    result.value = data
    submitted.value = true
  } catch (e) {
    if (!isAutoSubmit) alert('Ошибка: ' + (e.response?.data?.detail || e.message))
    else router.replace('/my/courses')
  } finally {
    submitting.value = false
  }
}
</script>
