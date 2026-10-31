<script setup>
import OktopiMascot from './OktopiMascot.vue'

defineProps({
  mood: { type: String, default: 'welcome' },
  title: { type: String, required: true },
  message: { type: String, default: '' },
})
</script>

<template>
  <section
    class="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 via-brand-700 to-brand-900 p-5 text-white shadow-lg sm:p-7"
  >
    <div class="pointer-events-none absolute -right-10 -top-16 h-56 w-56 rounded-full bg-aqua-400/25 blur-2xl" />
    <div class="pointer-events-none absolute -bottom-20 left-1/3 h-48 w-48 rounded-full bg-accent-500/25 blur-2xl" />
    <div class="relative flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
      <OktopiMascot :mood="mood" :size="112" class="shrink-0 text-slate-900 drop-shadow-xl" />
      <div class="min-w-0 flex-1">
        <h1 class="text-2xl font-extrabold leading-tight sm:text-3xl">{{ title }}</h1>
        <p v-if="message" class="mt-2 text-sm text-brand-100 sm:text-base">{{ message }}</p>
        <div v-if="$slots.default" class="mt-4 flex flex-wrap justify-center gap-2 sm:justify-start">
          <slot />
        </div>
      </div>
    </div>
  </section>
</template>
