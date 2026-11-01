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
    <div class="hidden bg-brand-800 p-10 text-white lg:flex lg:flex-col dark:bg-brand-950">
      <RouterLink to="/" class="text-2xl font-bold">OKTOP<span class="text-aqua-300">İ</span></RouterLink>
      <div class="m-auto flex flex-col items-center text-center">
        <p v-if="bubble" class="mb-4 max-w-xs text-sm text-brand-100">{{ bubble }}</p>
        <OktopiMascot :mood="mood" :size="200" />
        <p class="mt-6 max-w-sm text-brand-100">9–12. sınıf matematik: konu anlatımı, soru çözümü ve hata analizi.</p>
      </div>
    </div>

    <!-- Sağ: form -->
    <div class="flex flex-col px-4 py-6 sm:px-8">
      <div class="flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2 lg:invisible">
          <OktopiMascot mood="happy" :size="36" />
          <span class="text-xl font-bold text-brand-800 dark:text-brand-300">OKTOP<span class="text-aqua-500">İ</span></span>
        </RouterLink>
        <ThemeToggle />
      </div>
      <div class="mx-auto my-auto w-full max-w-md py-8">
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">{{ title }}</h1>
        <p v-if="subtitle" class="mt-1.5 text-slate-500 dark:text-slate-400">{{ subtitle }}</p>
        <div class="mt-6">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>
