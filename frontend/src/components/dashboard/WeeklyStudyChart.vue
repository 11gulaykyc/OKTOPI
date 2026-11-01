<script setup>
import { computed, ref } from 'vue'
import { formatDuration } from '@/composables/useHeartbeat'

/** Son 7 günün aktif çalışma süresi (tek seri çubuk grafik) + üzerine gelince ayrıntı. */
const props = defineProps({
  days: { type: Array, required: true }, // [{ date, study_seconds, questions, correct }]
})

const DAY_NAMES = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt']
const today = new Date().toDateString()

const rows = computed(() =>
  props.days.map((d) => {
    const date = new Date(`${d.date}T00:00:00`)
    return {
      ...d,
      minutes: Math.round(d.study_seconds / 60),
      short: DAY_NAMES[date.getDay()],
      long: date.toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' }),
      isToday: date.toDateString() === today,
    }
  }),
)

// Eksen üst sınırı "yuvarlak" bir dakika değerine çekilir; veri yoksa 30 dk ölçeği gösterilir.
const maxMinutes = computed(() => {
  const peak = Math.max(0, ...rows.value.map((r) => r.minutes))
  if (!peak) return 30
  const step = peak <= 30 ? 10 : peak <= 120 ? 30 : 60
  return Math.ceil(peak / step) * step
})
const gridLines = computed(() => [1, 0.5].map((f) => Math.round(maxMinutes.value * f)))
const hasData = computed(() => rows.value.some((r) => r.study_seconds > 0))

const hovered = ref(null)
</script>

<template>
  <figure class="relative">
    <div class="relative h-44 pl-9">
      <!-- Izgara çizgileri (geri planda, sessiz) -->
      <div v-for="g in gridLines" :key="g" class="absolute inset-x-0 left-9 border-t border-dashed border-slate-200 dark:border-slate-800" :style="{ bottom: `${(g / maxMinutes) * 100}%` }">
        <span class="absolute -left-9 -top-2 w-8 text-right text-[10px] font-semibold tabular-nums text-slate-400">{{ g }} dk</span>
      </div>
      <div class="absolute inset-x-0 bottom-0 left-9 border-t border-slate-300 dark:border-slate-700" />

      <div class="relative flex h-full items-end gap-0.5">
        <button
          v-for="(r, i) in rows"
          :key="r.date"
          type="button"
          class="group relative flex h-full flex-1 items-end justify-center focus-visible:outline-none"
          :aria-label="`${r.long}: ${formatDuration(r.study_seconds)} çalışma, ${r.questions} soru`"
          @mouseenter="hovered = i"
          @mouseleave="hovered = null"
          @focus="hovered = i"
          @blur="hovered = null"
        >
          <span
            class="block w-full max-w-10 rounded-t-[4px] transition-colors"
            :class="[
              r.study_seconds ? 'bg-brand-600 dark:bg-brand-500' : 'bg-slate-200 dark:bg-slate-800',
              hovered === i ? 'opacity-100' : hovered == null ? '' : 'opacity-60',
              'group-focus-visible:ring-2 group-focus-visible:ring-brand-400 group-focus-visible:ring-offset-2 dark:group-focus-visible:ring-offset-slate-900',
            ]"
            :style="{ height: r.study_seconds ? `max(4px, ${(r.minutes / maxMinutes) * 100}%)` : '2px' }"
          />
          <!-- Tooltip -->
          <span
            v-if="hovered === i"
            class="pointer-events-none absolute bottom-full z-10 mb-2 w-max max-w-44 rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs shadow-lg dark:border-slate-700 dark:bg-slate-900"
            :class="i < 2 ? 'left-0' : i > rows.length - 3 ? 'right-0' : 'left-1/2 -translate-x-1/2'"
            role="tooltip"
          >
            <span class="block font-bold capitalize text-slate-900 dark:text-white">{{ r.long }}</span>
            <span class="block text-slate-600 dark:text-slate-300">Çalışma: <strong class="tabular-nums">{{ formatDuration(r.study_seconds, { short: true }) }}</strong></span>
            <span class="block text-slate-600 dark:text-slate-300">Soru: <strong class="tabular-nums">{{ r.questions }}</strong> ({{ r.correct }} doğru)</span>
          </span>
        </button>
      </div>
    </div>
    <div class="mt-1.5 flex gap-0.5 pl-9" aria-hidden="true">
      <span v-for="r in rows" :key="r.date" class="flex-1 text-center text-[11px] font-bold" :class="r.isToday ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400'">
        {{ r.isToday ? 'Bugün' : r.short }}
      </span>
    </div>
    <figcaption v-if="!hasData" class="absolute inset-x-0 top-14 pl-9 text-center text-sm font-semibold text-slate-400">
      Son 7 günde kayıtlı çalışma yok
    </figcaption>

    <!-- Ekran okuyucular için tablo görünümü -->
    <table class="sr-only">
      <caption>Son 7 günlük aktif çalışma süresi</caption>
      <thead><tr><th>Gün</th><th>Çalışma</th><th>Soru</th><th>Doğru</th></tr></thead>
      <tbody>
        <tr v-for="r in rows" :key="r.date"><td>{{ r.long }}</td><td>{{ formatDuration(r.study_seconds) }}</td><td>{{ r.questions }}</td><td>{{ r.correct }}</td></tr>
      </tbody>
    </table>
  </figure>
</template>
