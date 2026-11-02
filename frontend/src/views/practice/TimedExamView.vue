<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, CircleCheck, Eraser, Flag, Hourglass, LoaderCircle, PencilLine, Timer, TriangleAlert } from 'lucide-vue-next'
import QuestionCard from '@/components/practice/QuestionCard.vue'
import SessionSetup from '@/components/practice/SessionSetup.vue'
import { errorCode, errorMessage } from '@/services/api'
import { useExamStore } from '@/stores/exam'

const route = useRoute()
const router = useRouter()
const exam = useExamStore()

const session = ref(null)
const answers = ref({}) // soru_id -> seçilen şık (doğruluk bilgisi test bitene kadar gelmez)
const currentIndex = ref(0)
const loading = ref(false)
const saving = ref('') // kaydedilen soru_id
const finishing = ref(false)
const error = ref('')

const sessionId = computed(() => route.params.sessionId)
const questions = computed(() => session.value?.questions ?? [])
const current = computed(() => questions.value[currentIndex.value])
const answeredCount = computed(() => Object.values(answers.value).filter(Boolean).length)

// Geri sayım: sunucunun bildirdiği kalan süre, istemci saatinden bağımsız olarak yerel saatle sayılır.
// Asıl süre denetimi sunucudadır; süre dolduktan sonra gönderilen cevaplar reddedilir.
const endsAt = ref(0)
const now = ref(Date.now())
let ticker = null
const remaining = computed(() => Math.max(0, Math.ceil((endsAt.value - now.value) / 1000)))
const clock = computed(() => {
  const m = Math.floor(remaining.value / 60)
  const s = remaining.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})
const lowTime = computed(() => remaining.value <= 60)

function startTicker() {
  window.clearInterval(ticker)
  ticker = window.setInterval(() => {
    now.value = Date.now()
    if (session.value && remaining.value === 0 && !finishing.value) {
      // Süre doldu: bir kez bitirmeyi dene (başarısız olursa "Testi bitir" butonu kalır; sunucu zaten süreyi denetler).
      window.clearInterval(ticker)
      finish({ confirm: false })
    }
  }, 500)
}
onBeforeUnmount(() => window.clearInterval(ticker))

function showResult(id) {
  window.clearInterval(ticker)
  router.replace({ name: 'exam-result', params: { type: 'timed', sessionId: id } })
}

async function load(id) {
  error.value = ''
  session.value = null
  answers.value = {}
  window.clearInterval(ticker)
  if (!id) return
  loading.value = true
  try {
    const data = await exam.fetchSession('timed', id)
    if (data.is_finished) return showResult(id)
    session.value = data
    answers.value = { ...data.answers }
    endsAt.value = Date.now() + data.remaining_seconds * 1000
    now.value = Date.now()
    currentIndex.value = Math.max(questions.value.findIndex((q) => !answers.value[q.id]), 0)
    startTicker()
  } catch (e) {
    error.value = errorMessage(e, 'Test yüklenemedi.')
  } finally {
    loading.value = false
  }
}
watch(sessionId, load, { immediate: true })

async function start(payload) {
  loading.value = true
  error.value = ''
  try {
    const data = await exam.startTimed(payload)
    router.push({ name: 'timed-session', params: { sessionId: data.id } })
  } catch (e) {
    error.value = errorMessage(e, 'Test başlatılamadı.')
    loading.value = false
  }
}

async function choose(key) {
  const q = current.value
  const previous = answers.value[q.id] || ''
  answers.value = { ...answers.value, [q.id]: key }
  saving.value = q.id
  error.value = ''
  try {
    await exam.submitAnswer('timed', session.value.id, q.id, key)
  } catch (e) {
    if (errorCode(e) === 'time_up') return showResult(session.value.id)
    answers.value = { ...answers.value, [q.id]: previous }
    error.value = errorMessage(e, 'Cevabın kaydedilemedi. Tekrar dene.')
  } finally {
    if (saving.value === q.id) saving.value = ''
  }
}

