<script setup>
import OktopiMascot from './OktopiMascot.vue'

/**
 * Henüz içeriği hazırlanmamış bölümler için dürüst "yakında" ekranı.
 * Sahte içerik göstermez; yalnızca bölümde neler olacağını anlatır.
 */
defineProps({
  icon: { type: [Object, Function], required: true },
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, required: true },
  plans: { type: Array, default: () => [] },
  mascot: { type: String, default: '' },
})
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <header class="card flex flex-col items-center gap-6 p-6 sm:flex-row sm:p-8">
      <div class="flex-1 text-center sm:text-left">
        <p v-if="eyebrow" class="text-sm font-bold text-brand-600 dark:text-brand-400">{{ eyebrow }}</p>
        <h1 class="mt-1 flex items-center justify-center gap-2 text-2xl font-bold text-slate-900 dark:text-white sm:justify-start sm:text-3xl">
          <component :is="icon" class="h-7 w-7 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          {{ title }}
        </h1>
        <p class="mt-3 text-slate-600 dark:text-slate-300">{{ description }}</p>
        <span class="mt-4 inline-block rounded-full bg-accent-100 px-3 py-1 text-xs font-bold text-accent-600 dark:bg-accent-600/20 dark:text-accent-400">
          Yakında
        </span>
      </div>
      <OktopiMascot :character="mascot" mood="thinking" :size="140" />
    </header>

    <section v-if="plans.length">
      <h2 class="text-lg font-bold text-slate-900 dark:text-white">Burada neler olacak?</h2>
      <ul class="mt-3 grid gap-3 sm:grid-cols-2">
        <li v-for="p in plans" :key="p.title" class="card p-5">
          <p class="font-semibold text-slate-900 dark:text-white">{{ p.title }}</p>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-400">{{ p.text }}</p>
        </li>
      </ul>
    </section>
  </div>
</template>
