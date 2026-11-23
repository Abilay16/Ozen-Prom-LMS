<template>
  <div class="h-screen flex bg-gray-50 overflow-hidden">
    <!-- Sidebar: fixed to the viewport, its own nav scrolls independently
         so the logo/footer never scroll away with the page content. -->
    <aside class="w-64 bg-brand-dark text-white shrink-0 hidden md:flex md:flex-col h-screen">
      <div class="h-16 flex items-center gap-2.5 px-5 border-b border-white/10 shrink-0">
        <span class="w-8 h-8 rounded-lg grid place-items-center bg-white/10 text-amber-400"><ShieldCheck :size="18" :stroke-width="2.2" /></span>
        <span class="font-bold text-[1.05rem] tracking-tight">Özen-Prom <span class="font-medium text-white/60">Admin</span></span>
      </div>
      <nav class="p-3 flex-1 overflow-y-auto" aria-label="Разделы админки">
        <div v-for="(group, gi) in menu" :key="gi" class="space-y-0.5" :class="{ 'mt-2 pt-2 border-t border-white/10': gi > 0 }">
          <RouterLink
            v-for="item in group" :key="item.to" :to="item.to"
            class="nav-link" :class="{ 'is-active': isActive(item.to) }"
          >
            <component :is="item.icon" :size="18" :stroke-width="1.9" class="shrink-0" />
            {{ item.label }}
          </RouterLink>
        </div>
      </nav>

      <!-- User info footer — pinned to the bottom of the sidebar via flex,
           not absolute positioning, so it never overlaps a long nav list. -->
      <div class="p-4 border-t border-white/10 shrink-0">
        <div class="text-sm text-gray-200 truncate" :title="fullName">{{ fullName }}</div>
        <div v-if="roleLabel" class="text-xs text-blue-300 mt-0.5">{{ roleLabel }}</div>
        <button @click="handleLogout" class="mt-2 inline-flex items-center gap-1.5 text-xs text-red-300 hover:text-red-100">
          <LogOut :size="14" /> Выйти
        </button>
      </div>
    </aside>

    <!-- Mobile sidebar overlay -->
    <Transition name="slide">
      <div v-if="sidebarOpen" class="fixed inset-0 z-50 md:hidden">
        <div class="absolute inset-0 bg-black/50" @click="sidebarOpen = false"/>
        <aside class="absolute left-0 top-0 bottom-0 w-72 max-w-[85vw] bg-brand-dark text-white flex flex-col">
          <div class="h-14 flex items-center justify-between px-4 border-b border-white/10">
            <span class="font-bold">Özen-Prom <span class="font-medium text-white/60">Admin</span></span>
            <button @click="sidebarOpen = false" class="w-9 h-9 grid place-items-center rounded-lg text-gray-300 hover:text-white hover:bg-white/10" aria-label="Закрыть меню">
              <X :size="20" />
            </button>
          </div>
          <nav class="p-3 flex-1 overflow-y-auto" aria-label="Разделы админки">
            <div v-for="(group, gi) in menu" :key="gi" class="space-y-0.5" :class="{ 'mt-2 pt-2 border-t border-white/10': gi > 0 }">
              <RouterLink
                v-for="item in group" :key="item.to" :to="item.to"
                class="nav-link" :class="{ 'is-active': isActive(item.to) }"
              >
                <component :is="item.icon" :size="18" :stroke-width="1.9" class="shrink-0" />
                {{ item.label }}
              </RouterLink>
            </div>
          </nav>
          <div class="p-4 border-t border-white/10">
            <div class="text-sm text-gray-200 truncate">{{ fullName }}</div>
            <div v-if="roleLabel" class="text-xs text-blue-300 mt-0.5">{{ roleLabel }}</div>
            <button @click="handleLogout" class="mt-2 inline-flex items-center gap-1.5 text-xs text-red-300 hover:text-red-100">
              <LogOut :size="14" /> Выйти
            </button>
          </div>
        </aside>
      </div>
    </Transition>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Mobile header -->
      <header class="md:hidden bg-white border-b border-gray-200 h-14 flex items-center justify-between px-2">
        <button @click="sidebarOpen = true" class="w-10 h-10 grid place-items-center rounded-lg text-gray-700 hover:bg-gray-100" aria-label="Открыть меню">
          <Menu :size="22" />
        </button>
        <span class="font-semibold text-brand-dark">Özen-Prom Admin</span>
        <button @click="handleLogout" class="w-10 h-10 grid place-items-center rounded-lg text-gray-500 hover:bg-red-50 hover:text-red-600" aria-label="Выйти">
          <LogOut :size="19" />
        </button>
      </header>

      <main class="flex-1 p-4 md:p-6 overflow-auto">
        <RouterView v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { RouterView, RouterLink, useRouter, useRoute } from 'vue-router'
