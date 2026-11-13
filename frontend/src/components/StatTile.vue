<template>
  <div class="stat-tile">
    <span class="stat-icon" :class="tone.chip">
      <svg viewBox="0 0 20 20" fill="none">
        <path :d="ICONS[icon]" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </span>
    <div class="stat-value" :class="tone.value">
      <span v-if="value === null" class="stat-skel"></span>
      <template v-else>{{ value }}</template>
    </div>
    <div class="stat-label">{{ label }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  icon: { type: String, required: true },
  tone: { type: String, default: 'primary' },
  label: { type: String, required: true },
  value: { type: [Number, String, null], default: null },
})

const ICONS = {
  users: 'M6.5 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Zm7 0a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5ZM2 15c0-2.2 2-4 4.5-4s4.5 1.8 4.5 4M11.5 11.3c.4-.2.9-.3 1.5-.3 2.5 0 4.5 1.8 4.5 4',
  batches: 'M3 5a1.5 1.5 0 0 1 1.5-1.5h3l1 1.5h7A1.5 1.5 0 0 1 17 6.5v7A1.5 1.5 0 0 1 15.5 15h-11A1.5 1.5 0 0 1 3 13.5V5Z',
  check: 'M4 10.5 8 14l8-8',
  clock: 'M10 5.5V10l3 2M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z',
  x: 'M6 6l8 8M14 6l-8 8',
}

const TONE_CLASSES = {
  primary: { chip: 'bg-blue-50 text-blue-600', value: 'text-blue-700' },
  violet:  { chip: 'bg-violet-50 text-violet-600', value: 'text-violet-700' },
  good:    { chip: 'bg-green-50 text-green-600', value: 'text-green-700' },
  warning: { chip: 'bg-amber-50 text-amber-600', value: 'text-amber-700' },
  critical:{ chip: 'bg-red-50 text-red-600', value: 'text-red-700' },
}

const tone = computed(() => TONE_CLASSES[props.tone] || TONE_CLASSES.primary)
</script>

<style scoped>
.stat-tile {
  background: #fff;
  border: 1px solid #f1f3f6;
  border-radius: 0.9rem;
  padding: 1.1rem;
  box-shadow: 0 1px 2px rgba(16,24,40,0.03);
  animation: tile-rise 0.35s cubic-bezier(0.16,1,0.3,1) both;
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}
.stat-tile:hover { box-shadow: 0 6px 20px -8px rgba(16,24,40,0.12); transform: translateY(-1px); }

@keyframes tile-rise {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.stat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.6rem;
  margin-bottom: 0.6rem;
  overflow: hidden;
}
.stat-icon svg { width: 17px; height: 17px; flex-shrink: 0; }

.stat-value {
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1.1;
  font-variant-numeric: proportional-nums;
  min-height: 1.9rem;
  display: flex;
  align-items: center;
}
.stat-label { font-size: 0.8rem; color: #667085; margin-top: 0.2rem; }

.stat-skel {
  display: inline-block;
  width: 2.5rem;
  height: 1.3rem;
  border-radius: 0.3rem;
  background: linear-gradient(90deg, #eef1f5 25%, #f6f8fa 37%, #eef1f5 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}
@keyframes shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .stat-tile, .stat-skel { animation: none; }
}
</style>
