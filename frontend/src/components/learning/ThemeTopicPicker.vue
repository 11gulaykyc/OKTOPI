<script setup>
import { computed } from 'vue'
import { ArrowLeft, ChevronRight } from 'lucide-vue-next'

/**
 * İki adımlı konu seçimi: önce tema (ör. "1. Sayılar"), sonra o temanın alt başlıkları (1.1, 1.2 …).
 * İkisi de alt alta satırlardan oluşan bir liste olarak gösterilir.
 * Seçili tema üst bileşende tutulur (adres sorgusu `?tema=`), böylece tarayıcının geri tuşu da çalışır.
 *
 * Slotlar:
 *   theme-meta { theme }          → tema satırının altındaki rozetler
 *   topic      { topic, number }  → alt başlık satırı (bağlantı ya da buton; tıklama davranışı sayfaya ait)
 */
const props = defineProps({
  themes: { type: Array, required: true },
  themeId: { type: String, default: '' },
})
const emit = defineEmits(['update:themeId'])

const selected = computed(() => props.themes.find((t) => t.id === props.themeId) ?? null)
</script>

<template>
  <!-- 1. adım: tema -->
  <ul v-if="!selected" class="divide-y divide-slate-200 overflow-hidden rounded-2xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
    <li v-for="theme in themes" :key="theme.id">
      <button
        type="button"
        class="group flex w-full items-center gap-4 px-4 py-4 text-left transition hover:bg-brand-50 dark:hover:bg-slate-800 sm:px-5"
        @click="emit('update:themeId', theme.id)"
      >
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 font-bold text-white">{{ theme.order }}</span>
        <span class="min-w-0 flex-1">
          <span class="block font-bold text-slate-900 group-hover:text-brand-700 dark:text-white dark:group-hover:text-brand-300">{{ theme.title }}</span>
          <span class="block text-sm text-slate-500 dark:text-slate-400">{{ theme.description }}</span>
          <span class="mt-1.5 flex flex-wrap gap-2 text-[11px] font-bold">
            <span class="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ theme.topics.length }} alt başlık</span>
            <slot name="theme-meta" :theme="theme" />
          </span>
        </span>
        <ChevronRight class="h-5 w-5 shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-brand-600" aria-hidden="true" />
      </button>
    </li>
  </ul>

  <!-- 2. adım: alt başlık -->
  <section v-else :aria-labelledby="`picker-${selected.id}`" class="space-y-4">
    <button type="button" class="btn-ghost !px-2 text-sm" @click="emit('update:themeId', '')">
      <ArrowLeft class="h-4 w-4" /> Tüm temalar
    </button>
    <div class="flex items-start gap-3">
      <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 font-bold text-white">{{ selected.order }}</span>
      <div class="min-w-0">
        <h2 :id="`picker-${selected.id}`" class="text-lg font-bold text-slate-900 dark:text-white">{{ selected.title }}</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">{{ selected.description }}</p>
      </div>
    </div>
    <ul class="divide-y divide-slate-200 overflow-hidden rounded-2xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
      <li v-for="(topic, i) in selected.topics" :key="topic.id">
        <slot name="topic" :topic="topic" :number="`${selected.order}.${i + 1}`" />
      </li>
    </ul>
  </section>
</template>
