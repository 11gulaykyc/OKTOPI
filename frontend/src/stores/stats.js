import { defineStore } from 'pinia'
import { ref } from 'vue'
import api, { errorMessage } from '@/services/api'

export const useStatsStore = defineStore('stats', () => {
  const summary = ref(null)
  const loading = ref(false)
  const error = ref('')
  // Bugünkü aktif çalışma süresi (sn). Her heartbeat yanıtıyla sunucudan güncellenir.
  const todaySeconds = ref(null)
  // Oyunlaştırma özeti: puan/seviye, rozetler, görevler, hedefler
  const gamification = ref(null)

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

  async function fetchGamification() {
    gamification.value = (await api.get('/gamification/summary/')).data
    return gamification.value
  }

  /** Gelişim Haritası: sınıfın tüm konuları için düzey ve tekrar edilmesi gereken alanlar. */
  async function fetchMasteryMap(grade) {
    return (await api.get('/analytics/mastery-map/', { params: { grade } })).data
  }

  /** Kavram yanılgısı örüntüleri ve düzeltilmemiş yanlışlar (cevap anahtarı içermez). */
  async function fetchErrorAnalysis(grade) {
    return (await api.get('/analytics/error-analysis/', { params: { grade } })).data
  }

  async function fetchGoals() {
    return (await api.get('/gamification/goals/')).data
  }

  /** Hedefi günceller. Sunucu eski hedefi kapatır, yenisini açar; geçmiş günler değişmez. */
  async function saveGoal(goalType, target) {
    return (await api.put('/gamification/goals/', { goal_type: goalType, target })).data
  }

  async function clearGoal(goalType) {
    await api.delete(`/gamification/goals/${goalType}/`)
  }

  function reset() {
    summary.value = null
    todaySeconds.value = null
    gamification.value = null
  }

  return {
    summary,
    loading,
    error,
    todaySeconds,
    gamification,
    fetchSummary,
    fetchGamification,
    fetchMasteryMap,
    fetchErrorAnalysis,
    fetchGoals,
    saveGoal,
    clearGoal,
    reset,
  }
})
