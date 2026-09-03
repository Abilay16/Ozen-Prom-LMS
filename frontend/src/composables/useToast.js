import { reactive } from 'vue'

// Global toast queue — a plain reactive array shared by every caller of
// useToast(), rendered once by <ToastContainer /> mounted in App.vue.
const toasts = reactive([])
let idCounter = 0

function push(message, type = 'success', duration = 3500) {
  const id = ++idCounter
  toasts.push({ id, message, type })
  if (duration > 0) {
    setTimeout(() => dismiss(id), duration)
  }
  return id
}

function dismiss(id) {
  const idx = toasts.findIndex(t => t.id === id)
  if (idx !== -1) toasts.splice(idx, 1)
}

export function useToast() {
  return {
    toasts,
    success: (message, duration) => push(message, 'success', duration),
    error: (message, duration) => push(message, 'error', duration ?? 5500),
    info: (message, duration) => push(message, 'info', duration),
    dismiss,
  }
}

// Consistent "what went wrong" text out of an Axios error — replaces the
// repeated `e.response?.data?.detail || e.message` pattern at every call site.
export function apiErrorMessage(e, fallback = 'Что-то пошло не так') {
  return e?.response?.data?.detail || e?.message || fallback
}
