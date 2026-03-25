<template>
  <div>
    <div v-if="loading" class="text-gray-500">Загрузка теста...</div>

    <div v-else-if="submitted">
      <ResultPage :result="result" />
    </div>

    <div v-else>
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-xl font-bold">Тест</h1>
        <span class="text-sm text-gray-500">{{ answered }} / {{ testData.total_questions }} ответов</span>
      </div>

      <form @submit.prevent="submitTest">
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
            type="submit"
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
import { ref, computed, onMounted } from 'vue'
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

onMounted(async () => {
  // testData is passed via attempt_id — we stored it in router state
  const state = history.state
  if (state?.testData) {
    testData.value = state.testData
  } else {
    // Fallback: redirect back
    router.replace('/my/courses')
    return
  }
  loading.value = false
})

const answered = computed(() => Object.keys(answers.value).length)

async function submitTest() {
  submitting.value = true
  try {
    const payload = testData.value.questions.map(q => ({
      question_id: q.id,
      option_id: answers.value[q.id] || null,
    }))
    const { data } = await api.post(`/learner/me/tests/${route.params.attemptId}/submit`, { answers: payload })
    result.value = data
    submitted.value = true
  } finally {
    submitting.value = false
  }
}
</script>
