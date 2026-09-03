<template>
  <Teleport to="body">
    <div class="toast-stack" role="status" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="toast-item"
          :class="`toast-item--${t.type}`"
          @click="dismiss(t.id)"
        >
          <span class="toast-icon">
            <svg v-if="t.type === 'success'" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4l2.8 2.8 6.8-6.8a1 1 0 0 1 1.4 0Z" clip-rule="evenodd"/></svg>
            <svg v-else-if="t.type === 'error'" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm-1-9a1 1 0 1 1 2 0v3a1 1 0 1 1-2 0V9Zm1-4a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z" clip-rule="evenodd"/></svg>
            <svg v-else viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10A8 8 0 1 1 2 10a8 8 0 0 1 16 0Zm-7-4a1 1 0 1 1-2 0 1 1 0 0 1 2 0ZM9 9a1 1 0 0 0 0 2h.01a1 1 0 0 0 0-2H9Zm0 3a1 1 0 1 0 0 2h1a1 1 0 1 0 0-2h-1Z" clip-rule="evenodd"/></svg>
          </span>
          <span class="toast-message">{{ t.message }}</span>
          <button class="toast-close" aria-label="Закрыть" @click.stop="dismiss(t.id)">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToast } from '@/composables/useToast'

const { toasts, dismiss } = useToast()
</script>

<style scoped>
.toast-stack {
  position: fixed;
  z-index: 9999;
  right: 16px;
  bottom: 16px;
  display: flex;
  flex-direction: column-reverse;
  gap: 8px;
  max-width: min(380px, calc(100vw - 32px));
}

.toast-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.12), 0 1px 3px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(15, 23, 42, 0.06);
  cursor: pointer;
  font-size: 13.5px;
  line-height: 1.45;
  color: #1F3A5C;
}

.toast-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  margin-top: 1px;
}
.toast-item--success .toast-icon { color: #16a34a; }
.toast-item--error .toast-icon { color: #dc2626; }
.toast-item--info .toast-icon { color: #2563eb; }

.toast-message {
  flex: 1;
  word-break: break-word;
  white-space: pre-line;
}

.toast-close {
  flex-shrink: 0;
  color: #9ca3af;
  font-size: 11px;
  line-height: 1;
  padding: 2px;
  margin: -2px;
  border-radius: 4px;
}
.toast-close:hover { color: #4b5563; background: rgba(0,0,0,0.04); }

/* Motion: transform + opacity only, no layout-triggering props */
.toast-enter-active,
.toast-leave-active {
  transition: transform 260ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(24px);
}
.toast-leave-active {
  position: absolute;
  width: calc(min(380px, 100vw - 32px) - 2px);
}
</style>
