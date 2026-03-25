<template>
  <div class="min-h-screen flex bg-gray-50">
    <!-- Sidebar -->
    <aside class="w-64 bg-brand-dark text-white flex-shrink-0 hidden md:block">
      <div class="h-16 flex items-center px-6 border-b border-white/10">
        <span class="font-bold text-lg">Озен-Пром Admin</span>
      </div>
      <nav class="p-4 space-y-1">
        <NavLink to="/admin/dashboard" icon="📊">Дашборд</NavLink>
        <NavLink to="/admin/batches" icon="📂">Потоки обучения</NavLink>
        <NavLink to="/admin/users" icon="👥">Пользователи</NavLink>
        <NavLink to="/admin/organizations" icon="🏢">Организации</NavLink>
        <div class="border-t border-white/10 my-2"/>
        <NavLink to="/admin/courses" icon="📚">Курсы</NavLink>
        <NavLink to="/admin/disciplines" icon="🏷️">Дисциплины</NavLink>
        <NavLink to="/admin/positions" icon="👷">Должности</NavLink>
        <NavLink to="/admin/rules" icon="⚙️">Правила назначений</NavLink>
        <div class="border-t border-white/10 my-2"/>
        <NavLink to="/admin/progress" icon="📈">Прогресс</NavLink>
        <NavLink to="/admin/exports" icon="⬇️">Экспорт</NavLink>
      </nav>

      <!-- User info at bottom -->
      <div class="absolute bottom-0 w-64 p-4 border-t border-white/10">
        <div class="text-sm text-gray-300">{{ auth.fullName }}</div>
        <button @click="handleLogout" class="text-xs text-red-300 hover:text-red-100 mt-1">Выйти</button>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Mobile header -->
      <header class="md:hidden bg-white border-b border-gray-200 h-14 flex items-center justify-between px-4">
        <button @click="sidebarOpen = !sidebarOpen" class="p-2">☰</button>
        <span class="font-semibold">Озен-Пром Admin</span>
        <button @click="handleLogout" class="text-sm text-red-500">Выйти</button>
      </header>

      <main class="flex-1 p-6 overflow-auto">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterView, RouterLink, useLink, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const sidebarOpen = ref(false)

function handleLogout() {
  auth.logout()
  router.push('/login')
}

// NavLink helper component (inline)
const NavLink = {
  props: ['to', 'icon'],
  template: `
    <RouterLink :to="to"
      class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
      :class="$route.path.startsWith(to) ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'"
    >
      <span>{{ icon }}</span>
      <slot />
    </RouterLink>
  `,
  components: { RouterLink },
}
</script>