async function finish({ confirm = true } = {}) {
  if (finishing.value || !session.value) return
  const blanks = questions.value.length - answeredCount.value
  if (confirm && !window.confirm(blanks ? `${blanks} soru boş. Testi bitirmek istediğine emin misin?` : 'Testi bitirmek istediğine emin misin?')) return
  finishing.value = true
  try {
    await exam.finish('timed', session.value.id)
    showResult(session.value.id)
  } catch (e) {
    error.value = errorMessage(e, 'Test bitirilemedi. Tekrar dene.')
    finishing.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <!-- Kurulum -->
    <template v-if="!sessionId">
      <header>
        <h1 class="flex items-center gap-2 text-2xl font-bold text-slate-900 dark:text-white"><Timer class="h-6 w-6 text-wine-600" /> Süreli Test</h1>
        <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Süre sunucuda tutulur ve sayfayı yenilesen de durmaz. Cevaplarını süre bitene kadar değiştirebilirsin; doğru cevaplar ve çözümler test bitince açılır.
        </p>
      </header>
      <p v-if="error" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">{{ error }}</p>
      <SessionSetup mode="timed" :loading="loading" :initial-topic="typeof route.query.konu === 'string' ? route.query.konu : ''" @start="start" />
      <RouterLink to="/soru-coz" class="card flex items-center gap-3 p-4 text-sm transition hover:border-brand-300">
        <PencilLine class="h-5 w-5 shrink-0 text-brand-500" />
        <span class="flex-1"><span class="font-bold text-slate-800 dark:text-slate-100">Önce alıştırma mı?</span> Soru Çöz modunda her cevaptan sonra çözümü hemen görürsün.</span>
        <ArrowRight class="h-4 w-4 text-slate-400" />
      </RouterLink>
    </template>

    <div v-else-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Test yükleniyor…</div>

    <div v-else-if="!session" class="card p-6 text-center">
      <p class="font-bold text-rose-600 dark:text-rose-400">{{ error }}</p>
      <RouterLink to="/sureli-test" class="btn-secondary mt-4">Yeni test başlat</RouterLink>
    </div>

    <!-- Test -->
    <template v-else>
      <div class="sticky top-16 z-10 -mx-4 border-b border-slate-200 bg-slate-50/95 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 sm:mx-0 sm:rounded-xl sm:border">
        <div class="flex items-center justify-between gap-3">
          <div
            class="flex items-center gap-2 rounded-xl px-3 py-1.5 text-lg font-bold tabular-nums"
            :class="lowTime ? 'bg-rose-600 text-white' : 'bg-white text-slate-900 dark:bg-slate-900 dark:text-white'"
            role="timer"
            :aria-label="`Kalan süre ${clock}`"
          >
            <Hourglass class="h-5 w-5" :class="{ 'animate-pulse': lowTime }" /> {{ clock }}
          </div>
          <span class="text-sm font-semibold text-slate-600 dark:text-slate-300">{{ answeredCount }}/{{ questions.length }} cevaplandı</span>
          <button type="button" class="btn-primary !py-2" :disabled="finishing" @click="finish()">
            <LoaderCircle v-if="finishing" class="h-4 w-4 animate-spin" /><Flag v-else class="h-4 w-4" />
            <span class="hidden min-[400px]:inline">Testi bitir</span>
          </button>
        </div>
        <p v-if="lowTime && remaining > 0" class="mt-2 flex items-center gap-1.5 text-xs font-bold text-rose-600 dark:text-rose-400" role="alert">
          <TriangleAlert class="h-3.5 w-3.5" /> Son bir dakika! Süre dolunca test otomatik olarak tamamlanır.
        </p>
      </div>

      <nav aria-label="Sorular" class="flex flex-wrap gap-1.5">
        <button
          v-for="(q, i) in questions"
          :key="q.id"
          type="button"
          class="h-8 w-8 rounded-lg text-xs font-bold transition"
          :class="[
            answers[q.id] ? 'bg-brand-600 text-white dark:bg-brand-500' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
            i === currentIndex ? 'ring-2 ring-brand-500 ring-offset-1 dark:ring-offset-slate-900' : '',
          ]"
          :aria-current="i === currentIndex ? 'step' : undefined"
          :aria-label="`Soru ${i + 1}${answers[q.id] ? ', cevaplandı' : ', boş'}`"
          @click="currentIndex = i"
        >
          {{ i + 1 }}
        </button>
      </nav>

      <article v-if="current" class="card space-y-4 p-4 sm:p-6">
        <QuestionCard
          :model-value="answers[current.id] || ''"
          :question="current"
          :index="currentIndex + 1"
          :total="questions.length"
          :disabled="finishing"
          @update:model-value="choose"
        />

        <p v-if="error" class="text-sm font-semibold text-rose-600 dark:text-rose-400" role="alert">{{ error }}</p>

        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="text-xs font-semibold text-slate-500 dark:text-slate-400" aria-live="polite">
            <template v-if="saving === current.id"><LoaderCircle class="inline h-3.5 w-3.5 animate-spin" /> Kaydediliyor…</template>
            <template v-else-if="answers[current.id]"><CircleCheck class="inline h-3.5 w-3.5 text-aqua-600" /> Cevabın kaydedildi</template>
          </span>
          <div class="flex gap-2">
            <button v-if="answers[current.id]" type="button" class="btn-ghost !py-2" :disabled="!!saving" @click="choose('')">
              <Eraser class="h-4 w-4" /> Boş bırak
            </button>
            <button type="button" class="btn-secondary !py-2" :disabled="currentIndex === 0" aria-label="Önceki soru" @click="currentIndex--">
              <ArrowLeft class="h-4 w-4" />
            </button>
            <button type="button" class="btn-secondary !py-2" :disabled="currentIndex === questions.length - 1" @click="currentIndex++">
              Sonraki <ArrowRight class="h-4 w-4" />
            </button>
          </div>
        </div>
      </article>
    </template>
  </div>
</template>
