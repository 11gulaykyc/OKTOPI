import { defineStore } from 'pinia'
import { ref } from 'vue'
import api, { errorMessage } from '@/services/api'

export const useStatsStore = defineStore('stats', () => {
  const summary = ref(null)
  const loading = ref(false)
  const error = ref('')
  // Bugünkü aktif çalışma süresi (sn). Her heartbeat yanıtıyla sunucudan güncellenir.
  const todaySeconds = ref(null)

  async function fetchSummary() {
    loading.value = true
    error.value = ''
    try {
      summary.value = (await api.get('/analytics/dashboard-summary/')).data
      todaySeconds.value = Math.max(todaySeconds.value ?? 0, summary.value.study.today_seconds)
    } catch (e) {
      error.value = errorMessage(e, 'Panel verileri yüklenemedi.')
    } finally {
      loading.value = false
    }
  }

  function reset() {
    summary.value = null
    todaySeconds.value = null
  }

  return { summary, loading, error, todaySeconds, fetchSummary, reset }
})
