<script setup>
import OktopiMascot from './OktopiMascot.vue'
import ThemeToggle from './ThemeToggle.vue'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  mood: { type: String, default: 'welcome' },
  bubble: { type: String, default: '' },
})
</script>

<template>
  <div class="grid min-h-dvh lg:grid-cols-2">
    <!-- Sol: marka paneli (masaüstü) -->
    <div
      class="relative hidden overflow-hidden bg-gradient-to-br from-brand-700 via-brand-800 to-brand-950 p-10 text-white lg:flex lg:flex-col"
    >
      <div class="absolute -left-20 top-1/3 h-72 w-72 rounded-full bg-aqua-400/20 blur-3xl" />
      <div class="absolute -right-10 bottom-10 h-64 w-64 rounded-full bg-accent-500/25 blur-3xl" />
      <RouterLink to="/" class="relative text-2xl font-extrabold">OKTOP<span class="text-aqua-300">İ</span></RouterLink>
      <div class="relative m-auto flex flex-col items-center text-center">
        <div v-if="bubble" class="mb-4 max-w-xs rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-brand-900 shadow-lg">
          {{ bubble }}
        </div>
        <OktopiMascot :mood="mood" :size="220" class="drop-shadow-2xl" />
        <p class="mt-6 max-w-sm text-brand-100">
          9–12. sınıf matematiğini kendi hızında öğren, hatalarından ders çıkar, ilerlemeni gör.
        </p>
      </div>
    </div>

    <!-- Sağ: form -->
    <div class="flex flex-col px-4 py-6 sm:px-8">
      <div class="flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2 lg:invisible">
          <OktopiMascot mood="happy" :size="36" />
          <span class="text-xl font-extrabold text-brand-800 dark:text-brand-300">OKTOP<span class="text-aqua-500">İ</span></span>
        </RouterLink>
        <ThemeToggle />
      </div>
      <div class="mx-auto my-auto w-full max-w-md py-8">
        <h1 class="text-2xl font-extrabold text-slate-900 dark:text-white sm:text-3xl">{{ title }}</h1>
        <p v-if="subtitle" class="mt-1.5 text-slate-500 dark:text-slate-400">{{ subtitle }}</p>
        <div class="mt-6">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>
