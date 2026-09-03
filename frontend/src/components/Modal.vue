<template>
  <Teleport to="body">
    <Transition name="modal-backdrop">
      <div
        v-if="modelValue"
        class="modal-backdrop"
        @click.self="close"
      >
        <Transition name="modal-panel" appear>
          <div v-if="modelValue" class="modal-panel" :class="maxWidth" role="dialog" aria-modal="true">
            <h2 v-if="title" class="font-semibold text-lg mb-4">{{ title }}</h2>
            <slot />
            <div v-if="$slots.footer" class="flex gap-3 mt-4">
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  // Any Tailwind max-w-* class — kept as a prop instead of a fixed set of
  // sizes since existing pages already use a handful of different widths.
  maxWidth: { type: String, default: 'max-w-lg' },
})
const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}

// A window-level listener (rather than a @keydown.esc on the backdrop) so
// Escape closes the modal regardless of what currently has focus — most
// callers don't autofocus anything inside, so a backdrop-only listener
// would silently never fire.
function onKeydown(e) {
  if (e.key === 'Escape') close()
}
watch(() => props.modelValue, (open) => {
  if (open) window.addEventListener('keydown', onKeydown)
  else window.removeEventListener('keydown', onKeydown)
}, { immediate: true })
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-panel {
  width: 100%;
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.2);
  max-height: calc(100vh - 32px);
  overflow-y: auto;
}

/* Motion — transform + opacity only, matches ConfirmDialog */
.modal-backdrop-enter-active,
.modal-backdrop-leave-active {
  transition: opacity 180ms ease;
}
.modal-backdrop-enter-from,
.modal-backdrop-leave-to {
  opacity: 0;
}

.modal-panel-enter-active {
  transition: transform 220ms cubic-bezier(0.16, 1, 0.3, 1), opacity 180ms ease;
}
.modal-panel-leave-active {
  transition: transform 150ms ease, opacity 150ms ease;
}
.modal-panel-enter-from {
  opacity: 0;
  transform: scale(0.96) translateY(6px);
}
.modal-panel-leave-to {
  opacity: 0;
  transform: scale(0.98);
}
</style>