import {
  Award, BookOpen, ClipboardList, Download, FolderOpen, LayoutDashboard, LogOut, Menu,
  ShieldCheck, Stethoscope, Tags, TrendingUp, UserCheck, Users, X,
} from 'lucide-vue-next'
import { useRole } from '@/composables/useRole'

const router = useRouter()
const route = useRoute()
const sidebarOpen = ref(false)
const fullName = localStorage.getItem('full_name') || ''
const { isCommission, isOrgViewer } = useRole()

// Одно меню на компьютер и телефон (раньше было продублировано в шаблоне).
const menu = computed(() => {
  const protocols = { to: '/admin/protocols', label: 'Протоколы', icon: ClipboardList }
  const certificates = { to: '/admin/certificates', label: 'Удостоверения', icon: Award }
  if (isOrgViewer) {
    return [
      [
        { to: '/admin/dashboard', label: 'Дашборд', icon: LayoutDashboard },
        { to: '/admin/batches', label: 'Потоки обучения', icon: FolderOpen },
        { to: '/admin/users', label: 'Сотрудники', icon: Users },
        { to: '/admin/progress', label: 'Прогресс', icon: TrendingUp },
      ],
      [protocols, certificates],
    ]
  }
  const signing = [protocols, { to: '/admin/commission', label: 'Комиссия', icon: UserCheck }, certificates]
  if (isCommission) return [signing]
  return [
    [
      { to: '/admin/dashboard', label: 'Дашборд', icon: LayoutDashboard },
      { to: '/admin/batches', label: 'Потоки обучения', icon: FolderOpen },
      { to: '/admin/users', label: 'Пользователи', icon: Users },
    ],
    [
      { to: '/admin/disciplines', label: 'Дисциплины', icon: Tags },
      { to: '/admin/courses', label: 'Курсы', icon: BookOpen },
    ],
    [
      { to: '/admin/progress', label: 'Прогресс', icon: TrendingUp },
      { to: '/admin/exports', label: 'Экспорт', icon: Download },
    ],
    [{ to: '/admin/med-exams', label: 'Медосмотры', icon: Stethoscope }],
    signing,
  ]
})

const roleLabel = isCommission ? 'Член комиссии' : isOrgViewer ? 'Просмотр по организации' : ''
const isActive = to => route.path.startsWith(to)

// На телефоне меню закрывается после перехода (раньше оставалось открытым
// поверх новой страницы).
watch(() => route.path, () => { sidebarOpen.value = false })

function handleLogout() {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0.75rem;
  border-radius: 0.55rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #c9d3e3;
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease, transform 0.15s ease;
}
.nav-link:hover { background: rgba(255, 255, 255, 0.06); color: #fff; transform: translateX(2px); }
.nav-link.is-active { background: rgba(255, 255, 255, 0.12); color: #fff; font-weight: 600; }
.nav-link.is-active :deep(svg) { color: #f5b544; }
.nav-link:focus-visible { outline: 2px solid #93c5fd; outline-offset: 1px; }

.slide-enter-active,
.slide-leave-active {
  transition: opacity 0.2s ease;
}
.slide-enter-active aside,
.slide-leave-active aside {
  transition: transform 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}
.slide-enter-from aside,
.slide-leave-to aside {
  transform: translateX(-100%);
}
@media (prefers-reduced-motion: reduce) {
  .nav-link:hover { transform: none; }
}
</style>
