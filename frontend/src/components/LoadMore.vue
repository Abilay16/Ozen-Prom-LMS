<template>
  <div v-if="total > 0" class="load-more">
    <span class="load-more__count">Показано {{ shown }} из {{ total }}</span>
    <button
      v-if="shown < total"
      type="button"
      class="btn-secondary text-sm"
      :disabled="loading"
      @click="$emit('more')"
    >
      {{ loading ? 'Загрузка…' : 'Показать ещё' }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  shown: { type: Number, required: true },
  total: { type: Number, required: true },
  loading: { type: Boolean, default: false },
})
defineEmits(['more'])
</script>

<style scoped>
.load-more {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #f2f4f7;
}
.load-more__count {
  font-size: 0.8125rem;
  color: #667085;
  font-variant-numeric: tabular-nums;
}
</style>
