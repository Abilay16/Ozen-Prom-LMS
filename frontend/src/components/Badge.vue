<template>
  <span :class="cssClass"><slot /></span>
</template>

<script setup>
import { computed } from 'vue'

// variant maps directly onto the shared .badge-* utility classes in
// assets/main.css — one place to change the color language of "status"
// across the whole admin area instead of every page hand-rolling its own
// bg-*-100/text-*-800 combo.
const props = defineProps({
  variant: {
    type: String,
    default: 'neutral',
    validator: (v) => ['assigned', 'passed', 'failed', 'progress', 'neutral'].includes(v),
  },
})

const cssClass = computed(() => `badge-${props.variant}`)
</script>
