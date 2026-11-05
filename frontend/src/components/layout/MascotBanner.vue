<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import OktopiMascot from './OktopiMascot.vue'
import { getMascot } from '@/assets/mascot'

const props = defineProps({
  mood: { type: String, default: 'welcome' },
  title: { type: String, required: true },
  message: { type: String, default: '' },
  character: { type: String, default: '' },
})

const route = useRoute()
const mascot = computed(() => getMascot(props.character || route?.meta?.mascot))
</script>

<template>
  <section class="rounded-xl bg-brand-800 p-5 text-white sm:px-6 sm:py-5 dark:bg-brand-900">
    <div class="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
      <div class="flex shrink-0 flex-col items-center">
        <OktopiMascot :character="mascot.key" :mood="mood" :size="96" />
        <span class="mt-1 text-xs font-semibold text-brand-100">{{ mascot.name }}</span>
      </div>
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
