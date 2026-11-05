<script setup>
import OktopiMascot from '@/components/layout/OktopiMascot.vue'
import MascotBanner from '@/components/layout/MascotBanner.vue'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import { MASCOTS } from '@/assets/mascot'

const moods = [
  { key: 'welcome', label: 'Karşılama' },
  { key: 'happy', label: 'Mutlu' },
  { key: 'celebrate', label: 'Kutlama' },
  { key: 'thinking', label: 'Düşünceli' },
  { key: 'encourage', label: 'Teşvik' },
]
const sections = {
  navigator: 'Ana sayfa, panel, sınıf ve konu anlatımı, başlangıç testi',
  tenebris: 'Soru çözümü, süreli test, sonuçlar, hata analizi',
  nori: 'OYSS hazırlık, hedefler, profil',
}
</script>

<template>
  <div class="space-y-10">
    <div>
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Maskot Önizleme</h1>
      <p class="text-slate-500 dark:text-slate-400">
        Geliştirme sayfası. Maskot, rotanın <code>meta.mascot</code> alanına göre seçilir.
      </p>
    </div>

    <section v-for="m in MASCOTS" :key="m.key" class="space-y-4">
      <div>
        <h2 class="text-xl font-bold text-slate-900 dark:text-white">{{ m.name }} <span class="text-sm font-medium text-slate-500">· {{ m.title }}</span></h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">{{ sections[m.key] }}</p>
      </div>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <article v-for="mood in moods" :key="mood.key" class="card flex flex-col items-center p-4 text-center">
          <OktopiMascot :character="m.key" :mood="mood.key" :size="130" />
          <h3 class="mt-2 font-semibold text-slate-900 dark:text-white">{{ mood.label }}</h3>
          <code class="text-xs text-brand-600 dark:text-brand-400">{{ mood.key }}</code>
        </article>
      </div>
      <MascotFeedback :character="m.key" state="struggle" />
    </section>

    <div class="flex flex-wrap items-end gap-6">
      <OktopiMascot v-for="s in [36, 64, 112, 220]" :key="s" character="navigator" mood="welcome" :size="s" />
    </div>

    <MascotBanner character="tenebris" mood="encourage" title="Bu kavramı birlikte tekrar inceleyelim" message="Negatif kuvvet sayıyı ters çevirir, eksi yapmaz. Hadi konu özetine bir göz atalım!" />
  </div>
</template>
