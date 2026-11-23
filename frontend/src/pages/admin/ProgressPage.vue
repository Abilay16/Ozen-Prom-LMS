<template>
  <div>
    <div class="flex items-end justify-between gap-3 mb-6">
      <h1 class="text-2xl font-bold">Прогресс обучения</h1>
      <button v-if="people.length" type="button" class="text-sm text-blue-700 hover:underline" @click="toggleAll">
        {{ allOpen ? 'Свернуть всех' : 'Развернуть всех' }}
      </button>
    </div>

    <!-- Filters -->
    <div class="flex gap-3 flex-wrap mb-4">
      <input
        v-model="filters.search"
        @input="debouncedLoad"
        placeholder="Поиск по ФИО..."
        class="input-field max-w-xs"
      />
      <select v-model="filters.organization_id" @change="load" class="input-field max-w-xs">
        <option value="">Все организации</option>
        <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
      </select>
      <select v-model="filters.batch_id" @change="load" class="input-field max-w-xs">
        <option value="">Все потоки</option>
        <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
      </select>
      <select v-model="filters.status" @change="load" class="input-field max-w-xs">
        <option value="">Все статусы</option>
        <option value="assigned">Назначен</option>
        <option value="in_progress">В процессе</option>
        <option value="passed">Сдан</option>
        <option value="failed">Не сдан</option>
      </select>
      <div class="flex items-center gap-1.5 w-full sm:w-auto">
        <span class="text-sm text-gray-500 shrink-0">Назначен:</span>
        <input type="date" v-model="filters.date_from" @change="load" class="input-field text-sm min-w-0 flex-1 sm:w-[9.5rem] sm:flex-none" aria-label="Назначен с" />
        <span class="text-gray-400">—</span>
        <input type="date" v-model="filters.date_to" @change="load" class="input-field text-sm min-w-0 flex-1 sm:w-[9.5rem] sm:flex-none" aria-label="Назначен по" />
      </div>
      <button @click="resetFilters" class="btn-secondary text-sm">Сброс</button>
    </div>


    <div class="card !p-0 overflow-x-auto">
      <table class="w-full text-sm progress-table">
        <thead>
          <tr>
            <th class="w-10"></th>
            <th class="text-left">Сотрудник</th>
            <th class="text-left hidden lg:table-cell">Организация</th>
            <th class="text-left">Обучения</th>
            <th class="text-left whitespace-nowrap hidden sm:table-cell">Итог</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="py-2"><RowsSkeleton :rows="4" /></td>
          </tr>
          <tr v-else-if="!people.length">
            <td colspan="5" class="px-4 py-10 text-center text-gray-400">
              {{ hasFilters ? 'Никого не найдено по этим фильтрам.' : 'Обучения ещё не назначены.' }}
            </td>
          </tr>
          <template v-for="p in people" :key="p.user.id">
            <!-- Сотрудник: одна строка на человека -->
            <tr
              class="person-row"
              :class="{ 'is-open': open[p.user.id] }"
              tabindex="0"
              role="button"
              :aria-expanded="!!open[p.user.id]"
              @click="toggle(p.user.id)"
              @keydown.enter.prevent="toggle(p.user.id)"
              @keydown.space.prevent="toggle(p.user.id)"
            >
              <td class="text-gray-400"><ChevronRight :size="18" class="chev" /></td>
              <td>
                <div class="font-medium text-gray-900">{{ p.user.full_name }}</div>
                <div class="text-xs text-gray-400">
                  {{ p.user.position_raw || 'Должность не указана' }}<span class="lg:hidden"> · {{ p.user.organization_name || '—' }}</span>
                </div>
              </td>
              <td class="text-gray-600 text-xs hidden lg:table-cell">{{ p.user.organization_name || '—' }}</td>
              <td>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="a in p.assignments" :key="a.id"
                    class="chip" :class="`chip--${a.status}`"
                    :title="`${a.course?.name || a.discipline?.name}: ${STATUS[a.status]?.label}${a.best_score != null ? ', ' + a.best_score + '%' : ''}`"
                  >
                    <component :is="STATUS[a.status]?.icon" :size="12" :stroke-width="2.6" />
                    {{ a.discipline?.name || a.course?.name }}
                  </span>
                </div>
                <div class="sm:hidden mt-1 text-xs text-gray-500">{{ p.summary.passed }} из {{ p.summary.total }} сдано</div>
              </td>
              <td class="whitespace-nowrap hidden sm:table-cell">
                <div class="text-xs font-medium" :class="p.summary.passed === p.summary.total ? 'text-emerald-700' : 'text-gray-700'">
                  {{ p.summary.passed }} из {{ p.summary.total }} сдано
                </div>
                <div class="mini-bar"><span :style="{ width: `${(p.summary.passed / (p.summary.total || 1)) * 100}%` }" /></div>
              </td>
            </tr>

            <!-- Подробности по каждому обучению -->
            <tr v-if="open[p.user.id]" class="details-row">
              <td class="hidden sm:table-cell"></td>
              <td colspan="5" class="sm:hidden !px-2"><!-- телефон: на всю ширину -->
                <div class="details">
                  <div v-for="a in p.assignments" :key="a.id" class="training">
                    <div class="training__name">
                      <div class="font-medium text-gray-900">{{ a.discipline?.name || '—' }}</div>
                      <div class="text-xs text-gray-500">{{ a.course?.name }}</div>
                    </div>
                    <span class="chip justify-self-end" :class="`chip--${a.status}`">
                      <component :is="STATUS[a.status]?.icon" :size="12" :stroke-width="2.6" />
                      {{ STATUS[a.status]?.label || a.status }}
                    </span>
                    <div class="text-xs text-gray-500">
                      <span v-if="a.best_score != null" :class="a.best_passed ? 'text-emerald-700' : 'text-red-600'" class="font-semibold">{{ a.best_score }}% · </span>
                      <template v-if="a.attempts_used">{{ attemptsLabel(a.attempts_used) }} · </template>назначен {{ formatDate(a.assigned_at) }}
                    </div>
                    <button
                      v-if="canEdit && (a.status === 'failed' || a.status === 'in_progress')"
                      type="button" class="retake-btn justify-self-end" @click.stop="allowRetake(a)"
                    >
                      <RotateCcw :size="14" /> Пересдача
                    </button>
                  </div>
                </div>
              </td>
              <td colspan="4" class="hidden sm:table-cell">
                <div class="details">
                  <div class="details__head">
                    <span>Логин: <span class="font-mono text-gray-700">{{ p.user.login }}</span></span>
                  </div>
                  <div v-for="a in p.assignments" :key="a.id" class="training">
                    <div class="training__name">
                      <div class="font-medium text-gray-900">{{ a.discipline?.name || '—' }}</div>
                      <div class="text-xs text-gray-500">{{ a.course?.name }}</div>
                    </div>
                    <span class="chip justify-self-start" :class="`chip--${a.status}`">
                      <component :is="STATUS[a.status]?.icon" :size="12" :stroke-width="2.6" />
                      {{ STATUS[a.status]?.label || a.status }}
                    </span>
                    <div class="training__score">
                      <span v-if="a.best_score != null" :class="a.best_passed ? 'text-emerald-700' : 'text-red-600'" class="font-semibold">{{ a.best_score }}%</span>
                      <span v-else class="text-gray-300">—</span>
                      <span class="text-xs text-gray-400 ml-1">{{ attemptsLabel(a.attempts_used) }}</span>
                    </div>
                    <div class="training__date text-xs text-gray-500">назначен {{ formatDate(a.assigned_at) }}</div>
                    <div class="training__action">
                      <button
                        v-if="canEdit && (a.status === 'failed' || a.status === 'in_progress')"
                        type="button"
                        class="retake-btn"
                        @click.stop="allowRetake(a)"
                      >
                        <RotateCcw :size="14" /> Пересдача
                      </button>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <LoadMore :shown="people.length" :total="list.total.value" :loading="list.loadingMore.value" @more="list.loadMore()" />
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ChevronRight, Circle, CircleCheck, CircleX, Clock, RotateCcw } from 'lucide-vue-next'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import RowsSkeleton from '@/components/RowsSkeleton.vue'
import LoadMore from '@/components/LoadMore.vue'
import { usePagedList } from '@/composables/usePagedList'
import { useRole } from '@/composables/useRole'

