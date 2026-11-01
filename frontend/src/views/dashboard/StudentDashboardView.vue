<script setup>
import { computed, onMounted } from 'vue'
import {
  ArrowRight,
  BookOpen,
  CalendarCheck,
  CalendarDays,
  CircleCheck,
  Clock3,
  FileQuestion,
  History,
  ListTodo,
  LoaderCircle,
  RefreshCw,
  Award,
  Crosshair,
  Gauge,
  PencilLine,
  Target,
  Timer,
} from 'lucide-vue-next'
import AnswerBreakdown from '@/components/dashboard/AnswerBreakdown.vue'
import BadgeGrid from '@/components/dashboard/BadgeGrid.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import WeeklyStudyChart from '@/components/dashboard/WeeklyStudyChart.vue'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import { formatDuration } from '@/composables/useHeartbeat'
import { useAuthStore } from '@/stores/auth'
import { useStatsStore } from '@/stores/stats'

const auth = useAuthStore()
const stats = useStatsStore()

onMounted(() => {
  stats.fetchSummary()
  stats.fetchGamification().catch(() => {}) // rozet satırı isteğe bağlı; hata paneli engellemez
})
const needsDiagnostic = computed(() => auth.user?.profile?.initial_level_status === 'not_assessed')
const badges = computed(() => stats.gamification?.badges ?? [])
const earnedBadges = computed(() => badges.value.filter((b) => b.earned).length)

const s = computed(() => stats.summary)
// Bugünkü süre, sayaç her ping'de güncellendiği için paneli yenilemeden de güncel kalır.
const todaySeconds = computed(() => Math.max(stats.todaySeconds ?? 0, s.value?.study.today_seconds ?? 0))
const answered = computed(() => (s.value ? s.value.questions.correct + s.value.questions.incorrect : 0))
const accuracy = computed(() => (answered.value ? Math.round((s.value.questions.correct / answered.value) * 100) : null))
const lastTopic = computed(() => s.value?.recent_topics.find((t) => t.status !== 'completed') ?? s.value?.recent_topics[0])

// Az veriyle "kesin tanı" verilmez (CLAUDE.md Faz 4 kuralı burada da geçerli).
const MIN_QUESTIONS_FOR_RATE = 3
const STATUS_LABEL = { completed: 'Tamamlandı', in_progress: 'Devam ediyor', not_started: 'Başlanmadı' }

function rateTone(rate) {
  if (rate >= 0.75) return 'bg-aqua-600'
  if (rate >= 0.5) return 'bg-brand-600 dark:bg-brand-500'
  return 'bg-rose-600 dark:bg-rose-500'
}

