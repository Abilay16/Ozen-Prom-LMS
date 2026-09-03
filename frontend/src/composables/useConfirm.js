import { reactive } from 'vue'

// Single global confirm-dialog state, rendered once by <ConfirmDialog />
// mounted in App.vue. confirm() returns a Promise<boolean>, so call sites
// read almost exactly like the old window.confirm() they replace:
//   const ok = await confirm({ message: 'Удалить пользователя?', danger: true })
//   if (!ok) return
const state = reactive({
  visible: false,
  title: '',
  message: '',
  confirmText: 'Подтвердить',
  cancelText: 'Отмена',
  danger: false,
  resolver: null,
})

function confirm({ title = '', message = '', confirmText = 'Подтвердить', cancelText = 'Отмена', danger = false } = {}) {
  state.title = title
  state.message = message
  state.confirmText = confirmText
  state.cancelText = cancelText
  state.danger = danger
  state.visible = true
  return new Promise((resolve) => {
    state.resolver = resolve
  })
}

function resolve(value) {
  state.visible = false
  if (state.resolver) {
    state.resolver(value)
    state.resolver = null
  }
}

export function useConfirm() {
  return { confirm }
}

// Internal — only <ConfirmDialog /> should use these.
export function _useConfirmState() {
  return { state, resolve }
}
