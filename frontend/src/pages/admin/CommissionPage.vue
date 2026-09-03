<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Состав комиссии</h1>
    </div>

    <p class="text-sm text-gray-500 mb-4">
      Отметьте сотрудников, которые могут входить в экзаменационную комиссию, и укажите их должности для протоколов.
      Отмеченные «В комиссии» автоматически подставляются в состав нового протокола (председатель по умолчанию —
      председателем, остальные — членами); в самом протоколе состав можно менять как обычно.
    </p>

    <div v-if="isCommission" class="bg-blue-50 border border-blue-200 text-blue-800 rounded-lg px-4 py-2 text-sm mb-4">
      ℹ️ Вы просматриваете состав комиссии в режиме чтения.
    </div>

    <div v-if="loading" class="text-gray-400 py-8 text-center">Загрузка...</div>

    <div v-else class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">ФИО</th>
            <th class="text-left px-4 py-3">Логин</th>
            <th class="text-left px-4 py-3 min-w-[260px]">Должность для протоколов</th>
            <th class="text-center px-4 py-3">В комиссии</th>
            <th class="text-center px-4 py-3">Председатель по умолчанию</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ u.full_name }}</td>
            <td class="px-4 py-3 text-gray-500">{{ u.login }}</td>
            <td class="px-4 py-3">
              <input
                v-model="u._positionDraft"
                class="input-field text-sm"
                placeholder="Председатель / Член комиссии..."
                :disabled="isCommission"
                @blur="!isCommission && savePositionTitle(u)"
                @keydown.enter.prevent="!isCommission && savePositionTitle(u)"
              />
            </td>
            <td class="px-4 py-3 text-center">
              <input
                type="checkbox"
                :checked="u.is_commission_eligible"
                class="w-4 h-4"
                :class="isCommission ? 'cursor-default opacity-60' : 'cursor-pointer'"
                :disabled="isCommission"
                @change="!isCommission && toggleEligible(u)"
              />
            </td>
            <td class="px-4 py-3 text-center">
              <input
                type="radio"
                name="default_chair"
                :checked="u.is_default_chair"
                class="w-4 h-4"
                :class="isCommission ? 'cursor-default opacity-60' : 'cursor-pointer'"
                :disabled="isCommission"
                @change="!isCommission && setDefaultChair(u)"
              />
            </td>
          </tr>
          <tr v-if="!users.length">
            <td colspan="5" class="text-center text-gray-400 py-8">Нет пользователей</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'

const toast = useToast()
const isCommission = localStorage.getItem('is_commission') === '1'
const users = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/admin/admin-users')
    users.value = data.map(u => ({ ...u, _positionDraft: u.position_title || '' }))
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Ошибка загрузки'))
  } finally {
    loading.value = false
  }
})

async function patch(u, payload) {
  try {
    const { data } = await api.patch(`/admin/admin-users/${u.id}`, payload)
    Object.assign(u, data, { _positionDraft: data.position_title || '' })
    toast.success('Сохранено')
  } catch (e) {
    toast.error(apiErrorMessage(e, 'Ошибка сохранения'))
  }
}

async function toggleEligible(u) {
  await patch(u, { is_commission_eligible: !u.is_commission_eligible })
}

async function setDefaultChair(u) {
  await patch(u, { is_default_chair: true })
  users.value.forEach(x => { x.is_default_chair = x.id === u.id })
}

async function savePositionTitle(u) {
  const title = u._positionDraft.trim() || null
  if (title === (u.position_title || null)) return
  await patch(u, { position_title: title })
}
</script>
