<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  BookMarked,
  CircleCheck,
  Clock3,
  Goal,
  History,
  Lightbulb,
  LoaderCircle,
  Sigma,
  TriangleAlert,
} from 'lucide-vue-next'
import ReinforcementQuestion from '@/components/learning/ReinforcementQuestion.vue'
import WorkedExample from '@/components/learning/WorkedExample.vue'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import KatexRenderer from '@/components/math/KatexRenderer.vue'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useContentStore } from '@/stores/content'
import { useGradeStore } from '@/stores/grade'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const contentStore = useContentStore()
const gradeStore = useGradeStore()

const topic = ref(null)
const progress = ref(null)
const questions = ref([])
const loading = ref(true)
const error = ref('')
const activeSection = ref('')
const resumeTarget = ref(null)
const completing = ref(false)
const completion = ref(null) // { points_awarded }

const content = computed(() => topic.value?.content)
const sections = computed(() => content.value?.sections ?? [])
const isCompleted = computed(() => progress.value?.status === 'completed')

async function load(topicId) {
  loading.value = true
  error.value = ''
  topic.value = null
  completion.value = null
  resumeTarget.value = null
  questions.value = []
  try {
    const [detail, prog] = await Promise.all([
      contentStore.fetchTopic(topicId),
      auth.isAuthenticated ? api.get(`/analytics/topic-progress/${topicId}/`).then((r) => r.data) : null,
    ])
    topic.value = detail
    progress.value = prog
    gradeStore.setGrade(detail.grade)

    const ids = detail.content?.reinforcement_question_ids ?? []
    if (ids.length) {
      const all = await contentStore.fetchTopicQuestions(topicId)
      const byId = Object.fromEntries(all.map((q) => [q.id, q]))
      questions.value = ids.map((id) => byId[id]).filter(Boolean)
    }
  } catch (e) {
    error.value = e.response?.status === 404 ? 'Bu konu bulunamadı.' : errorMessage(e, 'Konu yüklenemedi.')
  } finally {
    loading.value = false
  }

  await nextTick()
  observeSections()
  const requested = route.query.bolum
  if (typeof requested === 'string' && sections.value.some((s) => s.id === requested)) {
    scrollToSection(requested)
  } else if (progress.value?.last_section_id && progress.value.last_section_id !== sections.value[0]?.id) {
    resumeTarget.value = sections.value.find((s) => s.id === progress.value.last_section_id) ?? null
  }
}

watch(() => route.params.topicId, (id) => id && load(id), { immediate: true })
watch(
  () => route.query.bolum,
  (id) => typeof id === 'string' && topic.value && scrollToSection(id),
)

function scrollToSection(id) {
  const el = document.getElementById(id)
  if (!el) return
  tracking = true
  resumeTarget.value = null
  el.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' })
  activeSection.value = id
}

// --- "Son kalınan yer": okuma bölgesine giren bölüm izlenir ve gecikmeli olarak sunucuya kaydedilir.
// Sayfa açılırken görünen bölüm, önceki "son kalınan yer"in üzerine yazılmasın: kayıt ancak
// öğrenci kendisi kaydırdığında ya da bir bölüme atladığında başlar.
let observer = null
let tracking = false
function enableTracking() {
  tracking = true
}
function observeSections() {
  observer?.disconnect()
  tracking = false
  window.addEventListener('scroll', enableTracking, { once: true, passive: true })
  if (!sections.value.length) return
  observer = new IntersectionObserver(
    (entries) => {
      const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
      if (visible.length) activeSection.value = visible[0].target.id
    },
    { rootMargin: '-20% 0px -65% 0px' },
  )
  sections.value.forEach((s) => {
    const el = document.getElementById(s.id)
    if (el) observer.observe(el)
  })
}

let saveTimer = null
watch(activeSection, (id) => {
  window.clearTimeout(saveTimer)
  if (!auth.isAuthenticated || !tracking || !id || !topic.value || id === progress.value?.last_section_id) return
  const topicId = topic.value.id
  saveTimer = window.setTimeout(async () => {
    try {
      const { data } = await api.patch(`/analytics/topic-progress/${topicId}/`, { last_section_id: id })
      if (topic.value?.id === topicId) progress.value = data
    } catch {
      // Konum kaydı kritik değil; bir sonraki bölüm geçişinde tekrar denenir.
    }
  }, 1500)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  window.removeEventListener('scroll', enableTracking)
  window.clearTimeout(saveTimer)
})

