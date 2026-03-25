<template>
  <div class="min-h-screen bg-white">
    <!-- Navigation -->
    <nav class="bg-white border-b border-gray-100 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <RouterLink to="/" class="flex items-center gap-2">
            <span class="text-xl font-bold text-brand-dark">Озен-Пром</span>
          </RouterLink>

          <!-- Desktop nav -->
          <div class="hidden md:flex items-center gap-6">
            <RouterLink to="/about" class="text-gray-600 hover:text-brand-mid transition-colors">О компании</RouterLink>
            <RouterLink to="/services" class="text-gray-600 hover:text-brand-mid transition-colors">Услуги</RouterLink>
            <RouterLink to="/contacts" class="text-gray-600 hover:text-brand-mid transition-colors">Контакты</RouterLink>
            <RouterLink to="/faq" class="text-gray-600 hover:text-brand-mid transition-colors">FAQ</RouterLink>
            <RouterLink to="/login" class="btn-primary">Войти в систему</RouterLink>
          </div>

          <!-- Mobile burger -->
          <button @click="menuOpen = !menuOpen" class="md:hidden p-2">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>

        <!-- Mobile menu -->
        <div v-if="menuOpen" class="md:hidden pb-4 flex flex-col gap-3">
          <RouterLink to="/about" @click="menuOpen=false" class="text-gray-700 py-2">О компании</RouterLink>
          <RouterLink to="/services" @click="menuOpen=false" class="text-gray-700 py-2">Услуги</RouterLink>
          <RouterLink to="/contacts" @click="menuOpen=false" class="text-gray-700 py-2">Контакты</RouterLink>
          <RouterLink to="/faq" @click="menuOpen=false" class="text-gray-700 py-2">FAQ</RouterLink>
          <RouterLink to="/login" class="btn-primary text-center">Войти</RouterLink>
        </div>
      </div>
    </nav>

    <main>
      <RouterView />
    </main>

    <!-- Footer -->
    <footer class="bg-brand-dark text-white mt-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 class="text-lg font-bold mb-3">Озен-Пром</h3>
            <p class="text-gray-300 text-sm">Учебный центр по охране труда и технике безопасности</p>
          </div>
          <div>
            <h4 class="font-semibold mb-3">Обучение</h4>
            <ul class="text-gray-300 text-sm space-y-1">
              <li>БиОТ — Безопасность и охрана труда</li>
              <li>ПТМ — Промышленная безопасность</li>
              <li>Промышленная безопасность</li>
            </ul>
          </div>
          <div>
            <h4 class="font-semibold mb-3">Контакты</h4>
            <p class="text-gray-300 text-sm">Казахстан</p>
          </div>
        </div>
        <div class="border-t border-gray-700 mt-8 pt-6 text-center text-gray-400 text-sm">
          © {{ new Date().getFullYear() }} Озен-Пром. Все права защищены.
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
const menuOpen = ref(false)
</script>
