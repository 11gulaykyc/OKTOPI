<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Crosshair, Flag, LoaderCircle, PencilLine, SkipForward, Timer } from 'lucide-vue-next'
import RewardNotice from '@/components/dashboard/RewardNotice.vue'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import KatexRenderer from '@/components/math/KatexRenderer.vue'
import QuestionCard from '@/components/practice/QuestionCard.vue'
import SessionSetup from '@/components/practice/SessionSetup.vue'
import { errorMessage } from '@/services/api'
import { useExamStore } from '@/stores/exam'

const route = useRoute()
const router = useRouter()
const exam = useExamStore()

const session = ref(null)
const answers = ref({}) // soru_id -> sunucu değerlendirmesi
const rewards = ref({}) // soru_id -> o cevapla kazanılan ödüller
const currentIndex = ref(0)
const selected = ref('')
const loading = ref(false)
const submitting = ref(false)
const finishing = ref(false)
const error = ref('')

const sessionId = computed(() => route.params.sessionId)
const questions = computed(() => session.value?.questions ?? [])
const current = computed(() => questions.value[currentIndex.value])
const currentResult = computed(() => (current.value ? answers.value[current.value.id] : null))
const answeredCount = computed(() => Object.keys(answers.value).length)
const correctCount = computed(() => Object.values(answers.value).filter((a) => a.is_correct).length)
const allAnswered = computed(() => questions.value.length > 0 && answeredCount.value === questions.value.length)

function firstUnanswered(from = 0) {
  const list = questions.value
  for (let i = 0; i < list.length; i++) {
    const idx = (from + i) % list.length
    if (!answers.value[list[idx].id]) return idx
  }
  return -1
}

async function load(id) {
  error.value = ''
  session.value = null
  answers.value = {}
  rewards.value = {}
  if (!id) return
  loading.value = true
  try {
    const data = await exam.fetchSession('practice', id)
    if (data.is_finished) {
      router.replace({ name: 'exam-result', params: { type: 'practice', sessionId: id } })
      return
    }
    session.value = data
    answers.value = { ...data.answers }
    currentIndex.value = Math.max(firstUnanswered(), 0)
    selected.value = ''
  } catch (e) {
    error.value = errorMessage(e, 'Oturum yüklenemedi.')
  } finally {
    loading.value = false
  }
}
watch(sessionId, load, { immediate: true })

async function start(payload) {
  loading.value = true
  error.value = ''
  try {
    const data = await exam.startPractice(payload)
    router.push({ name: 'practice-session', params: { sessionId: data.id } })
  } catch (e) {
    error.value = errorMessage(e, 'Oturum başlatılamadı.')
    loading.value = false
  }
}

async function check() {
  if (!selected.value || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    const data = await exam.submitAnswer('practice', session.value.id, current.value.id, selected.value)
    answers.value = { ...answers.value, [current.value.id]: data }
    rewards.value = { ...rewards.value, [current.value.id]: data.rewards }
  } catch (e) {
    error.value = errorMessage(e, 'Cevabın kontrol edilemedi. Tekrar dene.')
  } finally {
    submitting.value = false
  }
}

function goTo(index) {
  currentIndex.value = index
  selected.value = ''
  error.value = ''
}

function next() {
  const idx = firstUnanswered(currentIndex.value + 1)
  if (idx >= 0) goTo(idx)
}

async function finish() {
  if (!allAnswered.value && !window.confirm(`${questions.value.length - answeredCount.value} soru cevapsız. Yine de bitirmek istiyor musun?`)) return
  finishing.value = true
  try {
    await exam.finish('practice', session.value.id)
    router.push({ name: 'exam-result', params: { type: 'practice', sessionId: session.value.id } })
  } catch (e) {
    error.value = errorMessage(e, 'Oturum bitirilemedi.')
  } finally {
    finishing.value = false
  }
}

function recommendationLink(rec) {
  return { name: 'topic-detail', params: { topicId: rec.topic_id }, query: rec.section_id ? { bolum: rec.section_id } : {} }
}

