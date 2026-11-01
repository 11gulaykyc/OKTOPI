<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Timer } from 'lucide-vue-next'
import { formatDuration, HEARTBEAT_INTERVAL_MS, useHeartbeat } from '@/composables/useHeartbeat'
import { useStatsStore } from '@/stores/stats'

const route = useRoute()
const stats = useStatsStore()

// Bağlam, sunucuda oturumun nerede geçtiğini gösterir: "topic:top-9-exp", "dashboard" ...
const { isActive, lastPingAt, error } = useHeartbeat({
  context: () => (route.params.topicId ? `topic:${route.params.topicId}` : String(route.name || '')),
  keepActive: () => Boolean(route.meta.keepStudyActive),
})

// İki ping arasında gösterge donmasın diye, aktifken son ping'den bu yana geçen süre
// (en fazla bir aralık) yerelde eklenir. Kaydedilen asıl değer her ping'de sunucudan gelir.
const now = ref(Date.now())
let ticker = null
onMounted(() => (ticker = window.setInterval(() => (now.value = Date.now()), 1000)))
onBeforeUnmount(() => window.clearInterval(ticker))

const displaySeconds = computed(() => {
  if (stats.todaySeconds == null) return null
  const pending = isActive.value && lastPingAt.value ? Math.min(now.value - lastPingAt.value, HEARTBEAT_INTERVAL_MS) : 0
  return stats.todaySeconds + Math.floor(pending / 1000)
})

const title = computed(() => {
  if (error.value) return 'Çalışma süresi şu an kaydedilemiyor; bağlantı gelince devam eder.'
  if (!isActive.value) return 'Süre duraklatıldı: etkileşim olmadığı için sayılmıyor.'
  return 'Bugünkü aktif çalışma süren. Yalnızca sayfayla etkileşimdeyken sayılır.'
})
</script>

<template>
  <div
    class="inline-flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-xs font-bold tabular-nums"
    :class="
      isActive && !error
        ? 'border-aqua-300 bg-aqua-50 text-aqua-700 dark:border-aqua-500/40 dark:bg-aqua-500/10 dark:text-aqua-300'
        : 'border-slate-200 bg-slate-100 text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400'
    "
    :title="title"
    role="timer"
    :aria-label="`Bugün aktif çalışma: ${displaySeconds == null ? 'yükleniyor' : formatDuration(displaySeconds)}`"
  >
    <span class="relative flex h-2 w-2" aria-hidden="true">
      <span v-if="isActive && !error" class="absolute inline-flex h-full w-full animate-ping rounded-full bg-aqua-400 opacity-60" />
      <span class="relative inline-flex h-2 w-2 rounded-full" :class="isActive && !error ? 'bg-aqua-500' : 'bg-slate-400'" />
    </span>
    <Timer class="h-3.5 w-3.5" aria-hidden="true" />
    <span>{{ displaySeconds == null ? '—' : formatDuration(displaySeconds, { short: true }) }}</span>
    <span class="hidden xl:inline font-semibold opacity-80">bugün</span>
  </div>
</template>
