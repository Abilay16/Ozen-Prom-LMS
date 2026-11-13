<template>
  <div class="login-screen">
    <!-- Brand panel -->
    <aside class="brand-panel">
      <div class="brand-pattern" aria-hidden="true"></div>
      <div class="brand-content">
        <div class="brand-mark">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M24 3 L43 10 V23 C43 34 35 41.5 24 45 C13 41.5 5 34 5 23 V10 Z"
                  fill="rgba(255,255,255,0.08)" stroke="#F59E0B" stroke-width="1.6" />
            <path d="M16 24.5 L21.5 30 L33 17.5" stroke="#F59E0B" stroke-width="2.4"
                  stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h1 class="brand-title">Özen&#8209;Prom</h1>
        <p class="brand-subtitle">Учебный центр по охране труда и промышленной безопасности</p>

        <ul class="brand-facts">
          <li>
            <span class="fact-dot"></span>
            Удостоверения подписываются ЭЦП через НУЦ РК
          </li>
          <li>
            <span class="fact-dot"></span>
            Проверка допусков работника по одному QR-коду
          </li>
          <li>
            <span class="fact-dot"></span>
            БиОТ · ПТМ · Промышленная безопасность
          </li>
        </ul>
      </div>
    </aside>

    <!-- Form panel -->
    <main class="form-panel">
      <div class="form-card" :class="{ 'shake': shake }">
        <h2 class="form-title">Вход в систему</h2>
        <p class="form-hint">Введите данные вашей учётной записи</p>

        <form @submit.prevent="handleLogin" class="mt-6 space-y-4" novalidate>
          <div class="field">
            <label for="login" class="field-label">Логин</label>
            <div class="field-control">
              <svg class="field-icon" viewBox="0 0 20 20" fill="none"><path d="M10 10a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm0 2c-3.3 0-7 1.7-7 4v1h14v-1c0-2.3-3.7-4-7-4Z" fill="currentColor"/></svg>
              <input
                id="login"
                v-model="form.login"
                type="text"
                placeholder="Введите логин"
                autocomplete="username"
                required
                autofocus
              />
            </div>
          </div>

          <div class="field">
            <label for="password" class="field-label">Пароль</label>
            <div class="field-control">
              <svg class="field-icon" viewBox="0 0 20 20" fill="none"><path d="M5 9V7a5 5 0 0 1 10 0v2h.5A1.5 1.5 0 0 1 17 10.5v6A1.5 1.5 0 0 1 15.5 18h-11A1.5 1.5 0 0 1 3 16.5v-6A1.5 1.5 0 0 1 4.5 9H5Zm2 0h6V7a3 3 0 0 0-6 0v2Z" fill="currentColor"/></svg>
              <input
                id="password"
                v-model="form.password"
                type="password"
                placeholder="Введите пароль"
                autocomplete="current-password"
                required
              />
            </div>
          </div>

          <Transition name="fade-slide">
            <div v-if="error" class="error-banner">
              <svg viewBox="0 0 20 20" fill="none" class="shrink-0"><path d="M10 2 1 18h18L10 2Zm0 5.5a1 1 0 0 1 1 1v4a1 1 0 1 1-2 0v-4a1 1 0 0 1 1-1Zm0 8a1.1 1.1 0 1 1 0-2.2 1.1 1.1 0 0 1 0 2.2Z" fill="currentColor"/></svg>
              {{ error }}
            </div>
          </Transition>

          <button type="submit" :disabled="loading" class="submit-btn">
            <svg v-if="loading" class="spinner" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2.5" stroke-opacity="0.25"/>
              <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <span>{{ loading ? 'Входим…' : 'Войти' }}</span>
          </button>
        </form>

        <RouterLink to="/" class="back-link">
          <svg viewBox="0 0 20 20" fill="none"><path d="M12.5 4 6.5 10l6 6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
          На главную
        </RouterLink>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ login: '', password: '' })
