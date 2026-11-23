<template>
  <div class="learner-shell">
    <header class="topbar">
      <div class="topbar__inner">
        <RouterLink to="/my/courses" class="brand" aria-label="На главную кабинета">
          <span class="brand__mark"><ShieldCheck :size="18" :stroke-width="2.2" /></span>
          <span class="brand__name">Özen-Prom</span>
        </RouterLink>

        <!-- Навигация: на компьютере — в шапке -->
        <nav class="topnav" aria-label="Разделы кабинета">
          <RouterLink v-for="item in nav" :key="item.to" :to="item.to" class="topnav__link" :class="{ 'is-active': isActive(item) }">
            <component :is="item.icon" :size="17" :stroke-width="2" />
            {{ item.label }}
          </RouterLink>
        </nav>

        <div class="user">
          <span class="user__avatar" :title="fullName">{{ initials }}</span>
          <span class="user__name">{{ shortName }}</span>
          <button type="button" class="user__logout" @click="handleLogout" title="Выйти" aria-label="Выйти">
            <LogOut :size="18" :stroke-width="2" />
          </button>
        </div>
      </div>
    </header>

    <main class="content" :class="{ 'content--with-tabs': showTabs }">
      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </RouterView>
    </main>

    <!-- Навигация: на телефоне — нижние вкладки. Во время теста скрыта,
         чтобы случайным касанием не уйти с теста. -->
    <nav v-if="showTabs" class="tabbar" aria-label="Разделы кабинета">
      <RouterLink v-for="item in nav" :key="item.to" :to="item.to" class="tabbar__item" :class="{ 'is-active': isActive(item) }">
        <component :is="item.icon" :size="22" :stroke-width="isActive(item) ? 2.3 : 1.9" />
        <span>{{ item.tabLabel }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { BookOpen, Award, LogOut, ShieldCheck } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const fullName = localStorage.getItem('full_name') || ''

const nav = [
  { to: '/my/courses', label: 'Мои курсы', tabLabel: 'Курсы', icon: BookOpen, match: ['/my/courses', '/my/result'] },
  { to: '/my/certificates', label: 'Удостоверения', tabLabel: 'Удостоверения', icon: Award, match: ['/my/certificates'] },
]

const isActive = item => item.match.some(p => route.path.startsWith(p))
const showTabs = computed(() => !route.path.startsWith('/my/test/'))

// «Тестов Тест Тестович» → «Тестов Т. Т.»; инициалы для кружка — «ТТ»
const parts = fullName.split(/\s+/).filter(Boolean)
const shortName = parts.length > 1 ? `${parts[0]} ${parts.slice(1).map(p => p[0] + '.').join(' ')}` : fullName
const initials = (parts[0]?.[0] || '') + (parts[1]?.[0] || '')

function handleLogout() {
  localStorage.clear()
  router.push('/login')
}
</script>

<style scoped>
.learner-shell {
  min-height: 100vh;
  background: #f6f7f9;
}

/* ── Шапка ─────────────────────────────────────────────── */
.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: saturate(160%) blur(8px);
  border-bottom: 1px solid #e7e9ee;
}
.topbar__inner {
  max-width: 56rem;
  margin: 0 auto;
  padding: 0 1rem;
  height: 3.5rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: #1f3a5c;
  text-decoration: none;
  flex-shrink: 0;
}
.brand__mark {
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.55rem;
  display: grid;
  place-items: center;
  background: #1f3a5c;
  color: #f5b544;
}
.brand__name {
  font-weight: 700;
  letter-spacing: -0.01em;
  font-size: 1rem;
}

.topnav {
  display: none;
  gap: 0.25rem;
}
.topnav__link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.75rem;
  border-radius: 0.6rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5565;
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.topnav__link:hover { background: #f1f3f6; color: #1f3a5c; }
.topnav__link.is-active { background: #eaf0f8; color: #1f3a5c; font-weight: 600; }

.user {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
}
.user__avatar {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #eaf0f8;
  color: #1f3a5c;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}
.user__name {
  display: none;
  font-size: 0.875rem;
  color: #4b5565;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 14rem;
}
.user__logout {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.6rem;
  display: grid;
  place-items: center;
  color: #6b7280;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.user__logout:hover { background: #fdecec; color: #c2410c; }
.user__logout:focus-visible, .topnav__link:focus-visible, .tabbar__item:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

/* ── Контент ───────────────────────────────────────────── */
.content {
  max-width: 56rem;
  margin: 0 auto;
  padding: 1.25rem 1rem 2.5rem;
}
.content--with-tabs {
  /* место под нижние вкладки + «чёлку» iPhone */
  padding-bottom: calc(5.5rem + env(safe-area-inset-bottom));
}

/* ── Нижние вкладки (телефон) ──────────────────────────── */
.tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 30;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: saturate(160%) blur(8px);
  border-top: 1px solid #e7e9ee;
  padding-bottom: env(safe-area-inset-bottom);
}
.tabbar__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  padding: 0.55rem 0 0.6rem;
  font-size: 0.6875rem;
  font-weight: 500;
  color: #6b7280;
  text-decoration: none;
}
.tabbar__item.is-active { color: #1f3a5c; font-weight: 600; }

@media (min-width: 640px) {
  .topnav { display: flex; }
  .user__name { display: block; }
  .tabbar { display: none; }
  .content { padding: 2rem 1.5rem 3rem; }
  .content--with-tabs { padding-bottom: 3rem; }
}
</style>
