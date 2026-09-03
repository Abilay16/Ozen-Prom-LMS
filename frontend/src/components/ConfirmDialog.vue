<template>
  <Teleport to="body">
    <Transition name="confirm-backdrop">
      <div
        v-if="state.visible"
        class="confirm-backdrop"
        @click.self="onCancel"
        @keydown.esc="onCancel"
      >
        <Transition name="confirm-panel" appear>
          <div v-if="state.visible" class="confirm-panel" role="alertdialog" aria-modal="true">
            <h2 v-if="state.title" class="confirm-title">{{ state.title }}</h2>
            <p class="confirm-message">{{ state.message }}</p>
            <div class="confirm-actions">
              <button ref="cancelBtn" class="confirm-btn confirm-btn--cancel" @click="onCancel">
                {{ state.cancelText }}
              </button>
              <button
                class="confirm-btn"
                :class="state.danger ? 'confirm-btn--danger' : 'confirm-btn--primary'"
                @click="onConfirm"
              >
                {{ state.confirmText }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { _useConfirmState } from '@/composables/useConfirm'

const { state, resolve } = _useConfirmState()
const cancelBtn = ref(null)

function onConfirm() { resolve(true) }
function onCancel() { resolve(false) }

// Focus the (safe) cancel button by default when the dialog opens.
watch(() => state.visible, async (visible) => {
  if (visible) {
    await nextTick()
    cancelBtn.value?.focus()
  }
})
</script>

<style scoped>
.confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.confirm-panel {
  width: 100%;
  max-width: 380px;
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.25);
}

.confirm-title {
  font-size: 16px;
  font-weight: 700;
  color: #1F3A5C;
  margin-bottom: 8px;
}

.confirm-message {
  font-size: 14px;
  line-height: 1.55;
  color: #374151;
  white-space: pre-line;
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

.confirm-btn {
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 600;
  transition: transform 120ms ease, opacity 120ms ease, background-color 120ms ease;
}
.confirm-btn:active { transform: scale(0.97); }

.confirm-btn--cancel {
  color: #4b5563;
  background: #f3f4f6;
}
.confirm-btn--cancel:hover { background: #e5e7eb; }

.confirm-btn--primary {
  color: #ffffff;
  background: #1F3A5C;
}
.confirm-btn--primary:hover { opacity: 0.9; }

.confirm-btn--danger {
  color: #ffffff;
  background: #dc2626;
}
.confirm-btn--danger:hover { opacity: 0.9; }

/* Motion — transform + opacity only */
.confirm-backdrop-enter-active,
.confirm-backdrop-leave-active {
  transition: opacity 180ms ease;
}
.confirm-backdrop-enter-from,
.confirm-backdrop-leave-to {
  opacity: 0;
}

.confirm-panel-enter-active {
  transition: transform 220ms cubic-bezier(0.16, 1, 0.3, 1), opacity 180ms ease;
}
.confirm-panel-leave-active {
  transition: transform 150ms ease, opacity 150ms ease;
}
.confirm-panel-enter-from {
  opacity: 0;
  transform: scale(0.96) translateY(6px);
}
.confirm-panel-leave-to {
  opacity: 0;
  transform: scale(0.98);
}
</style>
