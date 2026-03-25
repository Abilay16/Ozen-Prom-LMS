<template>
  <div class="min-h-screen flex items-center justify-center bg-brand-light">
    <div class="text-center p-8">
      <div class="text-8xl font-bold text-brand-mid mb-4">404</div>
      <h1 class="text-2xl font-semibold mb-2">Страница не найдена</h1>
      <p class="text-gray-500 mb-6">Запрошенная страница не существует или была перемещена.</p>
      <RouterLink to="/" class="btn-primary inline-block">На главную</RouterLink>
    </div>
  </div>
</template>
<script setup>
import { RouterLink } from 'vue-router'
</script>