function relativeTime(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return 'az önce'
  if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`
  if (diff < 86400) return `${Math.floor(diff / 3600)} sa önce`
  const days = Math.floor(diff / 86400)
  return days === 1 ? 'dün' : `${days} gün önce`
}
</script>

<template>
  <div class="space-y-6">
    <MascotFeedback state="welcome" :name="auth.displayName" :message="lastTopic ? `En son “${lastTopic.title}” konusundaydın. Kaldığın yerden devam etmeye ne dersin?` : 'Henüz bir konuya başlamadın. İlk konunu seçerek yolculuğa başla!'">
      <RouterLink
        v-if="lastTopic"
        :to="{ name: 'topic-detail', params: { topicId: lastTopic.topic_id } }"
        class="btn-primary !py-2 text-xs"
      >
        <History class="h-4 w-4" /> Devam et
      </RouterLink>
      <RouterLink to="/konular" class="btn-secondary !py-2 text-xs"><BookOpen class="h-4 w-4" /> Konular</RouterLink>
      <RouterLink to="/soru-coz" class="btn-secondary !py-2 text-xs"><PencilLine class="h-4 w-4" /> Soru Çöz</RouterLink>
      <RouterLink to="/sureli-test" class="btn-secondary !py-2 text-xs"><Timer class="h-4 w-4" /> Süreli Test</RouterLink>
      <RouterLink to="/oyss" class="btn-secondary !py-2 text-xs"><CalendarCheck class="h-4 w-4" /> OYSS Hazırlık</RouterLink>
    </MascotFeedback>

    <RouterLink
      v-if="needsDiagnostic"
      :to="{ name: 'diagnostic' }"
      class="flex items-center gap-3 rounded-xl border border-brand-200 bg-white p-4 transition hover:border-brand-400 dark:border-brand-500/30 dark:bg-slate-900"
    >
      <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300"><Gauge class="h-5 w-5" /></span>
      <span class="min-w-0 flex-1 text-sm">
        <span class="block font-bold text-slate-900 dark:text-white">Başlangıç seviyeni henüz belirlemedin</span>
        <span class="block text-slate-500 dark:text-slate-400">Birkaç kısa soruyla sana uygun başlangıç noktasını bulalım.</span>
      </span>
      <ArrowRight class="h-4 w-4 shrink-0 text-brand-500" />
    </RouterLink>

    <div class="flex items-center justify-between gap-3">
      <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Öğrenci Paneli</h1>
      <button type="button" class="btn-ghost !py-2 text-xs" :disabled="stats.loading" @click="stats.fetchSummary()">
        <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': stats.loading }" /> Yenile
      </button>
    </div>

    <p v-if="stats.error" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">
      {{ stats.error }}
    </p>
    <div v-if="!s && stats.loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Panel yükleniyor…</div>

    <template v-if="s">
      <!-- Özet kartları -->
      <section class="grid grid-cols-1 gap-3 min-[480px]:grid-cols-2 xl:grid-cols-4" aria-label="Özet">
        <StatCard label="Bugün" :value="formatDuration(todaySeconds, { short: true })" :hint="`${s.questions.today} soru çözdün`" :icon="Timer" tone="aqua" />
        <StatCard label="Bu hafta" :value="formatDuration(s.study.week_seconds, { short: true })" :hint="`Toplam ${formatDuration(s.study.total_seconds, { short: true })} · ${s.study.active_days} aktif gün`" :icon="CalendarDays" />
        <StatCard
          label="Çözülen soru"
          :value="s.questions.total"
          :hint="accuracy == null ? 'Henüz cevaplanmış soru yok' : `Doğruluk %${accuracy} · bu hafta ${s.questions.week}`"
          :icon="FileQuestion"
          tone="wine"
        />
        <StatCard label="Puan" :value="s.points.points" :hint="`Seviye ${s.points.level} · sonraki seviyeye ${s.points.next_level_at - s.points.points} puan`" :icon="Award" tone="accent">
          <div
            class="mt-2 h-1.5 w-full min-w-28 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
            role="progressbar"
            :aria-valuenow="Math.round(s.points.progress * 100)"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="`Seviye ${s.points.level + 1} ilerlemesi`"
          >
            <div class="h-full rounded-full bg-accent-600 dark:bg-accent-500" :style="{ width: `${s.points.progress * 100}%` }" />
          </div>
        </StatCard>
      </section>

      <!-- Grafikler -->
      <section class="grid gap-4 lg:grid-cols-3">
        <article class="card p-5 lg:col-span-2">
          <h2 class="font-bold text-slate-900 dark:text-white">Son 7 gün · aktif çalışma</h2>
          <p class="mb-4 text-xs text-slate-500 dark:text-slate-400">Yalnızca sayfayla etkileşimdeyken sayılan süre (dakika)</p>
          <WeeklyStudyChart :days="s.daily" />
        </article>
        <article class="card p-5">
          <h2 class="font-bold text-slate-900 dark:text-white">Cevap dağılımı</h2>
          <p class="mb-4 text-xs text-slate-500 dark:text-slate-400">Tüm zamanlar · {{ s.questions.total }} cevap</p>
          <AnswerBreakdown :correct="s.questions.correct" :incorrect="s.questions.incorrect" :blank="s.questions.blank" />
          <div v-if="s.misconception_count" class="mt-4 space-y-2 rounded-xl bg-rose-50 px-3 py-2 text-xs font-semibold text-wine-600 dark:bg-rose-500/10 dark:text-rose-300">
            <p>{{ s.misconception_count }} kavram yanılgısı kaydı var. Ayrıntılı hata analizi yakında burada.</p>
            <RouterLink :to="{ name: 'practice', query: { hata: '1' } }" class="inline-flex items-center gap-1 underline-offset-2 hover:underline">
              <Crosshair class="h-3.5 w-3.5" /> Yanlışlarını Hata Avcısı modunda tekrar çöz
            </RouterLink>
          </div>
        </article>
      </section>

      <!-- Konular -->
      <section class="grid gap-4 lg:grid-cols-2">
        <article class="card p-5">
          <div class="mb-3 flex items-center justify-between gap-2">
            <h2 class="font-bold text-slate-900 dark:text-white">Konu başarı oranları</h2>
            <span class="text-xs font-bold text-slate-500 dark:text-slate-400">{{ s.topics.completed }} / {{ s.topics.started }} konu tamamlandı</span>
          </div>
          <ul v-if="s.topics.success.length" class="space-y-3">
            <li v-for="t in s.topics.success" :key="t.topic_id">
              <div class="flex items-center justify-between gap-2 text-sm">
                <RouterLink :to="{ name: 'topic-detail', params: { topicId: t.topic_id } }" class="truncate font-bold text-slate-700 hover:text-brand-600 dark:text-slate-200">
                  {{ t.title }} <span class="font-semibold text-slate-400">· {{ t.grade }}. sınıf</span>
                </RouterLink>
                <span class="shrink-0 text-xs font-bold tabular-nums text-slate-600 dark:text-slate-300">
                  %{{ Math.round(t.success_rate * 100) }} <span class="font-semibold text-slate-400">({{ t.correct_answers }}/{{ t.questions_answered }})</span>
                </span>
              </div>
              <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                <div class="h-full rounded-full" :class="rateTone(t.success_rate)" :style="{ width: `${Math.max(t.success_rate * 100, 2)}%` }" />
              </div>
              <p v-if="t.questions_answered < MIN_QUESTIONS_FOR_RATE" class="mt-1 text-[11px] text-slate-400">
                Az veri: bu alanda daha fazla soru çözerek analizi netleştirebilirsin.
              </p>
            </li>
          </ul>
          <p v-else class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
            Henüz soru çözmedin. <RouterLink to="/soru-coz" class="font-semibold text-brand-600 hover:underline dark:text-brand-400">Soru Çöz</RouterLink> ekranında veya konu sonundaki pekiştirme sorularında çözdükçe başarı oranların burada görünecek.
          </p>
        </article>

        <article class="card p-5">
          <h2 class="mb-3 font-bold text-slate-900 dark:text-white">Son çalışmalar</h2>
          <ul v-if="s.recent_topics.length" class="divide-y divide-slate-100 dark:divide-slate-800">
            <li v-for="t in s.recent_topics" :key="t.topic_id">
              <RouterLink
                :to="{ name: 'topic-detail', params: { topicId: t.topic_id } }"
                class="group flex items-center gap-3 py-2.5"
              >
                <span
                  class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
                  :class="t.status === 'completed' ? 'bg-aqua-50 text-aqua-600 dark:bg-aqua-500/15 dark:text-aqua-300' : 'bg-brand-50 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300'"
                >
                  <component :is="t.status === 'completed' ? CircleCheck : Clock3" class="h-4 w-4" />
                </span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm font-bold text-slate-800 group-hover:text-brand-600 dark:text-slate-100">{{ t.title }}</span>
                  <span class="block text-xs text-slate-500 dark:text-slate-400">{{ STATUS_LABEL[t.status] }} · {{ relativeTime(t.updated_at) }}</span>
                </span>
                <ArrowRight class="h-4 w-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-brand-500" />
              </RouterLink>
            </li>
          </ul>
          <p v-else class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
            Açtığın konular burada listelenecek.
          </p>
        </article>
      </section>

      <!-- Görevler & hedefler -->
      <section class="grid gap-4 lg:grid-cols-2">
        <article class="card p-5">
          <div class="mb-3 flex items-center justify-between gap-2">
            <h2 class="flex items-center gap-2 font-bold text-slate-900 dark:text-white"><ListTodo class="h-5 w-5 text-brand-500" /> Aktif görevler</h2>
            <RouterLink to="/hedeflerim" class="text-xs font-bold text-brand-600 hover:underline dark:text-brand-400">Tümü</RouterLink>
          </div>
          <ul v-if="s.tasks.length" class="space-y-3">
            <li v-for="task in s.tasks" :key="task.id">
              <div class="flex items-center justify-between gap-2 text-sm">
                <span class="font-bold text-slate-700 dark:text-slate-200">
                  <CircleCheck v-if="task.completed" class="mr-1 inline h-4 w-4 text-aqua-600" />{{ task.title }}
                </span>
                <span class="shrink-0 text-xs font-bold tabular-nums text-slate-500">{{ task.progress }}/{{ task.target }} · +{{ task.points_reward }}</span>
              </div>
              <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                <div class="h-full rounded-full bg-brand-600 dark:bg-brand-500" :style="{ width: `${(task.progress / task.target) * 100}%` }" />
              </div>
            </li>
          </ul>
          <p v-else class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
            Bugün için atanmış görev yok.
          </p>
        </article>

        <article class="card p-5">
          <div class="mb-3 flex items-center justify-between gap-2">
            <h2 class="flex items-center gap-2 font-bold text-slate-900 dark:text-white"><Target class="h-5 w-5 text-aqua-500" /> Günlük hedeflerim</h2>
            <RouterLink to="/hedeflerim" class="text-xs font-bold text-brand-600 hover:underline dark:text-brand-400">Düzenle</RouterLink>
          </div>
          <ul v-if="s.goals.length" class="space-y-3">
            <li v-for="goal in s.goals" :key="goal.goal_type">
              <div class="flex items-center justify-between gap-2 text-sm">
                <span class="font-bold text-slate-700 dark:text-slate-200">{{ goal.label }}</span>
                <span class="shrink-0 text-xs font-bold tabular-nums text-slate-500">{{ Math.min(goal.current, goal.target) }}/{{ goal.target }}</span>
              </div>
              <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                <div class="h-full rounded-full bg-aqua-600" :style="{ width: `${Math.min(goal.current / goal.target, 1) * 100}%` }" />
              </div>
            </li>
          </ul>
          <p v-else class="rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
            Henüz bir günlük hedef belirlemedin. <RouterLink to="/hedeflerim" class="font-semibold text-brand-600 hover:underline dark:text-brand-400">Hedefini belirle</RouterLink>
          </p>
        </article>
      </section>

      <!-- Rozetler -->
      <section v-if="badges.length" class="card p-5">
        <div class="mb-3 flex items-center justify-between gap-2">
          <h2 class="flex items-center gap-2 font-bold text-slate-900 dark:text-white"><Award class="h-5 w-5 text-accent-600" /> Rozetlerim</h2>
          <RouterLink to="/hedeflerim" class="text-xs font-bold text-brand-600 hover:underline dark:text-brand-400">{{ earnedBadges }} / {{ badges.length }} · ayrıntılar</RouterLink>
        </div>
        <BadgeGrid :badges="badges" compact />
      </section>
    </template>
  </div>
</template>
