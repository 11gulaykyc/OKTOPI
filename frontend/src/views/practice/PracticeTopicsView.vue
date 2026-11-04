<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, FileQuestion, Lock, LoaderCircle, Play, Shuffle, Timer } from 'lucide-vue-next'
import ThemeTopicPicker from '@/components/learning/ThemeTopicPicker.vue'
import { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useContentStore } from '@/stores/content'
import { useExamStore } from '@/stores/exam'
import { useRouteGrade } from '@/composables/useRouteGrade'

/**
 * Soru çözümü için tema → alt başlık seçimi. Alt başlığa tıklamak oturumu hemen başlatır:
 * "Süre ekle" açıksa süreli test, kapalıysa serbest soru çözümü. Ayarlı başlatma (zorluk,
 * soru sayısı, süre) için eski kurulum ekranları /soru-coz ve /sureli-test adreslerinde duruyor.
 */
const QUESTION_COUNT = 10

const grade = useRouteGrade()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const content = useContentStore()
const exam = useExamStore()

const curriculum = ref(null)
const loading = ref(false)
const starting = ref('') // başlatılan konu kimliği ('*' = karışık)
const error = ref('')
const timed = ref(route.query.sure === '1')

watch(
  grade,
  async (g) => {
    loading.value = true
    error.value = ''
    try {
      const tree = await content.fetchGrade(g)
      if (g === grade.value) curriculum.value = tree
    } catch (e) {
      error.value = errorMessage(e, 'Konular yüklenemedi.')
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

const themes = computed(() => curriculum.value?.themes ?? [])
const totalQuestions = computed(() => themes.value.flatMap((t) => t.topics).reduce((sum, t) => sum + t.question_count, 0))
const questionsIn = (theme) => theme.topics.reduce((sum, t) => sum + t.question_count, 0)

const themeId = computed({
  get: () => (typeof route.query.tema === 'string' ? route.query.tema : ''),
  set: (id) => {
    router.push({ query: { ...route.query, tema: id || undefined } })
    window.scrollTo({ top: 0 })
  },
})
// Süre tercihi de adreste: girişten dönünce ya da geri gelince kaybolmasın.
watch(timed, (on) => router.replace({ query: { ...route.query, sure: on ? '1' : undefined } }))

async function start(topic) {
  if (starting.value) return
  if (!auth.isAuthenticated) {
    router.push({ name: 'login', query: { next: route.fullPath } })
    return
  }
  starting.value = topic?.id ?? '*'
  error.value = ''
  const available = topic ? topic.question_count : totalQuestions.value
  const payload = { grade: grade.value, topic_id: topic?.id ?? '', count: Math.min(QUESTION_COUNT, available) }
  try {
    if (timed.value) {
      const data = await exam.startTimed(payload)
      router.push({ name: 'timed-session', params: { sessionId: data.id } })
    } else {
      const data = await exam.startPractice(payload)
      router.push({ name: 'practice-session', params: { sessionId: data.id } })
    }
  } catch (e) {
    error.value = errorMessage(e, 'Oturum başlatılamadı.')
    starting.value = ''
  }
}
</script>

<template>
  <div class="space-y-6">
    <RouterLink :to="{ name: 'grade-hub', params: { grade } }" class="btn-ghost !px-2 text-sm"><ArrowLeft class="h-4 w-4" /> Geri</RouterLink>

    <header class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-sm font-bold text-brand-600 dark:text-brand-400">{{ grade }}. Sınıf</p>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">Soru Çözümü</h1>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {{ themeId ? 'Alt başlığa tıkla, sorular hemen başlasın.' : 'Önce temayı, sonra alt başlığı seç.' }}
        </p>
      </div>

      <label
        class="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm has-[:checked]:border-brand-500 has-[:checked]:bg-brand-50 dark:border-slate-700 dark:bg-slate-900 dark:has-[:checked]:bg-brand-500/10"
      >
        <input v-model="timed" type="checkbox" class="h-4 w-4 accent-brand-600" />
        <Timer class="h-4 w-4 text-brand-600 dark:text-brand-300" aria-hidden="true" />
        <span>
          <span class="block font-bold text-slate-800 dark:text-slate-100">Süre ekle</span>
          <span class="text-xs text-slate-500 dark:text-slate-400">{{ timed ? 'Soru başına 1,5 dk, sonuçlar test bitince' : 'Süresiz, her cevaptan sonra çözüm' }}</span>
        </span>
      </label>
    </header>

    <p v-if="!auth.isAuthenticated" class="flex items-center gap-2 rounded-xl bg-accent-100/60 px-4 py-3 text-sm font-semibold text-slate-700 dark:bg-accent-600/10 dark:text-slate-200">
      <Lock class="h-4 w-4 shrink-0" /> Soru çözmek için giriş yapman gerekiyor; alt başlığa tıkladığında giriş sayfasına yönlendirileceksin.
    </p>

    <p v-if="error" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">{{ error }}</p>
    <div v-if="loading && !curriculum" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Konular yükleniyor…</div>

    <template v-if="curriculum">
      <div v-if="!totalQuestions" class="card p-6 text-center text-sm text-slate-500 dark:text-slate-400">
        {{ grade }}. sınıf için soru havuzu henüz hazırlanıyor. Üst bardan başka bir sınıf seçebilirsin.
      </div>

      <template v-else>
        <button
          v-if="!themeId"
          type="button"
          class="card group flex w-full items-center gap-3 p-4 text-left transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md disabled:opacity-60 dark:hover:border-brand-500/50"
          :disabled="!!starting"
          @click="start(null)"
        >
          <LoaderCircle v-if="starting === '*'" class="h-5 w-5 animate-spin text-brand-600" />
          <Shuffle v-else class="h-5 w-5 text-brand-600 dark:text-brand-300" aria-hidden="true" />
          <span class="font-bold text-slate-900 group-hover:text-brand-700 dark:text-white dark:group-hover:text-brand-300">Tüm konulardan karışık</span>
          <span class="ml-auto rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">{{ totalQuestions }} soru</span>
        </button>

        <ThemeTopicPicker v-model:theme-id="themeId" :themes="themes">
          <template #theme-meta="{ theme }">
            <span
              class="rounded-full px-2 py-0.5"
              :class="questionsIn(theme) ? 'bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'"
            >
              {{ questionsIn(theme) ? `${questionsIn(theme)} soru` : 'Sorular hazırlanıyor' }}
            </span>
          </template>

          <template #topic="{ topic, number }">
            <button
              v-if="topic.question_count"
              type="button"
              class="group flex w-full items-center gap-4 px-4 py-3.5 text-left transition hover:bg-brand-50 disabled:opacity-60 dark:hover:bg-slate-800 sm:px-5"
              :disabled="!!starting"
              @click="start(topic)"
            >
              <span class="w-9 shrink-0 text-sm font-bold text-brand-600 dark:text-brand-400">{{ number }}</span>
              <span class="min-w-0 flex-1">
                <span class="block font-bold text-slate-900 group-hover:text-brand-700 dark:text-white dark:group-hover:text-brand-300">{{ topic.title }}</span>
                <span class="mt-1.5 inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                  <FileQuestion class="h-3 w-3" /> {{ topic.question_count }} soru
                </span>
              </span>
              <span class="inline-flex shrink-0 items-center gap-1 text-sm font-bold text-brand-600 dark:text-brand-300">
                <LoaderCircle v-if="starting === topic.id" class="h-4 w-4 animate-spin" />
                <template v-else><Play class="h-4 w-4" /> <span class="hidden sm:inline">{{ timed ? 'Süreli başla' : 'Başla' }}</span></template>
              </span>
            </button>
            <div v-else class="flex items-center gap-4 px-4 py-3.5 opacity-60 sm:px-5" aria-disabled="true">
              <span class="w-9 shrink-0 text-sm font-bold text-slate-500">{{ number }}</span>
              <div class="min-w-0 flex-1">
                <h3 class="font-bold text-slate-700 dark:text-slate-300">{{ topic.title }}</h3>
                <span class="mt-1.5 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-500 dark:bg-slate-800 dark:text-slate-400">Sorular hazırlanıyor</span>
              </div>
            </div>
          </template>
        </ThemeTopicPicker>
      </template>
    </template>
  </div>
</template>
