<script setup>
import { onBeforeUnmount, watch } from 'vue'
import { X } from 'lucide-vue-next'
import RewardNotice from '@/components/dashboard/RewardNotice.vue'
import { useRewardStore } from '@/stores/rewards'

// Kuyruktaki ödülü köşede gösterir; 8 sn sonra veya kapatılınca sıradakine geçer.
const store = useRewardStore()
const VISIBLE_MS = 8000
let timer = null

watch(
  () => store.current?.id,
  (id) => {
    window.clearTimeout(timer)
    if (id) timer = window.setTimeout(() => store.dismiss(), VISIBLE_MS)
  },
  { immediate: true },
)
onBeforeUnmount(() => window.clearTimeout(timer))
</script>

<template>
  <div class="pointer-events-none fixed inset-x-4 bottom-4 z-50 flex justify-end sm:inset-x-auto sm:right-6 sm:w-96" aria-live="polite">
    <Transition
      enter-from-class="translate-y-4 opacity-0"
      enter-active-class="transition duration-300"
      leave-to-class="translate-y-4 opacity-0"
      leave-active-class="transition duration-200"
    >
      <div v-if="store.current" :key="store.current.id" class="pointer-events-auto relative w-full rounded-2xl bg-white shadow-xl dark:bg-slate-900">
        <RewardNotice :rewards="store.current.rewards" compact />
        <button
          type="button"
          class="absolute right-2 top-2 rounded-lg p-1 text-slate-500 hover:bg-slate-900/5 dark:text-slate-400 dark:hover:bg-white/10"
          aria-label="Bildirimi kapat"
          @click="store.dismiss()"
        >
          <X class="h-4 w-4" />
        </button>
      </div>
    </Transition>
  </div>
</template>
