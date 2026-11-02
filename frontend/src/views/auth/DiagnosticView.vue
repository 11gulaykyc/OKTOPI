<script setup>
import { computed, onMounted, ref } from 'vue'
import { ArrowLeft, ArrowRight, BookOpen, ChartColumn, Gauge, LoaderCircle, Send } from 'lucide-vue-next'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import QuestionCard from '@/components/practice/QuestionCard.vue'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

/**
 * Kayıt sonrası başlangıç seviye testi. Sorular ve puanlama sunucudadır; sonuç profile işlenir
 * (`initial_level_status`) ve bir kez yapılır. Öğrenci isterse atlayıp sonra panelden dönebilir.
 */
const auth = useAuthStore()

const info = ref(null)
const step = ref('intro') // intro | questions | result
const index = ref(0)
const answers = ref({})
const result = ref(null)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

const questions = computed(() => info.value?.questions ?? [])
const current = computed(() => questions.value[index.value])
const answeredCount = computed(() => Object.values(answers.value).filter(Boolean).length)
const isLast = computed(() => index.value === questions.value.length - 1)

const LEVEL_TEXT = {
  beginner: 'Temellerden başlayarak ilerleyeceğiz. Konu anlatımlarındaki çözümlü örnekler sana çok iyi gelecek.',
  intermediate: 'Temelin sağlam görünüyor. Zorlandığın kavramlara odaklanarak hızla ilerleyebilirsin.',
  advanced: 'Çok iyi bir başlangıç! Zor sorular ve süreli testlerle kendini zorlayabilirsin.',
}

onMounted(async () => {
  try {
    info.value = (await api.get('/auth/diagnostic/')).data
    if (info.value.completed) step.value = 'result'
  } catch (e) {
    error.value = errorMessage(e, 'Başlangıç testi yüklenemedi.')
  } finally {
    loading.value = false
  }
})

function setAnswer(key) {
  answers.value = { ...answers.value, [current.value.id]: key }
}

function next() {
  if (!isLast.value) index.value++
}

async function submit() {
  const blanks = questions.value.length - answeredCount.value
  if (blanks && !window.confirm(`${blanks} soruyu boş bıraktın. Bilmediğin soruları boş bırakman sorun değil; göndermek istiyor musun?`)) return
  submitting.value = true
  error.value = ''
  try {
    const payload = questions.value.map((q) => ({ question_id: q.id, selected_option: answers.value[q.id] || null }))
    const { data } = await api.post('/auth/diagnostic/', { answers: payload })
    result.value = data
    auth.user = data.user
    step.value = 'result'
  } catch (e) {
    error.value = errorMessage(e, 'Cevapların gönderilemedi. Tekrar dene.')
  } finally {
    submitting.value = false
  }
}

const level = computed(() => result.value?.level ?? info.value?.level)
const levelDisplay = computed(() => result.value?.level_display ?? info.value?.level_display)
</script>