function pillClass(q, i) {
  const a = answers.value[q.id]
  const base = i === currentIndex.value ? 'ring-2 ring-brand-500 ring-offset-1 dark:ring-offset-slate-900 ' : ''
  if (!a) return base + 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
  return base + (a.is_correct ? 'bg-aqua-600 text-white' : 'bg-rose-600 text-white')
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <!-- Kurulum -->
    <template v-if="!sessionId">
      <header>
        <h1 class="flex items-center gap-2 text-2xl font-bold text-slate-900 dark:text-white"><PencilLine class="h-6 w-6 text-brand-500" /> Soru Çöz</h1>
        <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Süre yok, acele yok. Her cevaptan sonra doğru şıkkı ve adım adım çözümü hemen görürsün.
        </p>
      </header>
      <p v-if="error" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">{{ error }}</p>
      <SessionSetup
        mode="practice"
        :loading="loading"
        :initial-topic="typeof route.query.konu === 'string' ? route.query.konu : ''"
        :initial-mistakes="route.query.hata === '1'"
        @start="start"
      />
      <RouterLink to="/sureli-test" class="card flex items-center gap-3 p-4 text-sm transition hover:border-brand-300">
        <Timer class="h-5 w-5 shrink-0 text-wine-600" />
        <span class="flex-1"><span class="font-bold text-slate-800 dark:text-slate-100">Kendini sınamak mı istiyorsun?</span> Süreli testte sonuçları test bitince görürsün.</span>
        <ArrowRight class="h-4 w-4 text-slate-400" />
      </RouterLink>
    </template>

    <div v-else-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Sorular yükleniyor…</div>

    <div v-else-if="!session" class="card p-6 text-center">
      <p class="font-bold text-rose-600 dark:text-rose-400">{{ error }}</p>
      <RouterLink to="/soru-coz" class="btn-secondary mt-4">Yeni oturum başlat</RouterLink>
    </div>

    <!-- Oturum -->
    <template v-else>
      <header class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-white">
            <Crosshair v-if="session.mistakes_only" class="h-5 w-5 text-wine-600" />
            {{ session.mistakes_only ? 'Hata Avcısı' : 'Soru Çöz' }}
          </h1>
          <p class="text-sm text-slate-500 dark:text-slate-400">
            {{ session.topic_title || `${session.grade}. sınıf · karışık` }} · {{ answeredCount }}/{{ questions.length }} cevaplandı · {{ correctCount }} doğru
          </p>
        </div>
        <button type="button" class="btn-secondary !py-2" :disabled="finishing" @click="finish">
          <LoaderCircle v-if="finishing" class="h-4 w-4 animate-spin" /><Flag v-else class="h-4 w-4" /> Bitir
        </button>
      </header>

      <nav aria-label="Sorular" class="flex flex-wrap gap-1.5">
        <button
          v-for="(q, i) in questions"
          :key="q.id"
          type="button"
          class="h-8 w-8 rounded-lg text-xs font-bold transition"
          :class="pillClass(q, i)"
          :aria-current="i === currentIndex ? 'step' : undefined"
          :aria-label="`Soru ${i + 1}${answers[q.id] ? (answers[q.id].is_correct ? ', doğru' : ', yanlış') : ''}`"
          @click="goTo(i)"
        >
          {{ i + 1 }}
        </button>
      </nav>

      <article v-if="current" class="card space-y-4 p-4 sm:p-6">
        <QuestionCard v-model="selected" :question="current" :result="currentResult" :index="currentIndex + 1" :total="questions.length" :disabled="submitting" />

        <p v-if="error" class="text-sm font-semibold text-rose-600 dark:text-rose-400" role="alert">{{ error }}</p>

        <div v-if="!currentResult" class="flex flex-wrap justify-end gap-2">
          <button v-if="!allAnswered && answeredCount < questions.length - 1" type="button" class="btn-ghost" @click="next">
            <SkipForward class="h-4 w-4" /> Atla
          </button>
          <button type="button" class="btn-primary" :disabled="!selected || submitting" @click="check">
            <LoaderCircle v-if="submitting" class="h-4 w-4 animate-spin" /> Cevabı kontrol et
          </button>
        </div>

        <div v-else class="space-y-3">
          <MascotFeedback v-if="currentResult.is_correct" state="correct" compact />
          <MascotFeedback v-else state="struggle" compact :message="currentResult.misconception?.detail || 'Doğru cevabı ve çözümü aşağıda inceleyebilirsin.'">
            <RouterLink v-if="currentResult.misconception?.recommended" :to="recommendationLink(currentResult.misconception.recommended)" class="btn-secondary !py-1.5 text-xs">
              <ArrowRight class="h-3.5 w-3.5" /> “{{ currentResult.misconception.recommended.title }}” özetine git
            </RouterLink>
          </MascotFeedback>
          <RewardNotice :rewards="rewards[current.id]" compact />

          <details class="rounded-xl border border-slate-200 p-3 dark:border-slate-700" :open="!currentResult.is_correct">
            <summary class="cursor-pointer text-sm font-bold text-slate-800 dark:text-slate-100">Adım adım çözüm</summary>
            <KatexRenderer :text="currentResult.step_by_step_solution" class="mt-2 text-sm text-slate-700 dark:text-slate-200" />
          </details>

          <div class="flex justify-end">
            <button v-if="!allAnswered" type="button" class="btn-primary" @click="next">Sonraki soru <ArrowRight class="h-4 w-4" /></button>
            <button v-else type="button" class="btn-primary" :disabled="finishing" @click="finish">
              <Flag class="h-4 w-4" /> Sonuçları gör
            </button>
          </div>
        </div>
      </article>
    </template>
  </div>
</template>
