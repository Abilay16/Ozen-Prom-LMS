<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Организации</h1>
      <button @click="openCreate" class="btn-primary">+ Добавить</button>
    </div>

    <!-- Modal -->
    <div v-if="modal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-md">
        <h2 class="font-semibold text-lg mb-4">{{ editing ? 'Редактировать' : 'Новая организация' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium text-gray-700">Полное название</label>
            <input v-model="form.name" class="input-field mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Краткое название</label>
            <input v-model="form.short_name" class="input-field mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">БИН</label>
            <input v-model="form.bin" class="input-field mt-1" maxlength="12" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Email контакта</label>
            <input v-model="form.contact_email" type="email" class="input-field mt-1" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Телефон контакта</label>
            <input v-model="form.contact_phone" class="input-field mt-1" />
          </div>
        </div>
        <div class="flex gap-3 mt-4">
          <button @click="save" class="btn-primary">{{ editing ? 'Сохранить' : 'Создать' }}</button>
          <button @click="modal = false" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <div class="card overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-brand-dark text-white">
          <tr>
            <th class="text-left px-4 py-3">Название</th>
            <th class="text-left px-4 py-3">Краткое</th>
            <th class="text-left px-4 py-3">БИН</th>
            <th class="text-left px-4 py-3">Email</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="org in orgs" :key="org.id" class="border-b hover:bg-gray-50">
            <td class="px-4 py-3 font-medium">{{ org.name }}</td>
            <td class="px-4 py-3">{{ org.short_name }}</td>
            <td class="px-4 py-3">{{ org.bin }}</td>
            <td class="px-4 py-3">{{ org.contact_email }}</td>
            <td class="px-4 py-3">
              <button @click="openEdit(org)" class="text-blue-600 hover:underline text-xs">Изменить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const orgs = ref([])
const modal = ref(false)
const editing = ref(null)
const form = ref({ name: '', short_name: '', bin: '', contact_email: '', contact_phone: '' })

onMounted(load)

async function load() {
  const { data } = await api.get('/admin/organizations')
  orgs.value = data
}

function openCreate() {
  editing.value = null
  form.value = { name: '', short_name: '', bin: '', contact_email: '', contact_phone: '' }
  modal.value = true
}

function openEdit(org) {
  editing.value = org
  form.value = { name: org.name, short_name: org.short_name, bin: org.bin, contact_email: org.contact_email, contact_phone: org.contact_phone }
  modal.value = true
}

async function save() {
  if (editing.value) {
    await api.patch(`/admin/organizations/${editing.value.id}`, form.value)
  } else {
    await api.post('/admin/organizations', form.value)
  }
  modal.value = false
  await load()
}
</script>