const toast = useToast()
const { canEdit } = useRole()
const { confirm } = useConfirm()

const organizations = ref([])
const batches = ref([])
const filters = ref({ search: '', organization_id: '', batch_id: '', status: '', date_from: '', date_to: '' })

// Одна запись на сотрудника со всеми его обучениями (раньше — строка на
// каждый курс, и один человек повторялся 3–4 раза).
const list = usePagedList('/admin/progress/by-user', () => ({ ...filters.value, search: filters.value.search.trim() }), { pageSize: 50 })
const people = list.items
const loading = list.loading
const open = ref({})

const hasFilters = computed(() => Object.values(filters.value).some(v => v))
const allOpen = computed(() => people.value.length > 0 && people.value.every(p => open.value[p.user.id]))

function toggle(id) {
  open.value = { ...open.value, [id]: !open.value[id] }
}
function toggleAll() {
  const next = !allOpen.value
  open.value = Object.fromEntries(people.value.map(p => [p.user.id, next]))
}

const STATUS = {
  assigned: { label: 'Назначен', variant: 'neutral', icon: Circle },
  in_progress: { label: 'В процессе', variant: 'assigned', icon: Clock },
  passed: { label: 'Сдан', variant: 'passed', icon: CircleCheck },
  failed: { label: 'Не сдан', variant: 'failed', icon: CircleX },
}

