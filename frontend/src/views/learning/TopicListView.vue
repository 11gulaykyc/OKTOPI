<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BookOpen, ChevronRight, CircleCheck, Clock3, FileQuestion, LoaderCircle, RotateCcw } from 'lucide-vue-next'
import ThemeTopicPicker from '@/components/learning/ThemeTopicPicker.vue'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useContentStore } from '@/stores/content'
import { useGradeStore } from '@/stores/grade'

const auth = useAuthStore()
const content = useContentStore()
const gradeStore = useGradeStore()
const route = useRoute()
const router = useRouter()

const curriculum = ref(null)
const progress = ref({}) // topic_id -> ilerleme
const loading = ref(false)
const error = ref('')
const onlyWithContent = ref(false)

async function load(grade) {
  loading.value = true
  error.value = ''
  try {
    const [tree, list] = await Promise.all([
      content.fetchGrade(grade),
      auth.isAuthenticated ? api.get('/analytics/topic-progress/', { params: { grade } }) : { data: [] },
    ])
    if (grade !== gradeStore.grade) return // bu arada sınıf değiştiyse eski yanıtı yok say
    curriculum.value = tree
    progress.value = Object.fromEntries(list.data.map((p) => [p.topic_id, p]))
  } catch (e) {
    error.value = errorMessage(e, 'Konular yüklenemedi.')
  } finally {
    loading.value = false
  }
}
watch(() => gradeStore.grade, load, { immediate: true })

const themes = computed(() =>
  (curriculum.value?.themes ?? [])
    .map((theme) => ({
      ...theme,
      topics: theme.topics.filter((t) => !onlyWithContent.value || t.has_content),
    }))
    .filter((theme) => theme.topics.length),
)
const allTopics = computed(() => (curriculum.value?.themes ?? []).flatMap((t) => t.topics))
const completedCount = computed(() => allTopics.value.filter((t) => progress.value[t.id]?.status === 'completed').length)
const contentCount = (theme) => theme.topics.filter((t) => t.has_content).length
const completedIn = (theme) => theme.topics.filter((t) => progress.value[t.id]?.status === 'completed').length

// Seçili tema adreste (?tema=) tutulur; geri tuşu tema listesine döner.
const themeId = computed({
  get: () => (typeof route.query.tema === 'string' ? route.query.tema : ''),
  set: (id) => {
    router.push({ query: { ...route.query, tema: id || undefined } })
    window.scrollTo({ top: 0 })
  },
})

