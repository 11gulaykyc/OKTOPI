<script setup>
import OktopiMascot from '@/components/layout/OktopiMascot.vue'
import MascotBanner from '@/components/layout/MascotBanner.vue'
import { MASCOT_IMAGES } from '@/assets/mascot'

const moods = [
  { key: 'welcome', label: 'Karşılama', usage: 'Ana sayfa, giriş ekranı' },
  { key: 'happy', label: 'Mutlu', usage: 'Doğru cevap' },
  { key: 'celebrate', label: 'Kutlama', usage: 'Rozet / hedef kazanımı' },
  { key: 'thinking', label: 'Düşünceli', usage: 'İpucu, soru üzerinde düşünme' },
  { key: 'encourage', label: 'Teşvik', usage: 'Zorlanma / yanlış cevap' },
]
</script>

<template>
  <div class="space-y-8">
    <div>
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Maskot Önizleme</h1>
      <p class="text-slate-500 dark:text-slate-400">
        Geliştirme sayfası. Görseli tanımlı olmayan durumlar için yer tutucu SVG gösterilir.
      </p>
    </div>

    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <article v-for="m in moods" :key="m.key" class="card flex flex-col items-center p-5 text-center">
        <OktopiMascot :mood="m.key" :size="150" />
        <h2 class="mt-3 font-bold text-slate-900 dark:text-white">{{ m.label }}</h2>
        <code class="text-xs text-brand-600 dark:text-brand-400">{{ m.key }}</code>
        <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ m.usage }}</p>
        <span
          class="mt-2 rounded-full px-2 py-0.5 text-[10px] font-bold"
          :class="MASCOT_IMAGES[m.key] ? 'bg-aqua-50 text-aqua-700' : 'bg-accent-100 text-accent-600'"
        >
          {{ MASCOT_IMAGES[m.key] ? 'Gerçek görsel' : 'Yer tutucu SVG' }}
        </span>
      </article>
    </div>

    <div class="flex flex-wrap items-end gap-6">
      <OktopiMascot v-for="s in [36, 64, 112, 220]" :key="s" mood="welcome" :size="s" />
    </div>

    <MascotBanner mood="encourage" title="Bu kavramı birlikte tekrar inceleyelim" message="Negatif kuvvet sayıyı ters çevirir, eksi yapmaz. Hadi konu özetine bir göz atalım!" />
  </div>
</template>