function goToRecommendation(target) {
  if (target.topic_id === topic.value?.id && target.section_id) scrollToSection(target.section_id)
  else router.push({ name: 'topic-detail', params: { topicId: target.topic_id }, query: target.section_id ? { bolum: target.section_id } : {} })
}

async function markCompleted() {
  completing.value = true
  error.value = ''
  try {
    const { data } = await api.post(`/analytics/topic-progress/${topic.value.id}/complete/`)
    progress.value = data
    completion.value = { points: data.points_awarded }
  } catch (e) {
    error.value = errorMessage(e, 'Konu tamamlanamadı. Tekrar dene.')
  } finally {
    completing.value = false
  }
}
</script>

<template>
  <div v-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Konu yükleniyor…</div>

  <div v-else-if="!topic" class="card mx-auto max-w-lg p-6 text-center">
    <p class="font-bold text-rose-600 dark:text-rose-400">{{ error }}</p>
    <RouterLink to="/konular" class="btn-secondary mt-4"><ArrowLeft class="h-4 w-4" /> Konulara dön</RouterLink>
  </div>

  <div v-else class="space-y-6">
    <!-- Başlık -->
    <header class="space-y-3">
      <nav class="flex flex-wrap items-center gap-1 text-sm font-semibold text-slate-500 dark:text-slate-400" aria-label="Konum">
        <RouterLink to="/konular" class="hover:text-brand-600">Konular</RouterLink>
        <span aria-hidden="true">/</span>
        <span>{{ topic.grade }}. Sınıf</span>
        <span aria-hidden="true">/</span>
        <span class="truncate">{{ topic.theme.title }}</span>
      </nav>
      <div class="flex flex-wrap items-start justify-between gap-3">
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">{{ topic.title }}</h1>
        <span
          v-if="isCompleted"
          class="inline-flex items-center gap-1.5 rounded-full bg-aqua-50 px-3 py-1 text-xs font-bold text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300"
        >
          <CircleCheck class="h-3.5 w-3.5" /> Tamamlandı
        </span>
      </div>
      <p v-if="content" class="max-w-3xl text-slate-600 dark:text-slate-300">{{ content.summary }}</p>
      <div v-if="content" class="flex flex-wrap gap-3 text-xs font-bold text-slate-500 dark:text-slate-400">
        <span class="inline-flex items-center gap-1"><Clock3 class="h-3.5 w-3.5" /> ~{{ content.estimated_minutes }} dk</span>
        <span class="inline-flex items-center gap-1"><BookMarked class="h-3.5 w-3.5" /> {{ sections.length }} bölüm</span>
        <span v-if="questions.length" class="inline-flex items-center gap-1"><Goal class="h-3.5 w-3.5" /> {{ questions.length }} pekiştirme sorusu</span>
      </div>
    </header>

    <!-- Kaldığın yerden devam -->
    <div
      v-if="resumeTarget"
      class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-brand-200 bg-brand-50 px-4 py-3 dark:border-brand-500/30 dark:bg-brand-500/10"
    >
      <span class="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
        <History class="h-4 w-4 text-brand-600" /> En son “{{ resumeTarget.title }}” bölümündeydin.
      </span>
      <div class="flex gap-2">
        <button type="button" class="btn-ghost !py-1.5 text-xs" @click="resumeTarget = null">Baştan başla</button>
        <button type="button" class="btn-primary !py-1.5 text-xs" @click="scrollToSection(resumeTarget.id)">Kaldığın yerden devam et</button>
      </div>
    </div>

    <!-- Anlatımı henüz olmayan konu -->
    <template v-if="!content">
      <MascotFeedback
        state="welcome"
        title="Bu konunun anlatımı hazırlanıyor"
        message="Konu anlatımı yakında burada olacak. Şimdilik öğrenme hedeflerini ve alt konuları inceleyebilirsin."
      />
      <section class="card p-5">
        <h2 class="font-bold text-slate-900 dark:text-white">Kazanımlar</h2>
        <ul class="mt-3 space-y-2">
          <li v-for="o in topic.learning_outcomes" :key="o.code" class="flex gap-3 text-sm">
            <span class="shrink-0 rounded-md bg-brand-50 px-2 py-0.5 font-mono text-xs font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">{{ o.code }}</span>
            <span class="text-slate-700 dark:text-slate-200">{{ o.description }}</span>
          </li>
        </ul>
        <h2 class="mt-5 font-bold text-slate-900 dark:text-white">Alt konular</h2>
        <ul class="mt-2 flex flex-wrap gap-2">
          <li v-for="s in topic.subtopics" :key="s.id" class="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">{{ s.title }}</li>
        </ul>
      </section>
    </template>

    <div v-else class="lg:grid lg:grid-cols-[220px_minmax(0,1fr)] lg:gap-8">
      <!-- İçindekiler -->
      <aside class="mb-6 lg:mb-0">
        <nav class="lg:sticky lg:top-24" aria-label="Konu içindekiler">
          <p class="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">İçindekiler</p>
          <ol class="flex gap-2 overflow-x-auto pb-1 lg:flex-col lg:gap-0.5 lg:overflow-visible">
            <li v-for="(s, i) in sections" :key="s.id" class="shrink-0">
              <button
                type="button"
                class="flex w-full items-center gap-2 whitespace-nowrap rounded-xl px-3 py-1.5 text-left text-sm font-semibold transition lg:whitespace-normal"
                :class="activeSection === s.id ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-brand-50 dark:bg-slate-800 dark:text-slate-300 lg:bg-transparent lg:dark:bg-transparent'"
                :aria-current="activeSection === s.id ? 'location' : undefined"
                @click="scrollToSection(s.id)"
              >
                <span class="text-xs opacity-70">{{ i + 1 }}.</span> {{ s.title }}
              </button>
            </li>
            <li v-if="questions.length" class="shrink-0">
              <a href="#pekistirme" class="flex whitespace-nowrap rounded-xl bg-slate-100 px-3 py-1.5 text-sm font-semibold text-slate-600 hover:bg-brand-50 dark:bg-slate-800 dark:text-slate-300 lg:bg-transparent lg:dark:bg-transparent">
                Pekiştirme soruları
              </a>
            </li>
          </ol>
        </nav>
      </aside>

      <div class="min-w-0 space-y-6">
        <!-- Öğrenme hedefleri -->
        <section class="card p-5">
          <h2 class="flex items-center gap-2 font-bold text-slate-900 dark:text-white"><Goal class="h-5 w-5 text-aqua-500" /> Bu konuda neler öğreneceksin?</h2>
          <ul class="mt-3 space-y-2">
            <li v-for="(objective, i) in content.learning_objectives" :key="i" class="flex gap-2 text-sm text-slate-700 dark:text-slate-200">
              <CircleCheck class="mt-0.5 h-4 w-4 shrink-0 text-aqua-500" />
              <KatexRenderer :text="objective" inline />
            </li>
          </ul>
        </section>

        <!-- Bölümler -->
        <section v-for="(s, i) in sections" :id="s.id" :key="s.id" class="card scroll-mt-24 space-y-5 p-5 sm:p-6">
          <h2 class="text-xl font-bold text-slate-900 dark:text-white">
            <span class="text-brand-500">{{ i + 1 }}.</span> {{ s.title }}
          </h2>
          <KatexRenderer :text="s.body" class="leading-relaxed text-slate-700 dark:text-slate-200" />

          <div v-if="s.formulas.length">
            <h3 class="mb-2 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-500"><Sigma class="h-4 w-4" /> Formüller</h3>
            <div class="grid gap-3 sm:grid-cols-2">
              <div
                v-for="f in s.formulas"
                :key="f.label"
                class="min-w-0 rounded-xl border border-brand-100 bg-brand-50/60 px-4 py-3 dark:border-brand-500/20 dark:bg-brand-500/5"
              >
                <p class="text-xs font-bold text-brand-700 dark:text-brand-300">{{ f.label }}</p>
                <KatexRenderer :latex="f.latex" display class="text-slate-900 dark:text-white" />
              </div>
            </div>
          </div>

          <div v-if="s.examples.length" class="space-y-3">
            <WorkedExample v-for="(ex, j) in s.examples" :key="ex.title" :example="ex" :index="j + 1" />
          </div>

          <div v-if="s.tip" class="flex gap-3 rounded-xl bg-aqua-50 p-4 text-sm text-aqua-700 dark:bg-aqua-500/10 dark:text-aqua-300">
            <Lightbulb class="h-5 w-5 shrink-0" />
            <KatexRenderer :text="s.tip" class="min-w-0 font-semibold" />
          </div>

          <div v-if="s.common_mistakes.length" class="rounded-xl border border-rose-200 bg-rose-50/70 p-4 dark:border-rose-500/30 dark:bg-rose-500/5">
            <h3 class="flex items-center gap-2 text-sm font-bold text-wine-600 dark:text-rose-300"><TriangleAlert class="h-4 w-4" /> Sık yapılan hatalar</h3>
            <ul class="mt-2 space-y-1.5 text-sm text-slate-700 dark:text-slate-200">
              <li v-for="(m, j) in s.common_mistakes" :key="j" class="flex gap-2">
                <span class="text-rose-500" aria-hidden="true">✗</span> <KatexRenderer :text="m" inline />
              </li>
            </ul>
          </div>
        </section>

        <!-- Pekiştirme -->
        <section v-if="questions.length" id="pekistirme" class="scroll-mt-24 space-y-3">
          <div>
            <h2 class="text-xl font-bold text-slate-900 dark:text-white">Konu sonu pekiştirme</h2>
            <p class="text-sm text-slate-500 dark:text-slate-400">Cevapların sunucuda kontrol edilir; yanlışsan seni ilgili bölüme yönlendiririm.</p>
          </div>
          <ReinforcementQuestion
            v-for="(q, i) in questions"
            :key="q.id"
            :question="q"
            :index="i + 1"
            @go-to-section="goToRecommendation"
          />
        </section>

        <!-- Tamamla -->
        <section class="card p-5">
          <MascotFeedback
            v-if="completion"
            state="badge"
            :message="
              completion.points
                ? `“${topic.title}” konusunu tamamladın ve ${completion.points} puan kazandın!`
                : `“${topic.title}” konusu zaten tamamlanmış görünüyor. Tekrar etmek her zaman iyi fikir!`
            "
          >
            <RouterLink to="/konular" class="btn-secondary !py-1.5 text-xs">Sıradaki konuya geç</RouterLink>
            <RouterLink to="/panel" class="btn-ghost !py-1.5 text-xs">Paneline bak</RouterLink>
          </MascotFeedback>
          <div v-else-if="!auth.isAuthenticated" class="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="font-bold text-slate-900 dark:text-white">İlerlemeni kaydetmek ister misin?</p>
              <p class="text-sm text-slate-500 dark:text-slate-400">Hesap açarsan tamamladığın konular, cevapların ve puanın panelinde birikir.</p>
            </div>
            <div class="flex shrink-0 gap-2">
              <RouterLink :to="{ name: 'login', query: { next: route.fullPath } }" class="btn-secondary">Giriş yap</RouterLink>
              <RouterLink to="/kayit" class="btn-primary">Kayıt ol</RouterLink>
            </div>
          </div>
          <div v-else class="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p class="font-bold text-slate-900 dark:text-white">{{ isCompleted ? 'Bu konuyu tamamladın' : 'Konuyu bitirdin mi?' }}</p>
              <p class="text-sm text-slate-500 dark:text-slate-400">
                {{ isCompleted ? 'İstediğin zaman geri dönüp tekrar edebilirsin.' : 'Tamamlandı olarak işaretle; ilerlemen paneline yansısın.' }}
              </p>
            </div>
            <button v-if="!isCompleted" type="button" class="btn-primary" :disabled="completing" @click="markCompleted">
              <LoaderCircle v-if="completing" class="h-4 w-4 animate-spin" />
              <CircleCheck v-else class="h-4 w-4" />
              Tamamlandı olarak işaretle
            </button>
          </div>
          <p v-if="error" class="mt-3 text-sm font-semibold text-rose-600 dark:text-rose-400" role="alert">{{ error }}</p>
        </section>
      </div>
    </div>
  </div>
</template>
