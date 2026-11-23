import { ref, computed } from 'vue'
import api from '@/services/api'
import { useToast, apiErrorMessage } from '@/composables/useToast'

/**
 * Список с постраничной подгрузкой. Сервер отдаёт массив и общее количество
 * в заголовке X-Total-Count. Раньше списки молча обрезались на 50/500.
 *
 *   const list = usePagedList('/admin/certificates', () => ({ search: search.value }))
 *   list.reload()   — первая страница (при смене фильтров)
 *   list.loadMore() — следующая страница
 */
export function usePagedList(url, paramsFn = () => ({}), { pageSize = 50 } = {}) {
  const toast = useToast()
  const items = ref([])
  const total = ref(0)
  const loading = ref(false)
  const loadingMore = ref(false)
  let requestId = 0

  const hasMore = computed(() => items.value.length < total.value)

  function cleanParams() {
    return Object.fromEntries(Object.entries(paramsFn() || {}).filter(([, v]) => v !== '' && v != null))
  }

  async function fetchPage(skip) {
    const res = await api.get(url, { params: { ...cleanParams(), skip, limit: pageSize } })
    const count = Number(res.headers?.['x-total-count'])
    return { rows: res.data, total: Number.isFinite(count) ? count : res.data.length }
  }

  async function reload() {
    const id = ++requestId
    loading.value = true
    try {
      const page = await fetchPage(0)
      if (id !== requestId) return // ответ на устаревший фильтр
      items.value = page.rows
      total.value = page.total
    } catch (e) {
      if (id === requestId) toast.error(apiErrorMessage(e))
    } finally {
      if (id === requestId) loading.value = false
    }
  }

  async function loadMore() {
    if (loadingMore.value || !hasMore.value) return
    const id = requestId
    loadingMore.value = true
    try {
      const page = await fetchPage(items.value.length)
      if (id !== requestId) return
      items.value = items.value.concat(page.rows)
      total.value = page.total
    } catch (e) {
      toast.error(apiErrorMessage(e))
    } finally {
      loadingMore.value = false
    }
  }

  return { items, total, loading, loadingMore, hasMore, reload, loadMore }
}
