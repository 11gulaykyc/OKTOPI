<script setup>
import { computed } from 'vue'

/** Doğru / yanlış / boş dağılımı: tek yığılmış çubuk + her zaman görünen lejant ve sayılar. */
const props = defineProps({
  correct: { type: Number, default: 0 },
  incorrect: { type: Number, default: 0 },
  blank: { type: Number, default: 0 },
})

// Renkler doğrulanmış paletten (açık/koyu ayrı adımlar): turkuaz-600, gül-600/500, mor-600/500.
const segments = computed(() => {
  const total = props.correct + props.incorrect + props.blank
  return [
    { key: 'correct', label: 'Doğru', value: props.correct, color: 'bg-aqua-600' },
    { key: 'incorrect', label: 'Yanlış', value: props.incorrect, color: 'bg-rose-600 dark:bg-rose-500' },
    { key: 'blank', label: 'Boş', value: props.blank, color: 'bg-accent-600 dark:bg-accent-500' },
  ].map((s) => ({ ...s, share: total ? s.value / total : 0 }))
})
const total = computed(() => props.correct + props.incorrect + props.blank)
</script>

<template>
  <div>
    <div
      v-if="total"
      class="flex h-3 gap-0.5 overflow-hidden rounded-full"
      role="img"
      :aria-label="segments.map((s) => `${s.label} ${s.value}`).join(', ')"
    >
      <span
        v-for="s in segments.filter((x) => x.value)"
        :key="s.key"
        :class="s.color"
        :style="{ width: `${s.share * 100}%` }"
        :title="`${s.label}: ${s.value} (%${Math.round(s.share * 100)})`"
      />
    </div>
    <div v-else class="h-3 rounded-full bg-slate-200 dark:bg-slate-800" />

    <ul class="mt-3 grid grid-cols-3 gap-2">
      <li v-for="s in segments" :key="s.key" class="min-w-0">
        <span class="flex items-center gap-1.5 text-xs font-bold text-slate-500 dark:text-slate-400">
          <span class="h-2.5 w-2.5 shrink-0 rounded-sm" :class="s.color" aria-hidden="true" /> {{ s.label }}
        </span>
        <span class="text-lg font-bold tabular-nums text-slate-900 dark:text-white">{{ s.value }}</span>
        <span v-if="total" class="ml-1 text-xs font-semibold tabular-nums text-slate-400">%{{ Math.round(s.share * 100) }}</span>
      </li>
    </ul>
  </div>
</template>