const STATUS = {
  completed: { label: 'Tamamlandı', class: 'bg-aqua-50 text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300', icon: CircleCheck },
  in_progress: { label: 'Devam ediyor', class: 'bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300', icon: Clock3 },
}
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-sm font-bold text-brand-600 dark:text-brand-400">{{ gradeStore.grade }}. Sınıf</p>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">Konular</h1>
        <p v-if="curriculum" class="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {{ curriculum.program }} · {{ allTopics.length }} konu<template v-if="auth.isAuthenticated"> · {{ completedCount }} tamamlandı</template>
        </p>
      </div>
      <label class="inline-flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-300">
        <input v-model="onlyWithContent" type="checkbox" class="h-4 w-4 rounded border-slate-300 accent-brand-600" />
        Yalnızca anlatımı hazır olanlar
      </label>
    </header>

    <div
      v-if="!gradeStore.isOwnGrade && gradeStore.ownGrade"
      class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-accent-400/40 bg-accent-100/60 px-4 py-3 text-sm dark:border-accent-500/30 dark:bg-accent-600/10"
    >
      <span class="font-semibold text-slate-700 dark:text-slate-200">
        {{ gradeStore.grade }}. sınıf içeriklerine göz atıyorsun. Senin sınıfın: {{ gradeStore.ownGrade }}.
      </span>
      <button type="button" class="btn-secondary !py-1.5 text-xs" @click="gradeStore.reset()">
        <RotateCcw class="h-3.5 w-3.5" /> Kendi sınıfıma dön
      </button>
    </div>

    <p v-if="error" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">
      {{ error }}
    </p>

    <div v-if="loading && !curriculum" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Konular yükleniyor…</div>

    <ThemeTopicPicker v-if="curriculum" v-model:theme-id="themeId" :themes="themes">
      <template #theme-meta="{ theme }">
        <span v-if="contentCount(theme)" class="rounded-full bg-aqua-50 px-2 py-0.5 text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300">
          {{ contentCount(theme) }} anlatım hazır
        </span>
        <span v-if="auth.isAuthenticated && completedIn(theme)" class="rounded-full bg-brand-50 px-2 py-0.5 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
          {{ completedIn(theme) }} tamamlandı
        </span>
      </template>

      <template #topic="{ topic, number }">
        <div>
          <RouterLink
            :to="{ name: 'topic-detail', params: { topicId: topic.id } }"
            class="group flex items-center gap-4 px-4 py-3.5 transition hover:bg-brand-50 dark:hover:bg-slate-800 sm:px-5"
          >
            <span class="w-9 shrink-0 text-sm font-bold text-brand-600 dark:text-brand-400">{{ number }}</span>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
                <h3 class="font-bold text-slate-900 group-hover:text-brand-700 dark:text-white dark:group-hover:text-brand-300">{{ topic.title }}</h3>
                <span
                  v-if="STATUS[progress[topic.id]?.status]"
                  class="inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold"
                  :class="STATUS[progress[topic.id].status].class"
                >
                  <component :is="STATUS[progress[topic.id].status].icon" class="h-3 w-3" />
                  {{ STATUS[progress[topic.id].status].label }}
                </span>
              </div>
              <div class="mt-1.5 flex flex-wrap gap-2 text-[11px] font-bold">
                <span
                  class="inline-flex items-center gap-1 rounded-full px-2 py-0.5"
                  :class="topic.has_content ? 'bg-aqua-50 text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'"
                >
                  <BookOpen class="h-3 w-3" /> {{ topic.has_content ? 'Anlatım hazır' : 'Anlatım hazırlanıyor' }}
                </span>
                <span v-if="topic.question_count" class="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                  <FileQuestion class="h-3 w-3" /> {{ topic.question_count }} soru
                </span>
                <span
                  v-if="progress[topic.id]?.success_rate != null"
                  class="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                  :title="`${progress[topic.id].questions_answered} sorudan ${progress[topic.id].correct_answers} doğru (ilk denemeler)`"
                >
                  Başarı %{{ Math.round(progress[topic.id].success_rate * 100) }}
                </span>
              </div>
            </div>
            <ChevronRight class="h-5 w-5 shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-brand-600" aria-hidden="true" />
          </RouterLink>
          <!-- Alt başlığın kendi içindeki konuları: doğrudan anlatımın o bölümüne gider -->
          <ul v-if="topic.subtopics.length" class="space-y-0.5 pb-3 pl-[4.25rem] pr-4 sm:pl-[4.75rem] sm:pr-5">
            <li v-for="sub in topic.subtopics" :key="sub.id">
              <RouterLink
                :to="{ name: 'topic-detail', params: { topicId: topic.id }, query: { bolum: sub.id } }"
                class="group/sub flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-slate-600 transition hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-brand-300"
              >
                <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-slate-300 group-hover/sub:bg-brand-500 dark:bg-slate-600" aria-hidden="true" />
                {{ sub.title }}
              </RouterLink>
            </li>
          </ul>
        </div>
      </template>
    </ThemeTopicPicker>

    <p v-if="curriculum && onlyWithContent && !themes.some((t) => t.topics.length)" class="card p-6 text-center text-sm text-slate-500 dark:text-slate-400">
      Bu sınıf için anlatımı hazır konu henüz yok. Filtreyi kaldırarak konu ağacının tamamını görebilirsin.
    </p>
  </div>
</template>
