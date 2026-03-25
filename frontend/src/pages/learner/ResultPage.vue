<template>
  <div class="max-w-sm mx-auto text-center py-8">
    <div class="text-6xl mb-4">{{ result?.passed ? '✅' : '❌' }}</div>
    <h2 class="text-2xl font-bold mb-2">{{ result?.passed ? 'Поздравляем!' : 'Не сдан' }}</h2>
    <p class="text-gray-500 mb-6">
      {{ result?.passed ? 'Вы успешно прошли тест.' : 'К сожалению, набранных баллов недостаточно.' }}
    </p>

    <div class="card mb-6">
      <div class="flex justify-between py-2 border-b border-gray-100">
        <span class="text-gray-600">Результат</span>
        <span class="font-semibold">{{ result?.score_percent }}%</span>
      </div>
      <div class="flex justify-between py-2 border-b border-gray-100">
        <span class="text-gray-600">Правильных ответов</span>
        <span class="font-semibold">{{ result?.score }} / {{ result?.max_score }}</span>
      </div>
      <div class="flex justify-between py-2">
        <span class="text-gray-600">Проходной балл</span>
        <span class="font-semibold">{{ result?.pass_score }}%</span>
      </div>
    </div>

    <RouterLink to="/my/courses" class="btn-primary inline-block">← К моим курсам</RouterLink>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
const props = defineProps({ result: Object })
</script>
