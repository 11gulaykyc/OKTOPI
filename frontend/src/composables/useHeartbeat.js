import { onBeforeUnmount, onMounted, ref } from 'vue'
import api from '@/services/api'
import { useRewardStore } from '@/stores/rewards'
import { useStatsStore } from '@/stores/stats'

export const HEARTBEAT_INTERVAL_MS = 60_000
// Son etkileşimden bu yana bu süre geçtiyse kullanıcı "aktif değil" sayılır ve ping atılmaz.
const IDLE_AFTER_MS = 60_000
const ACTIVITY_EVENTS = ['pointerdown', 'pointermove', 'keydown', 'wheel', 'touchstart', 'scroll']

/**
 * Aktif çalışma süresi takibi (CLAUDE.md §4.2).
 *
 * Yalnızca sekme görünürken ve son 60 sn içinde fare/klavye/dokunma etkileşimi olduysa
 * (veya `keepActive()` true dönüyorsa — ör. süreli test ekranı) 60 sn'de bir
 * `/api/study-sessions/heartbeat/` uç noktasına ping atar. Sürenin kendisi sunucuda
 * hesaplanır; 2 dakikayı aşan sessizlikte oturum sunucuda dondurulur.
 *
 * @param {{ context?: () => string, keepActive?: () => boolean }} options
 */
export function useHeartbeat({ context = () => '', keepActive = () => false } = {}) {
  const stats = useStatsStore()
  const rewardStore = useRewardStore()
  const isActive = ref(true)
  const lastPingAt = ref(null)
  const error = ref(false)

  let lastActivityAt = Date.now()
  let timer = null
  let activityThrottle = 0

  function markActivity() {
    const now = Date.now()
    if (now - activityThrottle < 1000) return
    activityThrottle = now
    lastActivityAt = now
    isActive.value = true
  }

  function userIsActive() {
    if (document.visibilityState !== 'visible') return false
    return keepActive() || Date.now() - lastActivityAt < IDLE_AFTER_MS
  }

  async function ping() {
    if (!userIsActive()) {
      isActive.value = false
      return
    }
    isActive.value = true
    try {
      const { data } = await api.post('/study-sessions/heartbeat/', { context: context() })
      stats.todaySeconds = data.today_active_seconds
      // Çalışma süresiyle gelen rozet/hedef/görev ödülleri hangi sayfada olunursa olsun gösterilir.
      rewardStore.push(data.rewards)
      lastPingAt.value = Date.now()
      error.value = false
    } catch {
      error.value = true
    }
  }

  function onVisibilityChange() {
    if (document.visibilityState === 'visible') markActivity()
    else isActive.value = false
  }

  onMounted(() => {
    ACTIVITY_EVENTS.forEach((name) => window.addEventListener(name, markActivity, { passive: true }))
    document.addEventListener('visibilitychange', onVisibilityChange)
    ping()
    timer = window.setInterval(ping, HEARTBEAT_INTERVAL_MS)
  })

  onBeforeUnmount(() => {
    ACTIVITY_EVENTS.forEach((name) => window.removeEventListener(name, markActivity))
    document.removeEventListener('visibilitychange', onVisibilityChange)
    window.clearInterval(timer)
  })

  return { isActive, lastPingAt, error, ping }
}

/** Saniyeyi kısa Türkçe süre metnine çevirir: 45 sn, 12 dk, 1 sa 5 dk. */
export function formatDuration(seconds, { short = false } = {}) {
  const s = Math.max(0, Math.floor(seconds || 0))
  if (s < 60) return short ? `${s} sn` : `${s} saniye`
  const minutes = Math.floor(s / 60)
  if (minutes < 60) return short ? `${minutes} dk` : `${minutes} dakika`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (short) return rest ? `${hours} sa ${rest} dk` : `${hours} sa`
  return rest ? `${hours} saat ${rest} dakika` : `${hours} saat`
}
