<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200">
      <div class="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <span class="font-semibold text-brand-dark">Озен-Пром LMS</span>
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-600">{{ fullName }}</span>
          <button @click="handleLogout" class="text-sm text-red-500 hover:text-red-700">Выйти</button>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
const fullName = localStorage.getItem('full_name') || ''

function handleLogout() {
  localStorage.clear()
  router.push('/login')
}
</script>
