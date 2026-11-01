<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
  tone: { type: String, default: 'brand' },
})

const TONES = {
  brand: 'bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300',
  aqua: 'bg-aqua-50 text-aqua-600 dark:bg-aqua-500/15 dark:text-aqua-300',
  accent: 'bg-accent-100 text-accent-600 dark:bg-accent-600/20 dark:text-accent-400',
  wine: 'bg-rose-50 text-wine-600 dark:bg-rose-500/15 dark:text-rose-300',
}
</script>

<template>
  <article class="card flex items-start gap-3 p-4">
    <span v-if="icon" class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl" :class="TONES[tone]">
      <component :is="icon" class="h-5 w-5" aria-hidden="true" />
    </span>
    <div class="min-w-0">
      <p class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{{ label }}</p>
      <p class="mt-0.5 text-2xl font-bold tabular-nums text-slate-900 dark:text-white">{{ value }}</p>
      <p v-if="hint" class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{{ hint }}</p>
      <slot />
    </div>
  </article>
</template>
