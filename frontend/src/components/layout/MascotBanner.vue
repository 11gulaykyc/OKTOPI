<script setup>
import OktopiMascot from './OktopiMascot.vue'

defineProps({
  mood: { type: String, default: 'welcome' },
  title: { type: String, required: true },
  message: { type: String, default: '' },
})
</script>

<template>
  <section class="rounded-xl bg-brand-800 p-5 text-white sm:px-6 sm:py-5 dark:bg-brand-900">
    <div class="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
      <OktopiMascot :mood="mood" :size="88" class="shrink-0 text-slate-900" />
      <div class="min-w-0 flex-1">
        <h1 class="text-2xl font-bold leading-tight">{{ title }}</h1>
        <p v-if="message" class="mt-2 text-sm text-brand-100 sm:text-base">{{ message }}</p>
        <div v-if="$slots.default" class="mt-4 flex flex-wrap justify-center gap-2 sm:justify-start">
          <slot />
        </div>
      </div>
    </div>
  </section>
</template>
