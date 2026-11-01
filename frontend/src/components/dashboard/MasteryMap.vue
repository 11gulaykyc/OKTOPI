<script setup>
import { computed } from 'vue'

/**
 * Gelişim Haritası: temalara göre gruplanmış konu kutucukları.
 * Düzey sunucuda hesaplanır; yeterli cevap yoksa "Veri az" gösterilir, kesin tanı gibi sunulmaz.
 */
const props = defineProps({
  map: { type: Object, required: true },
})

const LEVELS = {
  mastered: { label: 'Pekişti', chip: 'bg-aqua-50 text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300', bar: 'bg-aqua-500', tile: 'border-aqua-300 dark:border-aqua-500/40' },
  developing: { label: 'Gelişiyor', chip: 'bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300', bar: 'bg-brand-500', tile: 'border-brand-200 dark:border-brand-500/30' },
  needs_review: { label: 'Tekrar et', chip: 'bg-rose-50 text-wine-600 dark:bg-rose-500/15 dark:text-rose-300', bar: 'bg-wine-500', tile: 'border-rose-300 dark:border-rose-500/40' },
  insufficient: { label: 'Veri az', chip: 'bg-accent-100 text-accent-600 dark:bg-accent-600/20 dark:text-accent-400', bar: 'bg-accent-400', tile: 'border-dashed border-slate-300 dark:border-slate-700' },
  not_started: { label: 'Başlanmadı', chip: 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400', bar: 'bg-slate-300', tile: 'border-slate-200 dark:border-slate-800' },
}
const LEGEND = ['mastered', 'developing', 'needs_review', 'insufficient', 'not_started']

const minAnswers = computed(() => props.map.thresholds.min_answers_for_diagnosis)

function percent(rate) {
  return rate == null ? null : Math.round(rate * 100)
}

/** Kutucuğun altındaki dürüst açıklama. */
function note(t) {
  if (t.level === 'not_started') return t.question_count ? 'Henüz soru çözmedin.' : 'Bu konunun soruları hazırlanıyor.'
  if (t.level === 'insufficient') {
    if (t.question_count < minAnswers.value && t.questions_answered >= t.question_count) {
      return `Havuzdaki ${t.question_count} sorunun hepsini çözdün; kesin analiz için yeni sorular eklenince tekrar bak.`
    }
    return `Analizi netleştirmek için ${t.answers_needed} soru daha çöz.`
  }
  return `${t.correct_answers}/${t.questions_answered} ilk denemede doğru`
}
</script>

<template>
  <div class="space-y-5">
    <ul class="flex flex-wrap gap-2 text-xs font-bold" aria-label="Renk açıklaması">
      <li v-for="key in LEGEND" :key="key" class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1" :class="LEVELS[key].chip">
        {{ LEVELS[key].label }}
        <span class="tabular-nums opacity-70">{{ map.levels[key] }}</span>
      </li>
    </ul>

    <section v-for="theme in map.themes" :key="theme.id">
      <h3 class="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{{ theme.title }}</h3>
      <ul class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <li v-for="t in theme.topics" :key="t.id" class="flex min-w-0 flex-col rounded-xl border bg-white p-3.5 dark:bg-slate-900" :class="LEVELS[t.level].tile">
          <div class="flex items-start justify-between gap-2">
            <RouterLink :to="{ name: 'topic-detail', params: { topicId: t.id } }" class="min-w-0 font-bold leading-snug text-slate-800 hover:text-brand-600 dark:text-slate-100">
              {{ t.title }}
            </RouterLink>
            <span class="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-bold" :class="LEVELS[t.level].chip">{{ LEVELS[t.level].label }}</span>
          </div>

          <div v-if="t.questions_answered" class="mt-3">
            <div class="flex items-baseline justify-between text-xs">
              <span class="font-semibold text-slate-500 dark:text-slate-400">{{ t.enough_data ? 'Başarı' : 'Şimdilik' }}</span>
              <span class="font-bold tabular-nums text-slate-700 dark:text-slate-200">%{{ percent(t.success_rate) }}</span>
            </div>
            <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" role="presentation">
              <div class="h-full rounded-full" :class="[LEVELS[t.level].bar, { 'opacity-50': !t.enough_data }]" :style="{ width: `${percent(t.success_rate)}%` }" />
            </div>
          </div>

          <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">{{ note(t) }}</p>
          <p v-if="t.open_mistakes" class="mt-1 text-xs font-semibold text-wine-600 dark:text-rose-300">
            {{ t.open_mistakes }} düzeltilmemiş yanlış
          </p>
        </li>
      </ul>
    </section>
  </div>
</template>
