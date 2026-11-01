<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { CalendarDays, ChevronDown, CircleHelp, Info, LoaderCircle, NotebookPen, TriangleAlert } from 'lucide-vue-next'
import { errorMessage } from '@/services/api'
import { useContentStore } from '@/stores/content'
import { GRADES, useGradeStore } from '@/stores/grade'
import { formatLongDate } from '@/utils/date'

const contentStore = useContentStore()
const gradeStore = useGradeStore()

const oyss = ref(null)
const error = ref('')
const loading = ref(true)
const selectedGrade = ref(gradeStore.grade)
watch(() => gradeStore.grade, (g) => (selectedGrade.value = g))

onMounted(async () => {
  try {
    oyss.value = await contentStore.fetchOyss()
  } catch (e) {
    error.value = errorMessage(e, 'OYSS bilgileri yüklenemedi.')
  } finally {
    loading.value = false
  }
})

const exams = computed(() =>
  (oyss.value?.calendar ?? [])
    .filter((e) => e.grade === selectedGrade.value)
    .sort((a, b) => a.term - b.term || a.exam_no - b.exam_no),
)
const gradesWithExams = computed(() => new Set((oyss.value?.calendar ?? []).map((e) => e.grade)))

function dateRange(exam) {
  if (!exam.start_date) return 'Tarih henüz açıklanmadı'
  if (!exam.end_date || exam.end_date === exam.start_date) return formatLongDate(exam.start_date)
  return `${formatLongDate(exam.start_date)} – ${formatLongDate(exam.end_date)}`
}
</script>

<template>
  <div v-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Yükleniyor…</div>
  <p v-else-if="!oyss" class="card p-6 text-center font-semibold text-rose-600 dark:text-rose-400">{{ error }}</p>

  <div v-else class="mx-auto max-w-5xl space-y-6">
    <header class="border-b border-slate-200 pb-5 dark:border-slate-800">
      <p class="text-sm font-semibold text-slate-500 dark:text-slate-400">{{ oyss.academic_year }} eğitim-öğretim yılı</p>
      <h1 class="mt-1 text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">{{ oyss.title }}</h1>
      <p class="mt-3 max-w-3xl text-slate-600 dark:text-slate-300">{{ oyss.intro }}</p>
    </header>

    <!-- Hakkında -->
    <section class="card p-5 sm:p-6">
      <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white"><Info class="h-5 w-5 text-brand-500" /> OYSS nasıl işler?</h2>
      <ul class="mt-3 space-y-2">
        <li v-for="(item, i) in oyss.about" :key="i" class="flex gap-3 text-sm text-slate-700 dark:text-slate-200">
          <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-aqua-500" aria-hidden="true" />
          {{ item }}
        </li>
      </ul>
    </section>

    <!-- Takvim -->
    <section class="card p-5 sm:p-6">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white"><CalendarDays class="h-5 w-5 text-brand-500" /> Sınav takvimi</h2>
        <div role="tablist" aria-label="Sınıf" class="inline-flex rounded-xl bg-slate-100 p-0.5 dark:bg-slate-800">
          <button
            v-for="g in GRADES"
            :key="g"
            type="button"
            role="tab"
            :aria-selected="selectedGrade === g"
            class="rounded-[10px] px-3 py-1.5 text-xs font-bold transition"
            :class="selectedGrade === g ? 'bg-white text-brand-700 shadow-sm dark:bg-slate-950 dark:text-brand-300' : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white'"
            @click="selectedGrade = g"
          >
            {{ g }}. Sınıf
          </button>
        </div>
      </div>

      <div
        v-if="!oyss.calendar_is_official"
        class="mt-4 flex gap-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200"
        role="note"
      >
        <TriangleAlert class="h-5 w-5 shrink-0" />
        <p>
          <strong>Tahmini takvim.</strong> Tarihler ve kapsam henüz resmî MEB duyurusuyla doğrulanmadı. Kesin bilgi için okulunun
          ve MEB'in duyurularını takip et.
        </p>
      </div>
      <p v-else-if="oyss.calendar_source" class="mt-3 text-xs text-slate-500">Kaynak: {{ oyss.calendar_source }}</p>

      <ol v-if="exams.length" class="mt-5 space-y-3">
        <li v-for="exam in exams" :key="`${exam.term}-${exam.exam_no}`" class="flex gap-4 rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
          <div class="flex h-14 w-14 shrink-0 flex-col items-center justify-center rounded-2xl bg-brand-600 text-white">
            <span class="text-[10px] font-bold uppercase leading-none">{{ exam.term }}. dönem</span>
            <span class="text-xl font-bold leading-tight">{{ exam.exam_no }}</span>
          </div>
          <div class="min-w-0 flex-1">
            <p class="font-bold text-slate-900 dark:text-white">{{ exam.period_label }}</p>
            <p class="text-sm" :class="exam.start_date ? 'text-slate-600 dark:text-slate-300' : 'italic text-slate-400'">{{ dateRange(exam) }}</p>
            <div v-if="exam.topics.length" class="mt-2 flex flex-wrap gap-1.5">
              <RouterLink
                v-for="t in exam.topics"
                :key="t.id"
                :to="{ name: 'topic-detail', params: { topicId: t.id } }"
                class="rounded-full bg-aqua-50 px-2.5 py-0.5 text-xs font-bold text-aqua-700 hover:bg-aqua-100 dark:bg-aqua-500/15 dark:text-aqua-300"
              >
                {{ t.title }}
              </RouterLink>
            </div>
          </div>
        </li>
      </ol>
      <p v-else class="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
        {{ selectedGrade }}. sınıf için takvim bilgisi henüz eklenmedi.
        <template v-if="gradesWithExams.size">Diğer sınıfların takvimine yukarıdan bakabilirsin.</template>
      </p>
    </section>

    <!-- Hazırlık ipuçları -->
    <section v-if="oyss.preparation_tips.length">
      <h2 class="mb-3 flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white"><NotebookPen class="h-5 w-5 text-brand-500" /> Yazılıya hazırlık</h2>
      <div class="grid gap-3 sm:grid-cols-2">
        <article v-for="(tip, i) in oyss.preparation_tips" :key="tip.title" class="card p-5">
          <span class="text-xs font-bold text-aqua-600 dark:text-aqua-400">İPUCU {{ i + 1 }}</span>
          <h3 class="mt-1 font-bold text-slate-900 dark:text-white">{{ tip.title }}</h3>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{{ tip.body }}</p>
        </article>
      </div>
      <RouterLink to="/konular" class="btn-primary mt-4">Konu anlatımlarıyla çalışmaya başla</RouterLink>
    </section>

    <!-- SSS -->
    <section v-if="oyss.faq.length" class="card divide-y divide-slate-200 dark:divide-slate-800">
      <h2 class="flex items-center gap-2 p-5 text-lg font-bold text-slate-900 dark:text-white"><CircleHelp class="h-5 w-5 text-brand-500" /> Sık sorulan sorular</h2>
      <details v-for="item in oyss.faq" :key="item.question" class="group px-5 py-4">
        <summary class="flex cursor-pointer list-none items-center justify-between gap-3 font-bold text-slate-800 dark:text-slate-100">
          {{ item.question }}
          <ChevronDown class="h-4 w-4 shrink-0 transition group-open:rotate-180" />
        </summary>
        <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">{{ item.answer }}</p>
      </details>
    </section>
  </div>
</template>
