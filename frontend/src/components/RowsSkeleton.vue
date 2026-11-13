<template>
  <div class="rows-skel" role="status" aria-label="Загрузка...">
    <div v-for="i in rows" :key="i" class="rows-skel-row" :style="{ animationDelay: `${i * 40}ms` }">
      <span class="skel" :style="{ width: widths[i % widths.length] }"></span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  rows: { type: Number, default: 5 },
})
const widths = ['92%', '78%', '85%', '70%', '88%']
</script>

<style scoped>
.rows-skel { display: flex; flex-direction: column; gap: 0.85rem; padding: 0.5rem 0; }
.rows-skel-row {
  height: 1.1rem;
  display: flex;
  align-items: center;
  animation: row-rise 0.3s ease both;
}
.rows-skel-row .skel { height: 0.9rem; }
@keyframes row-rise {
  from { opacity: 0; transform: translateY(3px); }
  to   { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: reduce) {
  .rows-skel-row { animation: none; }
}
</style>
