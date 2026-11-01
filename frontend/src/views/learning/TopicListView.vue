<script setup>
import { computed, ref, watch } from 'vue'
import { BookOpen, CircleCheck, Clock3, FileQuestion, LoaderCircle, RotateCcw } from 'lucide-vue-next'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useContentStore } from '@/stores/content'
import { useGradeStore } from '@/stores/grade'

const auth = useAuthStore()
const content = useContentStore()
const gradeStore = useGradeStore()

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
  (curriculum.value?.themes ?? []).map((theme) => ({
    ...theme,
    topics: theme.topics.filter((t) => !onlyWithContent.value || t.has_content),
  })),
)
const allTopics = computed(() => (curriculum.value?.themes ?? []).flatMap((t) => t.topics))
const completedCount = computed(() => allTopics.value.filter((t) => progress.value[t.id]?.status === 'completed').length)

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

    <section v-for="theme in themes" v-show="theme.topics.length" :key="theme.id" :aria-labelledby="theme.id">
      <div class="mb-3 flex items-start gap-3">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white">{{ theme.order }}</span>
        <div class="min-w-0">
          <h2 :id="theme.id" class="text-lg font-bold text-slate-900 dark:text-white">{{ theme.title }}</h2>
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ theme.description }}</p>
        </div>
      </div>

      <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <RouterLink
          v-for="topic in theme.topics"
          :key="topic.id"
          :to="{ name: 'topic-detail', params: { topicId: topic.id } }"
          class="card group flex flex-col p-4 transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md dark:hover:border-brand-500/50"
        >
          <div class="flex items-start justify-between gap-2">
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
          <p class="mt-1 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">
            {{ topic.subtopics.map((s) => s.title).join(' · ') }}
          </p>
          <div class="mt-auto flex flex-wrap gap-2 pt-3 text-[11px] font-bold">
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
        </RouterLink>
      </div>
    </section>

    <p v-if="curriculum && onlyWithContent && !themes.some((t) => t.topics.length)" class="card p-6 text-center text-sm text-slate-500 dark:text-slate-400">
      Bu sınıf için anlatımı hazır konu henüz yok. Filtreyi kaldırarak konu ağacının tamamını görebilirsin.
    </p>
  </div>
</template>
