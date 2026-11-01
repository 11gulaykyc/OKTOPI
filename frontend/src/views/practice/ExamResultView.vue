<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowRight, CircleCheck, CircleDashed, CircleX, Clock3, Crosshair, LoaderCircle, RotateCcw, TriangleAlert } from 'lucide-vue-next'
import AnswerBreakdown from '@/components/dashboard/AnswerBreakdown.vue'
import RewardNotice from '@/components/dashboard/RewardNotice.vue'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import KatexRenderer from '@/components/math/KatexRenderer.vue'
import QuestionCard from '@/components/practice/QuestionCard.vue'
import { formatDuration } from '@/composables/useHeartbeat'
import { errorMessage } from '@/services/api'
import { useExamStore } from '@/stores/exam'

const route = useRoute()
const exam = useExamStore()

const result = ref(null)
const loading = ref(true)
const error = ref('')
const filter = ref('all')

watch(
  () => [route.params.type, route.params.sessionId],
  async ([type, id]) => {
    loading.value = true
    error.value = ''
    result.value = null
    try {
      result.value = await exam.fetchResult(type, id)
    } catch (e) {
      error.value = errorMessage(e, 'Sonuçlar yüklenemedi.')
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

const isTimed = computed(() => result.value?.type === 'timed')
const s = computed(() => result.value?.summary)
const percent = computed(() => (s.value?.success_rate == null ? 0 : Math.round(s.value.success_rate * 100)))
const answered = computed(() => (s.value ? s.value.correct + s.value.incorrect : 0))
const hasMistakes = computed(() => (s.value?.incorrect ?? 0) > 0)

const mascot = computed(() => {
  if (!s.value) return null
  if (percent.value >= 80) return { state: 'correct', title: 'Harikasın, böyle devam!', message: `${s.value.total} sorudan ${s.value.correct} tanesini doğru çözdün.` }
  if (percent.value >= 50) return { state: 'correct', title: 'İyi gidiyorsun', message: 'Yanlışlarına göz atıp önerilen konu özetlerine bakarsan bir sonraki sefer daha da iyi olacak.' }
  return { state: 'struggle', title: 'Bu kavramları birlikte tekrar inceleyelim', message: 'Aşağıdaki kavram yanılgısı uyarıları nereden başlaman gerektiğini gösteriyor.' }
})

const FILTERS = [
  { value: 'all', label: 'Tümü' },
  { value: 'incorrect', label: 'Yanlışlar' },
  { value: 'blank', label: 'Boşlar' },
  { value: 'correct', label: 'Doğrular' },
]
function itemStatus(item) {
  if (!item.answered) return 'blank'
  return item.is_correct ? 'correct' : 'incorrect'
}
const items = computed(() => (result.value?.items ?? []).map((item, i) => ({ ...item, index: i + 1, status: itemStatus(item) })))
const visibleItems = computed(() => (filter.value === 'all' ? items.value : items.value.filter((i) => i.status === filter.value)))
const STATUS = {
  correct: { label: 'Doğru', icon: CircleCheck, tone: 'text-aqua-600' },
  incorrect: { label: 'Yanlış', icon: CircleX, tone: 'text-rose-600' },
  blank: { label: 'Boş', icon: CircleDashed, tone: 'text-slate-400' },
}

function recommendationLink(rec) {
  return { name: 'topic-detail', params: { topicId: rec.topic_id }, query: rec.section_id ? { bolum: rec.section_id } : {} }
}
const againLink = computed(() => ({
  name: isTimed.value ? 'timed' : 'practice',
  query: result.value?.topic_id ? { konu: result.value.topic_id } : {},
}))
</script>

<template>
  <div class="mx-auto max-w-4xl space-y-6">
    <div v-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Sonuçlar hazırlanıyor…</div>

    <div v-else-if="!result" class="card p-6 text-center">
      <p class="font-bold text-rose-600 dark:text-rose-400">{{ error }}</p>
      <RouterLink to="/soru-coz" class="btn-secondary mt-4">Soru çözmeye dön</RouterLink>
    </div>

    <template v-else>
      <header class="space-y-1">
        <p class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {{ isTimed ? 'Süreli test sonucu' : result.mistakes_only ? 'Hata Avcısı sonucu' : 'Soru çözümü sonucu' }}
        </p>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white">{{ result.topic_title || `${result.grade}. sınıf · karışık` }}</h1>
      </header>

      <p
        v-if="isTimed && result.auto_finished"
        class="flex items-center gap-2 rounded-xl bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-800 dark:bg-amber-500/10 dark:text-amber-300"
      >
        <Clock3 class="h-4 w-4 shrink-0" /> Süre dolduğu için test otomatik tamamlandı. Boş kalan sorular boş sayıldı.
      </p>

      <MascotFeedback v-if="mascot" :state="mascot.state" :title="mascot.title" :message="mascot.message" />
      <RewardNotice :rewards="result.rewards" />

      <!-- Özet -->
      <section class="grid gap-4 md:grid-cols-3">
        <article class="card flex flex-col items-center justify-center p-5 text-center">
          <p class="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Başarı</p>
          <p class="mt-1 text-4xl font-bold tabular-nums text-slate-900 dark:text-white">%{{ percent }}</p>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ s.correct }} / {{ s.total }} doğru</p>
          <p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
            <Clock3 class="mr-0.5 inline h-3.5 w-3.5" />{{ formatDuration(result.duration_used_seconds) }}
            <template v-if="isTimed"> / {{ formatDuration(result.duration_seconds) }}</template>
          </p>
        </article>
        <article class="card p-5 md:col-span-2">
          <h2 class="mb-4 font-bold text-slate-900 dark:text-white">Doğru · yanlış · boş</h2>
          <AnswerBreakdown :correct="s.correct" :incorrect="s.incorrect" :blank="s.blank" />
          <p v-if="answered && s.accuracy != null" class="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Cevapladığın {{ answered }} sorunun %{{ Math.round(s.accuracy * 100) }}'i doğru.
          </p>
        </article>
      </section>

      <!-- Kavram yanılgıları -->
      <section v-if="result.misconceptions.length" class="card space-y-3 p-5">
        <h2 class="flex items-center gap-2 font-bold text-slate-900 dark:text-white">
          <TriangleAlert class="h-5 w-5 text-wine-600" /> Kavram yanılgısı uyarıları
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400">
          Seçtiğin yanlış şıklar aşağıdaki düşünme hatalarına işaret ediyor olabilir. Tek bir test kesin tanı değildir; önerilen özetlere bakıp tekrar dene.
        </p>
        <ul class="space-y-2">
          <li
            v-for="m in result.misconceptions"
            :key="m.tag"
            class="flex flex-col gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 dark:border-rose-500/30 dark:bg-rose-500/10 sm:flex-row sm:items-center"
          >
            <p class="flex-1 text-sm text-slate-700 dark:text-slate-200">
              {{ m.detail }}
              <span v-if="m.count > 1" class="ml-1 rounded-full bg-rose-600 px-2 py-0.5 text-[11px] font-bold text-white">{{ m.count }} soruda</span>
            </p>
            <RouterLink v-if="m.recommended" :to="recommendationLink(m.recommended)" class="btn-secondary shrink-0 !py-1.5 text-xs">
              <ArrowRight class="h-3.5 w-3.5" /> “{{ m.recommended.title }}” özetine git
            </RouterLink>
          </li>
        </ul>
      </section>

      <div class="flex flex-wrap gap-2">
        <RouterLink v-if="hasMistakes" :to="{ name: 'practice', query: { hata: '1', ...(result.topic_id ? { konu: result.topic_id } : {}) } }" class="btn-primary">
          <Crosshair class="h-4 w-4" /> Yanlışlarımı tekrar çöz
        </RouterLink>
        <RouterLink :to="againLink" class="btn-secondary"><RotateCcw class="h-4 w-4" /> {{ isTimed ? 'Yeni test' : 'Yeni oturum' }}</RouterLink>
        <RouterLink to="/panel" class="btn-ghost">Panele dön</RouterLink>
      </div>

      <!-- Soru soru inceleme -->
      <section class="space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">Soruları incele</h2>
          <div class="flex flex-wrap gap-1" role="group" aria-label="Soruları filtrele">
            <button
              v-for="f in FILTERS"
              :key="f.value"
              type="button"
              class="rounded-lg px-3 py-1.5 text-xs font-bold transition"
              :class="filter === f.value ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'"
              :aria-pressed="filter === f.value"
              @click="filter = f.value"
            >
              {{ f.label }}
            </button>
          </div>
        </div>
        <p v-if="!visibleItems.length" class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">Bu filtrede soru yok.</p>
        <article v-for="item in visibleItems" :key="item.question_id" class="card space-y-3 p-4 sm:p-5">
          <p class="flex items-center gap-1.5 text-xs font-bold" :class="STATUS[item.status].tone">
            <component :is="STATUS[item.status].icon" class="h-4 w-4" /> {{ STATUS[item.status].label }}
          </p>
          <QuestionCard :question="item.question" :result="item" :index="item.index" :total="items.length" />
          <p v-if="item.misconception" class="rounded-lg bg-rose-50 px-3 py-2 text-xs text-wine-600 dark:bg-rose-500/10 dark:text-rose-300">{{ item.misconception.detail }}</p>
          <details class="rounded-xl border border-slate-200 p-3 dark:border-slate-700" :open="item.status !== 'correct'">
            <summary class="cursor-pointer text-sm font-bold text-slate-800 dark:text-slate-100">Adım adım çözüm</summary>
            <KatexRenderer :text="item.step_by_step_solution" class="mt-2 text-sm text-slate-700 dark:text-slate-200" />
          </details>
        </article>
      </section>
    </template>
  </div>
</template>
