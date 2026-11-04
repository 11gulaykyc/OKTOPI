<script setup>
import { ArrowLeft, BookOpen, ChevronRight, PencilLine } from 'lucide-vue-next'
import { useRouteGrade } from '@/composables/useRouteGrade'

/** Sınıf seçildikten sonra öğrencinin ne yapacağını seçtiği ekran. */
const grade = useRouteGrade()

const options = [
  {
    title: 'Konu Anlatımı',
    text: 'Konuyu seç; öğrenme hedefleri, formüller ve adım adım çözümlü örneklerle öğren.',
    icon: BookOpen,
    to: () => ({ name: 'topics' }),
  },
  {
    title: 'Soru Çözümü',
    text: 'Konuyu seç ve soru çöz. İstersen süre ekleyerek sınav temposunda çalış.',
    icon: PencilLine,
    to: () => ({ name: 'practice-topics', params: { grade: grade.value } }),
  },
]
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <RouterLink to="/#sinif-sec" class="btn-ghost !px-2 text-sm"><ArrowLeft class="h-4 w-4" /> Sınıf seçimine dön</RouterLink>

    <header>
      <p class="text-sm font-bold text-brand-600 dark:text-brand-400">{{ grade }}. Sınıf</p>
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">Ne yapmak istersin?</h1>
    </header>

    <div class="grid gap-4 sm:grid-cols-2">
      <RouterLink
        v-for="o in options"
        :key="o.title"
        :to="o.to()"
        class="card group flex flex-col p-6 transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md dark:hover:border-brand-500/50"
      >
        <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-white">
          <component :is="o.icon" class="h-6 w-6" aria-hidden="true" />
        </span>
        <h2 class="mt-4 text-lg font-bold text-slate-900 group-hover:text-brand-700 dark:text-white dark:group-hover:text-brand-300">{{ o.title }}</h2>
        <p class="mt-1 text-sm text-slate-600 dark:text-slate-400">{{ o.text }}</p>
        <span class="mt-4 inline-flex items-center gap-1 text-sm font-bold text-brand-600 dark:text-brand-300">
          Devam et <ChevronRight class="h-4 w-4 transition group-hover:translate-x-0.5" />
        </span>
      </RouterLink>
    </div>
  </div>
</template>
