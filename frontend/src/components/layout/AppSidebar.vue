<script setup>
import { BookOpen, CalendarCheck, ChartColumn, House, PencilLine, Target, TriangleAlert, UserRound, X } from 'lucide-vue-next'

defineProps({ open: { type: Boolean, default: false } })
defineEmits(['close'])

// `to` olmayan bağlantılar sonraki fazlarda etkinleşecek ekranlardır.
const sections = [
  {
    title: 'Genel',
    items: [
      { label: 'Ana Sayfa', icon: House, to: '/' },
      { label: 'Öğrenci Paneli', icon: ChartColumn, soon: true },
    ],
  },
  {
    title: 'Öğren',
    items: [
      { label: 'Konular', icon: BookOpen, soon: true },
      { label: 'OYSS Hazırlık', icon: CalendarCheck, soon: true },
    ],
  },
  {
    title: 'Pratik',
    items: [
      { label: 'Soru Çöz & Test', icon: PencilLine, soon: true },
      { label: 'Hata Analizi', icon: TriangleAlert, soon: true },
      { label: 'Hedeflerim', icon: Target, soon: true },
    ],
  },
  {
    title: 'Hesap',
    items: [{ label: 'Profilim', icon: UserRound, to: '/profil' }],
  },
]
</script>

<template>
  <!-- Mobil karartma -->
  <div v-if="open" class="fixed inset-0 z-30 bg-slate-950/40 lg:hidden" aria-hidden="true" @click="$emit('close')" />

  <aside
    class="fixed inset-y-0 left-0 z-40 w-64 -translate-x-full border-r border-slate-200 bg-white p-4 transition-transform dark:border-slate-800 dark:bg-slate-900 lg:sticky lg:top-16 lg:z-0 lg:h-[calc(100dvh-4rem)] lg:translate-x-0"
    :class="{ 'translate-x-0': open }"
    aria-label="Ana menü"
  >
    <div class="mb-4 flex items-center justify-between lg:hidden">
      <span class="font-extrabold text-brand-800 dark:text-brand-300">Menü</span>
      <button type="button" class="btn-ghost !p-2" aria-label="Menüyü kapat" @click="$emit('close')">
        <X class="h-5 w-5" />
      </button>
    </div>

    <nav class="space-y-5 overflow-y-auto">
      <div v-for="section in sections" :key="section.title">
        <p class="mb-1.5 px-3 text-xs font-bold uppercase tracking-wider text-slate-400">{{ section.title }}</p>
        <ul class="space-y-0.5">
          <li v-for="item in section.items" :key="item.label">
            <RouterLink
              v-if="item.to"
              :to="item.to"
              class="flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-slate-800"
              exact-active-class="!bg-brand-600 !text-white"
              @click="$emit('close')"
            >
              <component :is="item.icon" class="h-[18px] w-[18px]" />
              {{ item.label }}
            </RouterLink>
            <span
              v-else
              class="flex cursor-not-allowed items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold text-slate-400 dark:text-slate-500"
              title="Sonraki geliştirme aşamasında açılacak"
            >
              <component :is="item.icon" class="h-[18px] w-[18px]" />
              {{ item.label }}
              <span class="ml-auto rounded-full bg-accent-100 px-2 py-0.5 text-[10px] font-bold text-accent-600 dark:bg-accent-600/20 dark:text-accent-400">
                Yakında
              </span>
            </span>
          </li>
        </ul>
      </div>
    </nav>
  </aside>
</template>
