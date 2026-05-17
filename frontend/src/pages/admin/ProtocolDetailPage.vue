<template>
  <div v-if="!pageReady" class="flex items-center justify-center py-20 text-gray-400">
    Загрузка...
  </div>
  <div v-else>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <button @click="$router.back()" class="text-gray-500 hover:text-gray-700">← Назад</button>
      <h1 class="text-2xl font-bold text-gray-800 flex-1">
        {{ isNew ? 'Новый протокол' : `Протокол № ${form.protocol_number}` }}
      </h1>
      <span v-if="!isNew" class="px-2 py-1 rounded text-sm font-medium" :class="statusClass(protocol?.status)">
        {{ statusLabel(protocol?.status) }}
      </span>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left: main form -->
      <div class="lg:col-span-2 space-y-4">

        <!-- Lock notice for non-draft protocols -->
        <div v-if="!isNew && !isDraft" class="bg-amber-50 border border-amber-300 text-amber-800 rounded-lg px-4 py-2 text-sm">
          ⚠ Протокол {{ protocol.status === 'archived' ? 'архивирован' : 'отправлен на подпись или уже подписан' }} — редактирование заблокировано.
        </div>

        <!-- Basic info card -->
        <div class="bg-white rounded-xl shadow-sm p-5">
          <h2 class="font-semibold text-gray-700 mb-4">Основная информация</h2>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-gray-500 mb-1">Тип проверки знаний *</label>
              <select v-model="form.training_type_id" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500">
                <option value="">— выберите —</option>
                <option v-for="tt in trainingTypes" :key="tt.id" :value="tt.id">{{ tt.name_short }} — {{ tt.name_ru }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Поток обучения</label>
              <select v-model="form.batch_id" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500">
                <option value="">— выберите —</option>
                <option v-for="b in batches" :key="b.id" :value="b.id">{{ b.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Номер протокола *</label>
              <input v-model="form.protocol_number" type="text" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50" placeholder="Напр. №b62" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Дата экзамена *</label>
              <input v-model="form.exam_date" type="date" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Номер приказа</label>
              <input v-model="form.order_number" type="text" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50" placeholder="Напр. 05/пп" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Дата приказа</label>
              <input v-model="form.order_date" type="date" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50" />
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-gray-500 mb-1">Основание (ст. закона)</label>
              <input v-model="form.legal_basis" type="text" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50" placeholder='Напр. "на основании ст 79 РК «О Гражданской защите»"' />
            </div>
            <div class="col-span-2">
              <label class="block text-xs text-gray-500 mb-1">Нормативные документы (каждый с новой строки)</label>
              <textarea v-model="form.regulatory_docs" rows="3" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Вид проверки знаний</label>
              <select v-model="form.check_type" :disabled="!isDraft" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500">
                <option value="">— не указан —</option>
                <option value="первичный">Первичный</option>
                <option value="периодический">Периодический</option>
                <option value="повторный">Повторный</option>
                <option value="внеплановый">Внеплановый</option>
              </select>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-4">
            <button
              v-if="!isNew"
              @click="router.push(`/admin/protocols/${route.params.id}/print`)"
              class="bg-gray-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-gray-700"
            >
              🖨 Печать протокола
            </button>
            <button v-if="isDraft && !isCommission" @click="saveMainForm" :disabled="saving" class="bg-brand-dark text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-opacity-90 disabled:opacity-50">
              {{ isNew ? 'Создать протокол' : 'Сохранить' }}
            </button>
          </div>
        </div>

        <!-- Commission card (only after protocol created) -->
        <div v-if="!isNew" class="bg-white rounded-xl shadow-sm p-5">
          <h2 class="font-semibold text-gray-700 mb-3">Состав комиссии</h2>
          <div v-if="protocol.commission_members.length === 0" class="text-sm text-gray-400 mb-3">Комиссия не добавлена</div>
          <div v-for="m in protocol.commission_members" :key="m.id" class="py-2 border-b border-gray-100 last:border-0">
            <div class="flex items-center gap-3">
              <span class="px-2 py-0.5 rounded text-xs shrink-0" :class="m.role === 'chair' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'">
                {{ m.role === 'chair' ? 'Председатель' : 'Член' }}
              </span>
              <span class="flex-1 text-sm">{{ m.position_title ? `${m.position_title} — ` : '' }}{{ m.full_name }}</span>
              <!-- Sign status -->
              <span v-if="m.signed_at" class="text-green-600 text-xs shrink-0" :title="formatDateTime(m.signed_at)">✓ Подписал</span>
              <span v-else-if="protocol.status === 'awaiting_signatures'" class="text-yellow-500 text-xs shrink-0">⧖ Ожидает</span>
              <button v-if="protocol.status === 'draft' && !isCommission" @click="removeCommissionMember(m.id)" class="text-red-400 hover:text-red-600 text-xs shrink-0">✕</button>
            </div>
            <!-- EDS stamp for signed members -->
            <div v-if="m.signer_cert_serial" class="mt-2 ml-2">
              <SignatureStamp
                :serial="m.signer_cert_serial"
                :owner="m.signer_cert_owner"
                :valid-from="m.signer_cert_valid_from"
                :valid-to="m.signer_cert_valid_to"
                :signed-at="m.signed_at"
                compact
              />
            </div>
          </div>
          <!-- Add member form (only in draft, only for superadmin) -->
          <div v-if="protocol.status === 'draft' && !isCommission" class="mt-3 bg-gray-50 rounded-lg p-3">
            <div class="grid grid-cols-3 gap-2 mb-2">
              <select v-model="newMember.role" class="border border-gray-300 rounded px-2 py-1.5 text-xs">
                <option value="chair">Председатель</option>
                <option value="member">Член комиссии</option>
              </select>
              <select v-model="newMember.admin_user_id" @change="onCandidateSelected" class="border border-gray-300 rounded px-2 py-1.5 text-xs">
                <option value="">— выберите пользователя —</option>
                <option v-for="u in commissionCandidates" :key="u.id" :value="u.id">{{ u.full_name }}</option>
              </select>
              <input v-model="newMember.position_title" placeholder="Должность" class="border border-gray-300 rounded px-2 py-1.5 text-xs" />
            </div>
            <button @click="addCommissionMember" class="text-xs bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700">+ Добавить</button>
          </div>
        </div>

        <!-- Participants card -->
        <div v-if="!isNew" class="bg-white rounded-xl shadow-sm p-5">
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-semibold text-gray-700">Участники ({{ protocol.participants.length }})</h2>
            <div class="flex gap-2">
              <button
                v-if="protocol.batch_id && protocol.status === 'draft' && !isCommission"
                @click="importFromBatch"
                :disabled="importing"
                class="text-xs bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {{ importing ? 'Загрузка...' : '⬇ Загрузить из потока' }}
              </button>
              <button
                v-if="protocol.status === 'signed' && protocol.participants.some(p => p.result === 'passed' && !p.certificate?.id) && !isCommission"
                @click="issueCertificates"
                class="text-xs bg-green-600 text-white px-3 py-1.5 rounded hover:bg-green-700"
              >
                Выдать удостоверения (сдавшим)
              </button>
            </div>
          </div>

          <!-- Empty state - no batch selected -->
          <div v-if="protocol.participants.length === 0 && !protocol.batch_id" class="text-sm text-gray-400 mb-3">
            Выберите поток обучения, затем нажмите «Загрузить из потока»
          </div>
          <!-- Empty state - batch selected but not imported -->
          <div v-else-if="protocol.participants.length === 0" class="text-sm text-gray-400 mb-3">
            Участников нет — нажмите «Загрузить из потока»
          </div>

          <table v-if="protocol.participants.length > 0" class="w-full text-xs mb-3">
            <thead class="bg-gray-50">
              <tr>
                <th class="text-left px-2 py-2 font-medium text-gray-500">№</th>
                <th class="text-left px-2 py-2 font-medium text-gray-500">ФИО</th>
                <th class="text-left px-2 py-2 font-medium text-gray-500">Должность</th>
                <th class="text-left px-2 py-2 font-medium text-gray-500">Образование</th>
                <th class="text-left px-2 py-2 font-medium text-gray-500">Результат</th>
                <th class="px-2 py-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, i) in protocol.participants" :key="p.id" class="border-t border-gray-100">
                <td class="px-2 py-2 text-gray-500">{{ i + 1 }}</td>
                <td class="px-2 py-2">{{ p.full_name }}</td>
                <td class="px-2 py-2 text-gray-600">{{ p.position || '—' }}</td>
                <td class="px-2 py-2 text-gray-600">{{ p.education || '—' }}</td>
                <td class="px-2 py-2">
                  <select
                    :value="p.result"
                    @change="updateParticipantResult(p.id, $event.target.value)"
                    :disabled="protocol.status !== 'draft' || isCommission"
                    class="border border-gray-300 rounded px-1 py-0.5 text-xs disabled:opacity-50 disabled:bg-gray-50"
                    :class="p.result === 'passed' ? 'text-green-700' : p.result === 'failed' ? 'text-red-700' : ''"
                  >
                    <option value="">—</option>
                    <option value="passed">Сдал</option>
                    <option value="failed">Не сдал</option>
                  </select>
                  <span v-if="p.certificate?.id" class="ml-1 text-green-600" title="Удостоверение выдано">📜</span>
                  <router-link v-if="p.certificate?.id" :to="`/admin/certificates/${p.certificate.id}`" class="ml-1 text-blue-500 hover:text-blue-700 text-xs" title="Открыть удостоверение">📄</router-link>
                </td>
                <td class="px-2 py-2 text-right">
                  <button v-if="protocol.status === 'draft' && !isCommission" @click="removeParticipant(p.id)" class="text-red-400 hover:text-red-600">✕</button>
                </td>
              </tr>
            </tbody>
          </table>

          <!-- Manual add (collapsed, fallback) -->
          <div v-if="protocol.status === 'draft' && !isCommission">
            <button @click="showManualAdd = !showManualAdd" class="text-xs text-gray-400 hover:text-gray-600 mt-1">
              {{ showManualAdd ? '▲ Скрыть' : '+ Добавить вручную' }}
            </button>
            <div v-if="showManualAdd" class="mt-2 bg-gray-50 rounded-lg p-3">
              <div class="grid grid-cols-4 gap-2 mb-2">
                <input v-model="newParticipant.full_name" placeholder="ФИО *" class="col-span-2 border border-gray-300 rounded px-2 py-1.5 text-xs" />
                <input v-model="newParticipant.position" placeholder="Должность" class="border border-gray-300 rounded px-2 py-1.5 text-xs" />
                <select v-model="newParticipant.education" class="border border-gray-300 rounded px-2 py-1.5 text-xs">
                  <option value="">Образование</option>
                  <option value="высшее">Высшее</option>
                  <option value="среднее">Среднее</option>
                  <option value="среднее специальное">Ср. спец.</option>
                </select>
              </div>
              <button @click="addParticipant" class="text-xs bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700">+ Добавить</button>
            </div>
          </div>
        </div>

      </div>

      <!-- Right: status + actions -->
      <div class="space-y-4">
        <div v-if="!isNew" class="bg-white rounded-xl shadow-sm p-5">
          <h2 class="font-semibold text-gray-700 mb-3">Действия</h2>
          <div class="space-y-3 text-sm">

            <!-- Status badge -->
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded text-xs font-medium" :class="statusClass(protocol.status)">
                {{ statusLabel(protocol.status) }}
              </span>
            </div>

            <!-- Batch info -->
            <div v-if="protocol.batch">
              <div class="text-xs text-gray-400">Поток</div>
              <div class="font-medium text-gray-700">{{ protocol.batch.name }}</div>
            </div>

            <hr />

            <!-- DRAFT: send for signatures -->
            <div v-if="protocol.status === 'draft' && !isCommission">
              <p class="text-xs text-gray-500 mb-2">
                После добавления комиссии и участников — отправьте на подпись.
              </p>
              <button @click="requestSignatures"
                      :disabled="protocol.commission_members.length === 0"
                      class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40">
                → Отправить на подпись
              </button>
            </div>

            <!-- AWAITING_SIGNATURES -->
            <div v-if="protocol.status === 'awaiting_signatures'">
              <p class="text-xs text-gray-500 mb-2">Протокол ожидает подписей:</p>
              <ul class="space-y-1 mb-3">
                <li v-for="m in protocol.commission_members" :key="m.id"
                    class="flex items-center justify-between text-xs">
                  <span class="text-gray-700">{{ m.full_name }}</span>
                  <span v-if="m.signed_at" class="text-green-600">✓ {{ formatDate(m.signed_at) }}</span>
                  <span v-else class="text-yellow-500">⧖ ожидает</span>
                </li>
              </ul>

              <template v-if="myCommissionSlot">
                <div v-if="myCommissionSlot.signed_at" class="text-green-600 text-xs text-center py-2">
                  ✓ Вы уже подписали ({{ formatDate(myCommissionSlot.signed_at) }})
                </div>
                <div v-else>
                  <p v-if="myCommissionSlot.role === 'chair' && unsignedMembersCount > 0"
                     class="text-xs text-gray-400 mb-1">
                    Ожидаем подписи {{ unsignedMembersCount }} чл. комиссии...
                  </p>
                  <button @click="signProtocol"
                          :disabled="myCommissionSlot.role === 'chair' && unsignedMembersCount > 0"
                          class="w-full bg-green-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-40">
                    {{ myCommissionSlot.role === 'chair' ? '✓ Подписать (председатель)' : '✓ Подписать' }}
                  </button>
                </div>
              </template>
              <p v-else class="text-xs text-gray-400 italic">Вы не входите в состав комиссии</p>
            </div>

            <!-- SIGNED -->
            <div v-if="protocol.status === 'signed'">
              <div class="text-green-600 text-sm font-medium text-center py-2">✓ Протокол подписан</div>
              <button v-if="!isCommission" @click="setStatus('archived')"
                      class="w-full bg-gray-400 text-white py-2 rounded-lg text-sm font-medium hover:bg-gray-500 mt-2">
                Архивировать
              </button>
            </div>

            <hr />
            <div class="text-xs text-gray-500 space-y-1">
              <div>Участников: {{ protocol.participants.length }}</div>
              <div>Сдали: {{ passedCount }}</div>
              <div>Удостоверений выдано: {{ issuedCount }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="fixed bottom-4 right-4 bg-red-100 text-red-700 px-4 py-3 rounded-xl shadow text-sm">{{ error }}</div>
    <div v-if="success" class="fixed bottom-4 right-4 bg-green-100 text-green-700 px-4 py-3 rounded-xl shadow text-sm">{{ success }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { signWithNcaLayer } from '@/services/ncaLayer'
import SignatureStamp from '@/components/SignatureStamp.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isCommission = localStorage.getItem('is_commission') === '1'

const isNew = computed(() => route.params.id === 'new')
const isDraft = computed(() => !protocol.value || protocol.value.status === 'draft')
const protocol = ref(null)
const trainingTypes = ref([])
const batches = ref([])
const commissionCandidates = ref([])
const pageReady = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')

const form = ref({
  training_type_id: '',
  batch_id: '',
  organization_id: '',
  protocol_number: '',
  exam_date: '',
  order_number: '',
  order_date: '',
  legal_basis: '',
  regulatory_docs: '',
  check_type: '',
})

const newMember = ref({ role: 'member', admin_user_id: '', position_title: '' })
const newParticipant = ref({ full_name: '', position: '', education: '' })
const importing = ref(false)
const showManualAdd = ref(false)

const passedCount = computed(() => protocol.value?.participants.filter(p => p.result === 'passed').length ?? 0)
const issuedCount = computed(() => protocol.value?.participants.filter(p => p.certificate?.id).length ?? 0)

// Current admin's commission slot (if any)
const myCommissionSlot = computed(() =>
  protocol.value?.commission_members.find(m => m.admin_user_id === auth.userId) ?? null
)
// How many non-chair members haven't signed yet
const unsignedMembersCount = computed(() =>
  protocol.value?.commission_members.filter(m => m.role === 'member' && !m.signed_at).length ?? 0
)

function flash(msg, type = 'success') {
  if (type === 'success') { success.value = msg; setTimeout(() => success.value = '', 3000) }
  else { error.value = msg; setTimeout(() => error.value = '', 4000) }
}

async function loadProtocol() {
  if (isNew.value) return
  const res = await api.get(`/admin/protocols/${route.params.id}`)
  protocol.value = res.data
  Object.assign(form.value, {
    training_type_id: res.data.training_type_id ?? '',
    batch_id: res.data.batch_id ?? '',
    organization_id: res.data.organization_id ?? '',
    protocol_number: res.data.protocol_number,
    exam_date: res.data.exam_date,
    order_number: res.data.order_number ?? '',
    order_date: res.data.order_date ?? '',
    legal_basis: res.data.legal_basis ?? '',
    regulatory_docs: res.data.regulatory_docs ?? '',
    check_type: res.data.check_type ?? '',
  })
}

onMounted(async () => {
  const [ttRes, batchRes, candRes] = await Promise.all([
    api.get('/admin/training-types'),
    api.get('/admin/batches'),
    api.get('/admin/protocols/commission-candidates'),
  ])
  trainingTypes.value = ttRes.data
  batches.value = batchRes.data
  commissionCandidates.value = candRes.data
  await loadProtocol()
  pageReady.value = true
})

async function saveMainForm() {
  if (!form.value.protocol_number || !form.value.exam_date || !form.value.training_type_id) {
    flash('Заполните обязательные поля (*)', 'error')
    return
  }
  saving.value = true
  try {
    const payload = { ...form.value }
    if (!payload.batch_id) delete payload.batch_id
    if (!payload.organization_id) delete payload.organization_id
    if (!payload.order_date) delete payload.order_date
    if (!payload.check_type) delete payload.check_type
    if (isNew.value) {
      const res = await api.post('/admin/protocols', payload)
      router.replace(`/admin/protocols/${res.data.id}`)
      flash('Протокол создан')
    } else {
      await api.patch(`/admin/protocols/${route.params.id}`, payload)
      await loadProtocol()
      flash('Сохранено')
    }
  } catch (e) {
    flash(e.response?.data?.detail ?? 'Ошибка сохранения', 'error')
  } finally {
    saving.value = false
  }
}

async function setStatus(status) {
  if (!confirm(`Архивировать протокол?`)) return
  await api.patch(`/admin/protocols/${route.params.id}`, { status })
  await loadProtocol()
  flash('Протокол архивирован')
}

async function addCommissionMember() {
  if (!newMember.value.admin_user_id) { flash('Выберите пользователя', 'error'); return }
  await api.post(`/admin/protocols/${route.params.id}/commission`, newMember.value)
  newMember.value = { role: 'member', admin_user_id: '', position_title: '' }
  await loadProtocol()
}

async function removeCommissionMember(id) {
  await api.delete(`/admin/protocols/${route.params.id}/commission/${id}`)
  await loadProtocol()
}

async function addParticipant() {
  if (!newParticipant.value.full_name.trim()) { flash('Введите ФИО', 'error'); return }
  await api.post(`/admin/protocols/${route.params.id}/participants`, newParticipant.value)
  newParticipant.value = { full_name: '', position: '', education: '' }
  await loadProtocol()
}

async function removeParticipant(id) {
  if (!confirm('Удалить участника?')) return
  await api.delete(`/admin/protocols/${route.params.id}/participants/${id}`)
  await loadProtocol()
}

async function updateParticipantResult(id, result) {
  await api.patch(`/admin/protocols/${route.params.id}/participants/${id}`, { result: result || null })
  await loadProtocol()
}

async function importFromBatch() {
  importing.value = true
  try {
    const res = await api.post(`/admin/protocols/${route.params.id}/import-participants`)
    await loadProtocol()
    flash(`Загружено: ${res.data.added} участников из потока`)
  } catch (e) {
    flash(e.response?.data?.detail ?? 'Ошибка импорта', 'error')
  } finally {
    importing.value = false
  }
}

async function issueCertificates() {
  if (!confirm('Выдать удостоверения всем участникам, сдавшим экзамен?')) return
  try {
    const res = await api.post(`/admin/protocols/${route.params.id}/issue-certificates`)
    flash(`Выдано: ${res.data.issued.length} удостоверений`)
    await loadProtocol()
  } catch (e) {
    flash(e.response?.data?.detail ?? 'Ошибка', 'error')
  }
}

function statusLabel(s) {
  return {
    draft: 'Черновик',
    awaiting_signatures: 'На подписи',
    signed: 'Подписан',
    archived: 'Архив',
  }[s] ?? s
}

function statusClass(s) {
  return {
    draft: 'bg-yellow-100 text-yellow-700',
    awaiting_signatures: 'bg-blue-100 text-blue-700',
    signed: 'bg-green-100 text-green-700',
    archived: 'bg-gray-100 text-gray-600',
  }[s] ?? 'bg-gray-100 text-gray-600'
}

async function requestSignatures() {
  if (!confirm('Отправить протокол на подпись членам комиссии?')) return
  try {
    const res = await api.post(`/admin/protocols/${route.params.id}/request-signatures`)
    protocol.value = res.data
    flash('Протокол отправлен на подпись')
  } catch (e) {
    flash(e.response?.data?.detail ?? 'Ошибка', 'error')
  }
}

async function signProtocol() {
  const isChair = myCommissionSlot.value?.role === 'chair'
  const msg = isChair
    ? 'Подписать протокол (председатель)? Это завершит процесс подписания.'
    : 'Подтвердить свою подпись под протоколом?'
  if (!confirm(msg)) return

  let cms = null
  try {
    // 1. Get the deterministic payload string from the backend
    const payloadRes = await api.get(`/admin/protocols/${route.params.id}/signature-payload`)
    const payloadStr = payloadRes.data.payload

    // 2. Sign with NCALayer (opens certificate selection dialog)
    cms = await signWithNcaLayer(payloadStr)
  } catch (ncaErr) {
    // EDS is mandatory — signing without NCALayer is not allowed
    alert(`Ошибка ЭЦП: ${ncaErr.message}\n\nПодписание без ЭЦП невозможно. Убедитесь, что NCALayer запущен, и попробуйте снова.`)
    return
  }

  try {
    const body = { cms }
    const res = await api.post(`/admin/protocols/${route.params.id}/sign`, body)
    protocol.value = res.data
    flash(isChair ? 'Протокол подписан!' : 'Ваша подпись зафиксирована')
  } catch (e) {
    flash(e.response?.data?.detail ?? 'Ошибка', 'error')
  }
}

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function formatDateTime(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('ru-RU')
}

function onCandidateSelected() {
  const u = commissionCandidates.value.find(c => c.id === newMember.value.admin_user_id)
  if (u && u.position_title && !newMember.value.position_title) {
    newMember.value.position_title = u.position_title
  }
}
</script>
