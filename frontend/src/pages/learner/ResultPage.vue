<template>
  <div class="max-w-lg mx-auto py-8">
    <!-- Big pass/fail banner -->
    <div
      class="rounded-2xl p-8 text-center mb-6 shadow-lg"
      :class="result?.passed ? 'bg-gradient-to-br from-green-400 to-emerald-600 text-white' : 'bg-gradient-to-br from-red-400 to-rose-600 text-white'"
    >
      <div class="text-7xl mb-4">{{ result?.passed ? '🎉' : '😔' }}</div>
      <h1 class="text-3xl font-extrabold mb-2">
        {{ result?.passed ? 'Тест сдан!' : 'Не сдан' }}
      </h1>
      <p class="text-lg opacity-90">
        {{ result?.passed ? 'Поздравляем! Курс успешно завершён.' : 'Набранных баллов недостаточно. Попробуйте ещё раз.' }}
      </p>

      <!-- Large score circle -->
      <div class="mt-6 inline-flex items-center justify-center w-28 h-28 rounded-full bg-white/20 backdrop-blur">
        <span class="text-4xl font-black">{{ result?.score_percent }}%</span>
      </div>
    </div>

    <!-- Stats card -->
    <div class="card mb-6">
      <div class="divide-y divide-gray-100">
        <div class="flex justify-between py-3 px-1">
          <span class="text-gray-500">Правильных ответов</span>
          <span class="font-semibold">{{ result?.score }} / {{ result?.max_score }}</span>
        </div>
        <div class="flex justify-between py-3 px-1">
          <span class="text-gray-500">Набрано баллов</span>
          <span
            class="font-semibold text-lg"
            :class="result?.passed ? 'text-green-600' : 'text-red-500'"
          >{{ result?.score_percent }}%</span>
        </div>
        <div class="flex justify-between py-3 px-1">
          <span class="text-gray-500">Проходной порог</span>
          <span class="font-semibold">{{ result?.pass_score }}%</span>
        </div>
        <div v-if="result?.finished_at" class="flex justify-between py-3 px-1">
          <span class="text-gray-500">Завершён</span>
          <span class="font-semibold text-sm text-gray-600">{{ formatDate(result.finished_at) }}</span>
        </div>
      </div>
    </div>

    <RouterLink to="/my/courses" class="btn-primary w-full block text-center">
      ← К моим курсам
    </RouterLink>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'

const props = defineProps({ result: Object })

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>