function attemptsLabel(n) {
  if (!n) return ''
  const mod10 = n % 10, mod100 = n % 100
  const word = mod10 === 1 && mod100 !== 11 ? 'попытка' : mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14) ? 'попытки' : 'попыток'
  return `${n} ${word}`
}

function formatDate(d) {
  return d ? new Date(d).toLocaleDateString('ru-RU') : '—'
}

let debounceTimer = null
function debouncedLoad() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 350)
}

onMounted(async () => {
  load()
  // Справочники для фильтров: ошибка в них не должна ломать сам список.
  const [o, b] = await Promise.allSettled([api.get('/admin/organizations'), api.get('/admin/batches')])
  if (o.status === 'fulfilled') organizations.value = o.value.data
  if (b.status === 'fulfilled') batches.value = b.value.data
})

function load() {
  return list.reload()
}

function resetFilters() {
  filters.value = { search: '', organization_id: '', batch_id: '', status: '', date_from: '', date_to: '' }
  load()
}

async function allowRetake(a) {
  const ok = await confirm({
    message: `Разрешить пересдачу «${a.discipline?.name || a.course?.name}»? Все предыдущие попытки будут сброшены.`,
    danger: true,
    confirmText: 'Разрешить',
  })
  if (!ok) return
  try {
    await api.post(`/admin/progress/${a.id}/allow-retake`)
    // Обновляем на месте — раскрытые строки и прокрутка не сбрасываются.
    a.status = 'assigned'
    a.best_score = null
    a.best_passed = null
    a.attempts_used = 0
    const person = people.value.find(p => p.assignments.includes(a))
    if (person) {
      person.summary = person.assignments.reduce(
        (acc, x) => ({ ...acc, [x.status]: (acc[x.status] || 0) + 1 }),
        { total: person.assignments.length, assigned: 0, in_progress: 0, passed: 0, failed: 0 },
      )
    }
    toast.success('Пересдача разрешена')
  } catch (e) {
    toast.error(apiErrorMessage(e))
  }
}
</script>


<style scoped>
.progress-table thead th {
  padding: 0.7rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: #667085;
  background: #f8fafc;
  border-bottom: 1px solid #e7e9ee;
}
.progress-table td { padding: 0.7rem 0.75rem; vertical-align: middle; }
.person-row { cursor: pointer; border-bottom: 1px solid #f1f3f6; }
.person-row:hover { background: #f8fafc; }
.person-row:focus-visible { outline: 2px solid #2563eb; outline-offset: -2px; }
.person-row.is-open { background: #f5f8fd; }
.chev { transition: transform 0.15s ease; }
.person-row.is-open .chev { transform: rotate(90deg); color: #1f3a5c; }

.chip {
  display: inline-flex; align-items: center; gap: 0.25rem;
  padding: 0.15rem 0.5rem 0.15rem 0.4rem; border-radius: 999px;
  font-size: 0.72rem; font-weight: 600; white-space: nowrap;
}
.chip--passed { background: #e7f6ee; color: #11683f; }
.chip--failed { background: #fdecec; color: #a12a1f; }
.chip--in_progress { background: #fff4e0; color: #9a5b00; }
.chip--assigned { background: #f1f3f6; color: #4b5565; }

.mini-bar { margin-top: 0.3rem; width: 5.5rem; height: 4px; border-radius: 999px; background: #eef0f4; overflow: hidden; }
.mini-bar span { display: block; height: 100%; background: #16a34a; border-radius: inherit; }

.details-row { background: #f5f8fd; border-bottom: 1px solid #e7e9ee; }
.details-row td { padding-top: 0; }
.details { background: #fff; border: 1px solid #e3e8f0; border-radius: 0.65rem; overflow: hidden; }
.details__head { padding: 0.5rem 0.85rem; font-size: 0.75rem; color: #8a93a3; border-bottom: 1px solid #f1f3f6; }
.training {
  display: grid;
  grid-template-columns: minmax(10rem, 1.6fr) auto minmax(6rem, 0.8fr) minmax(7rem, 0.8fr) minmax(7.5rem, auto);
  align-items: center; gap: 0.75rem;
  padding: 0.6rem 0.85rem; border-bottom: 1px solid #f1f3f6;
}
.training:last-child { border-bottom: 0; }
.training__action { text-align: right; }
@media (max-width: 900px) {
  .training { grid-template-columns: 1fr auto; row-gap: 0.35rem; }
  .training__score, .training__date { grid-column: 1; }
  .training__action { grid-column: 2; grid-row: 2 / span 2; }
}
.retake-btn {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.3rem 0.6rem; border-radius: 0.45rem;
  font-size: 0.75rem; font-weight: 600;
  background: #fff4e0; color: #9a5b00;
}
.retake-btn:hover { background: #ffe8bf; }
</style>
