<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Потоки обучения</h1>
      <button @click="showCreate = true" class="btn-primary">+ Новый поток</button>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div class="card w-full max-w-md">
        <h2 class="font-semibold text-lg mb-4">Новый поток</h2>
        <div class="space-y-3">
          <div>
            <label class="text-sm font-medium text-gray-700">Название</label>
            <input v-model="form.name" class="input-field mt-1" placeholder="Например: Поток май 2026 — КазТрансОйл" />
          </div>
          <div>
            <label class="text-sm font-medium text-gray-700">Организация</label>
            <select v-model="form.organization_id" class="input-field mt-1">
              <option value="">— Выберите организацию —</option>
              <option v-for="o in organizations" :key="o.id" :value="o.id">{{ o.name }}</option>
            </select>
          </div>
        </div>
        <div class="flex gap-3 mt-4">
          <button @click="createBatch" class="btn-primary">Создать</button>
          <button @click="showCreate = false" class="btn-secondary">Отмена</button>
        </div>
      </div>
    </div>

    <div class="space-y-3">
      <RouterLink
        v-for="b in batches"
        :key="b.id"
        :to="`/admin/batches/${b.id}`"
        class="card block hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="font-semibold">{{ b.name }}</div>
            <div class="text-sm text-gray-400 mt-1">{{ new Date(b.created_at).toLocaleDateString('ru-RU') }}</div>
          </div>
          <span :class="statusBadge(b.status)">{{ b.status }}</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/services/api'

const batches = ref([])
const organizations = ref([])
const showCreate = ref(false)
const form = ref({ name: '', organization_id: '' })

onMounted(async () => {
  const [b, o] = await Promise.all([api.get('/admin/batches'), api.get('/admin/organizations')])
  batches.value = b.data
  organizations.value = o.data
})

async function createBatch() {
  const payload = { ...form.value, organization_id: form.value.organization_id || null }
  await api.post('/admin/batches', payload)
  showCreate.value = false
  const { data } = await api.get('/admin/batches')
  batches.value = data
  form.value = { name: '', organization_id: '' }
}

function statusBadge(s) {
  return { draft: 'badge-assigned', processing: 'badge-progress', completed: 'badge-passed', archived: 'badge-failed' }[s] || 'badge-assigned'
}
</script>