<template>
  <div class="mx-auto max-w-3xl space-y-5">
    <div v-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Yükleniyor…</div>

    <p v-else-if="!info" class="card p-6 text-center font-bold text-rose-600 dark:text-rose-400">{{ error }}</p>

    <!-- Giriş -->
    <template v-else-if="step === 'intro'">
      <MascotFeedback
        state="welcome"
        :name="auth.displayName"
        :title="`Hoş geldin ${auth.displayName}!`"
        message="Sana uygun bir başlangıç noktası bulmak için birkaç kısa soru soracağım. Süre yok; bilmediğin soruyu boş bırakabilirsin."
      />
      <article class="card space-y-4 p-5 sm:p-6">
        <h1 class="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-white"><Gauge class="h-6 w-6 text-brand-500" /> Başlangıç seviye testi</h1>
        <div v-if="questions.length" class="space-y-2 text-sm text-slate-600 dark:text-slate-300">
          <p><strong>{{ questions.length }} soru</strong> · yaklaşık {{ Math.ceil(questions.length * 1.5) }} dakika · test yalnızca bir kez yapılır.</p>
          <p v-if="info.includes_lower_grades">
            {{ info.grade }}. sınıf soru havuzu henüz hazırlanırken temel bilgilerini önceki sınıfların konularıyla ölçüyoruz.
          </p>
          <p>Sonuç bir not değil; yalnızca hangi konulardan başlaman gerektiğini anlamamıza yardım eder.</p>
        </div>
        <p v-else class="rounded-xl bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-800/50 dark:text-slate-300">
          Şu an sınıfın için başlangıç sorusu bulunmuyor. Bu adımı atlayıp doğrudan konulara geçebilirsin.
        </p>
        <div class="flex flex-wrap justify-end gap-2">
          <RouterLink to="/panel" class="btn-ghost">Şimdilik atla</RouterLink>
          <button v-if="questions.length" type="button" class="btn-primary" @click="step = 'questions'">Teste başla <ArrowRight class="h-4 w-4" /></button>
        </div>
      </article>
    </template>

    <!-- Sorular -->
    <template v-else-if="step === 'questions' && current">
      <div class="flex items-center justify-between gap-3">
        <h1 class="text-lg font-bold text-slate-900 dark:text-white">Başlangıç seviye testi</h1>
        <span class="text-sm font-semibold text-slate-500 dark:text-slate-400">{{ answeredCount }}/{{ questions.length }} cevaplandı</span>
      </div>
      <div class="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="progressbar" :aria-valuenow="index + 1" aria-valuemin="1" :aria-valuemax="questions.length">
        <div class="h-full rounded-full bg-brand-600 transition-all dark:bg-brand-500" :style="{ width: `${((index + 1) / questions.length) * 100}%` }" />
      </div>
      <article class="card space-y-4 p-4 sm:p-6">
        <QuestionCard :model-value="answers[current.id] || ''" :question="current" :index="index + 1" :total="questions.length" :disabled="submitting" @update:model-value="setAnswer" />
        <p v-if="error" class="text-sm font-semibold text-rose-600 dark:text-rose-400" role="alert">{{ error }}</p>
        <div class="flex flex-wrap items-center justify-between gap-2">
          <button type="button" class="btn-ghost !py-2" :disabled="index === 0" @click="index--"><ArrowLeft class="h-4 w-4" /> Önceki</button>
          <div class="flex gap-2">
            <button v-if="!isLast && !answers[current.id]" type="button" class="btn-ghost !py-2" @click="next">Bilmiyorum, geç</button>
            <button v-if="!isLast" type="button" class="btn-primary !py-2" :disabled="!answers[current.id]" @click="next">Sonraki <ArrowRight class="h-4 w-4" /></button>
            <button v-else type="button" class="btn-primary !py-2" :disabled="submitting" @click="submit">
              <LoaderCircle v-if="submitting" class="h-4 w-4 animate-spin" /><Send v-else class="h-4 w-4" /> Gönder
            </button>
          </div>
        </div>
      </article>
    </template>

    <!-- Sonuç -->
    <template v-else-if="step === 'result'">
      <MascotFeedback state="badge" :title="`Başlangıç seviyen: ${levelDisplay}`" :message="LEVEL_TEXT[level] || ''" />
      <article v-if="result" class="card space-y-4 p-5">
        <p class="text-sm text-slate-600 dark:text-slate-300">
          {{ result.total }} sorudan <strong>{{ result.correct }}</strong> tanesini doğru cevapladın. Zor sorular daha fazla ağırlık taşır.
        </p>
        <ul class="space-y-2">
          <li v-for="t in result.topics" :key="t.topic_id">
            <div class="flex items-center justify-between text-sm">
              <span class="font-bold text-slate-700 dark:text-slate-200">{{ t.title }}</span>
              <span class="text-xs font-bold tabular-nums text-slate-500">{{ t.correct }}/{{ t.total }}</span>
            </div>
            <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
              <div class="h-full rounded-full bg-brand-600 dark:bg-brand-500" :style="{ width: `${Math.max((t.correct / t.total) * 100, 2)}%` }" />
            </div>
          </li>
        </ul>
        <p class="text-xs text-slate-500 dark:text-slate-400">Birkaç soruyla kesin tanı konmaz; soru çözdükçe analizin netleşecek.</p>
      </article>
      <p v-else class="card p-5 text-sm text-slate-600 dark:text-slate-300">
        Bu testi daha önce tamamladın. Sonucun profilinde görünüyor.
      </p>
      <div class="flex flex-wrap gap-2">
        <RouterLink to="/panel" class="btn-primary"><ChartColumn class="h-4 w-4" /> Panelime git</RouterLink>
        <RouterLink to="/konular" class="btn-secondary"><BookOpen class="h-4 w-4" /> Konulara göz at</RouterLink>
      </div>
    </template>
  </div>
</template>
