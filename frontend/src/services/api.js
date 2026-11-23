import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Один общий refresh на все запросы, упавшие с 401 одновременно
// (иначе каждый параллельный запрос обновлял токен сам).
let refreshing = null

function refreshAccessToken() {
  if (!refreshing) {
    const refreshToken = localStorage.getItem('refresh_token')
    refreshing = axios
      .post('/api/v1/auth/refresh', { refresh_token: refreshToken })
      .then(({ data }) => {
        localStorage.setItem('access_token', data.access_token)
        if (data.is_commission !== undefined) localStorage.setItem('is_commission', data.is_commission ? '1' : '0')
        if (data.is_org_viewer !== undefined) localStorage.setItem('is_org_viewer', data.is_org_viewer ? '1' : '0')
        return data.access_token
      })
      .finally(() => { refreshing = null })
  }
  return refreshing
}

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    // 401 от самого входа/обновления — это «неверный логин или пароль»,
    // а не истёкший токен: отдаём ошибку форме, ничего не перезагружаем.
    const isAuthCall = original?.url?.startsWith('/auth/')
    const hasSession = !!localStorage.getItem('refresh_token')

    if (error.response?.status === 401 && original && !original._retry && !isAuthCall && hasSession) {
      original._retry = true
      try {
        const token = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      } catch {
        localStorage.clear()
        if (!window.location.pathname.startsWith('/login')) window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