const loading = ref(false)
const error = ref('')
const shake = ref(false)

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    const data = await auth.login(form.value.login, form.value.password)
    // Use a full page reload so the browser always loads the latest JS bundles.
    // SPA navigation (router.push) can serve stale cached modules.
    if (data.role === 'admin') {
      window.location.href = data.is_commission ? '/admin/protocols' : '/admin/dashboard'
    } else {
      window.location.href = '/my/courses'
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Неверный логин или пароль'
    shake.value = true
    setTimeout(() => { shake.value = false }, 420)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-screen {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr;
}

@media (min-width: 900px) {
  .login-screen { grid-template-columns: minmax(320px, 42%) 1fr; }
}

/* ── Brand panel ─────────────────────────────────────────────── */
.brand-panel {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  padding: 3rem 2.5rem;
  background: radial-gradient(120% 140% at 15% 0%, #294b74 0%, #1F3A5C 45%, #142942 100%);
  color: #fff;
  min-height: 220px;
}

.brand-pattern {
  position: absolute;
  inset: 0;
  opacity: 0.5;
  background-image:
    repeating-linear-gradient(135deg, rgba(255,255,255,0.045) 0 1px, transparent 1px 34px),
    repeating-linear-gradient(45deg, rgba(255,255,255,0.03) 0 1px, transparent 1px 34px);
}

.brand-content {
  position: relative;
  max-width: 380px;
  margin: 0 auto;
}

.brand-mark svg { width: 46px; height: 46px; }

.brand-title {
  font-family: 'Manrope', 'Inter', system-ui, sans-serif;
  font-weight: 800;
  font-size: 1.9rem;
  letter-spacing: -0.01em;
  margin-top: 1.1rem;
}

.brand-subtitle {
  color: #a9c0dc;
  margin-top: 0.4rem;
  font-size: 0.95rem;
  line-height: 1.5;
}

.brand-facts {
  margin-top: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.brand-facts li {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  font-size: 0.875rem;
  color: #d7e3f2;
  line-height: 1.4;
}
.fact-dot {
  flex-shrink: 0;
  margin-top: 0.4rem;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #F59E0B;
}

/* ── Form panel ──────────────────────────────────────────────── */
.form-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  background: #f7f9fc;
}

.form-card {
  width: 100%;
  max-width: 380px;
  background: #fff;
  border: 1px solid #eef1f5;
  border-radius: 1.1rem;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 12px 32px -12px rgba(16, 24, 40, 0.1);
  padding: 2.25rem 2rem 1.75rem;
  animation: rise 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.form-title {
  font-family: 'Manrope', 'Inter', system-ui, sans-serif;
  font-weight: 700;
  font-size: 1.3rem;
  color: #101828;
}
.form-hint {
  color: #667085;
  font-size: 0.85rem;
  margin-top: 0.2rem;
}

.field-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: #344054;
  margin-bottom: 0.35rem;
}

.field-control {
  position: relative;
  display: flex;
  align-items: center;
}
.field-icon {
  position: absolute;
  left: 0.75rem;
  width: 17px;
  height: 17px;
  color: #98a2b3;
  pointer-events: none;
  transition: color 0.15s ease;
}
.field-control input {
  width: 100%;
  padding: 0.6rem 0.75rem 0.6rem 2.35rem;
  border: 1px solid #d0d5dd;
  border-radius: 0.6rem;
  font-size: 0.925rem;
  color: #101828;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.field-control input::placeholder { color: #98a2b3; }
.field-control input:focus {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.14);
}
.field-control input:focus + .field-icon,
.field-control:focus-within .field-icon { color: #2563EB; }

.error-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #fef3f2;
  border: 1px solid #fee4e2;
  color: #b42318;
  border-radius: 0.6rem;
  padding: 0.65rem 0.85rem;
  font-size: 0.825rem;
}
.error-banner svg { width: 16px; height: 16px; }

.submit-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.3rem;
  padding: 0.65rem 1rem;
  border-radius: 0.6rem;
  background: #2563EB;
  color: #fff;
  font-weight: 600;
  font-size: 0.925rem;
  transition: background-color 0.15s ease, transform 0.1s ease, box-shadow 0.15s ease;
  box-shadow: 0 1px 2px rgba(16,24,40,0.05);
}
.submit-btn:hover:not(:disabled) { background: #1d4ed8; transform: translateY(-1px); box-shadow: 0 4px 12px -2px rgba(37,99,235,0.35); }
.submit-btn:active:not(:disabled) { transform: translateY(0); }
.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.spinner { width: 17px; height: 17px; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.back-link {
  margin-top: 1.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  font-size: 0.825rem;
  color: #667085;
  transition: color 0.15s ease;
}
.back-link svg { width: 14px; height: 14px; }
.back-link:hover { color: #2563EB; }

/* ── Shared micro-interactions ───────────────────────────────── */
.shake { animation: shake 0.4s ease; }
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-6px); }
  40% { transform: translateX(5px); }
  60% { transform: translateX(-4px); }
  80% { transform: translateX(3px); }
}

.fade-slide-enter-active { transition: all 0.2s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateY(-4px); }

@media (prefers-reduced-motion: reduce) {
  .form-card, .shake, .spinner { animation: none; }
}
</style>
