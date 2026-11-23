<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200">
      <div class="max-w-4xl mx-auto px-4">

        <!-- Desktop: single row -->
        <div class="hidden sm:flex items-center justify-between h-14 gap-4">
          <span class="font-semibold text-brand-dark whitespace-nowrap">Озен-Пром LMS</span>
          <div class="flex items-center gap-4">
            <router-link to="/my/courses" class="text-sm text-gray-600 hover:text-brand-dark">Мои курсы</router-link>
            <router-link to="/my/certificates" class="text-sm text-gray-600 hover:text-brand-dark">🏅 Удостоверения</router-link>
            <span class="text-sm text-gray-500">{{ fullName }}</span>
            <button @click="handleLogout" class="text-sm text-red-500 hover:text-red-700">Выйти</button>
          </div>
        </div>

        <!-- Mobile: two rows -->
        <div class="sm:hidden">
          <!-- Row 1: logo + logout -->
          <div class="flex items-center justify-between h-12">
            <span class="font-semibold text-brand-dark">Озен-Пром LMS</span>
            <div class="flex items-center gap-2 min-w-0">
              <span class="text-xs text-gray-400 truncate max-w-[150px]">{{ fullName }}</span>
              <button @click="handleLogout" class="text-sm text-red-500 hover:text-red-700 whitespace-nowrap">Выйти</button>
            </div>
          </div>
          <!-- Row 2: nav -->
          <div class="flex items-center gap-5 pb-2.5 border-t border-gray-100 pt-2">
            <router-link
              to="/my/courses"
              class="text-sm font-medium text-gray-600 hover:text-brand-dark"
              active-class="text-brand-dark font-semibold"
            >Мои курсы</router-link>
            <router-link
              to="/my/certificates"
              class="text-sm font-medium text-gray-600 hover:text-brand-dark"
              active-class="text-brand-dark font-semibold"
            >🏅 Удостоверения</router-link>
          </div>
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
