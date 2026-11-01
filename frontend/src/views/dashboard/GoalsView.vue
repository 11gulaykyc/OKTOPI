<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Award, CircleCheck, Clock3, FileQuestion, ListTodo, LoaderCircle, Save, Target, Trash2 } from 'lucide-vue-next'
import BadgeGrid from '@/components/dashboard/BadgeGrid.vue'
import RewardNotice from '@/components/dashboard/RewardNotice.vue'
import { errorMessage, fieldErrors } from '@/services/api'
import { useStatsStore } from '@/stores/stats'

const stats = useStatsStore()

const loading = ref(true)
const error = ref('')
const goals = ref([])
const history = ref([])
const drafts = reactive({}) // goal_type -> girilen hedef
const goalErrors = reactive({})
const saving = ref('')
const savedType = ref('')
const rewards = ref(null)

const GOAL_META = {
  daily_questions: { icon: FileQuestion, unit: 'soru', hint: 'Bir günde çözdüğün farklı soru sayısı (aynı soruyu tekrar çözmek sayılmaz).' },
  daily_minutes: { icon: Clock3, unit: 'dk', hint: 'Yalnızca sayfayla etkileşimdeyken sayılan aktif çalışma süresi.' },
}

function applyGoals(data) {
  goals.value = data.goals
  history.value = data.history
  for (const g of data.goals) drafts[g.goal_type] = g.target ?? ''
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [goalData] = await Promise.all([stats.fetchGoals(), stats.fetchGamification()])
    applyGoals(goalData)
  } catch (e) {
    error.value = errorMessage(e, 'Hedefler yüklenemedi.')
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function save(goal) {
  goalErrors[goal.goal_type] = ''
  savedType.value = ''
  const target = Number(drafts[goal.goal_type])
  if (!Number.isInteger(target) || target < goal.min || target > goal.max) {
    goalErrors[goal.goal_type] = `Hedef ${goal.min} ile ${goal.max} arasında bir tam sayı olmalı.`
    return
  }
  saving.value = goal.goal_type
  try {
    const data = await stats.saveGoal(goal.goal_type, target)
    applyGoals(data)
    rewards.value = data.rewards
    savedType.value = goal.goal_type
    stats.fetchGamification()
  } catch (e) {
    goalErrors[goal.goal_type] = fieldErrors(e).target || errorMessage(e, 'Hedef kaydedilemedi.')
  } finally {
    saving.value = ''
  }
}

async function remove(goal) {
  if (!window.confirm(`“${goal.label}” hedefini kaldırmak istiyor musun? Geçmiş günlerin kaydı silinmez.`)) return
  saving.value = goal.goal_type
  try {
    await stats.clearGoal(goal.goal_type)
    applyGoals(await stats.fetchGoals())
  } catch (e) {
    goalErrors[goal.goal_type] = errorMessage(e, 'Hedef kaldırılamadı.')
  } finally {
    saving.value = ''
  }
}

const g = computed(() => stats.gamification)
const earnedCount = computed(() => g.value?.badges.filter((b) => b.earned).length ?? 0)
const dailyTasks = computed(() => g.value?.tasks.filter((t) => t.period === 'daily') ?? [])
const weeklyTasks = computed(() => g.value?.tasks.filter((t) => t.period === 'weekly') ?? [])

const dayLabel = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString('tr-TR', { weekday: 'short', day: 'numeric' })
function cellTone(cell) {
  if (cell.target == null) return 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500'
  if (cell.reached) return 'bg-aqua-600 text-white'
  if (cell.current > 0) return 'bg-brand-100 text-brand-700 dark:bg-brand-500/20 dark:text-brand-300'
  return 'bg-slate-200 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
}
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="flex items-center gap-2 text-2xl font-bold text-slate-900 dark:text-white"><Target class="h-6 w-6 text-aqua-500" /> Hedeflerim</h1>
      <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">
        Günlük hedefini kendin belirle. Hedefini değiştirdiğinde geçmiş günlerin, o gün geçerli olan hedefe göre değerlendirilmeye devam eder.
      </p>
    </header>

    <p v-if="error" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">{{ error }}</p>
    <div v-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Yükleniyor…</div>

    <template v-else-if="goals.length">
      <RewardNotice :rewards="rewards" />

      <!-- Hedefler -->
      <section class="grid gap-4 md:grid-cols-2">
        <article v-for="goal in goals" :key="goal.goal_type" class="card space-y-3 p-5">
          <div class="flex items-start gap-3">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-aqua-50 text-aqua-600 dark:bg-aqua-500/15 dark:text-aqua-300">
              <component :is="GOAL_META[goal.goal_type].icon" class="h-5 w-5" />
            </span>
            <div class="min-w-0">
              <h2 class="font-bold text-slate-900 dark:text-white">{{ goal.label }}</h2>
              <p class="text-xs text-slate-500 dark:text-slate-400">{{ GOAL_META[goal.goal_type].hint }}</p>
            </div>
          </div>

          <div v-if="goal.target">
            <div class="flex items-center justify-between text-sm">
              <span class="font-bold text-slate-700 dark:text-slate-200">Bugün</span>
              <span class="font-bold tabular-nums text-slate-600 dark:text-slate-300">
                {{ Math.min(goal.current, goal.target) }} / {{ goal.target }} {{ GOAL_META[goal.goal_type].unit }}
                <CircleCheck v-if="goal.current >= goal.target" class="ml-1 inline h-4 w-4 text-aqua-600" aria-label="Hedefe ulaşıldı" />
              </span>
            </div>
            <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
              <div class="h-full rounded-full bg-aqua-600" :style="{ width: `${Math.min(goal.current / goal.target, 1) * 100}%` }" />
            </div>
          </div>
          <p v-else class="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500 dark:bg-slate-800/50 dark:text-slate-400">
            Henüz hedef yok. Bugün şu ana kadar: {{ goal.current }} {{ GOAL_META[goal.goal_type].unit }}.
          </p>

          <form class="flex items-end gap-2" @submit.prevent="save(goal)">
            <div class="flex-1">
              <label class="field-label" :for="`goal-${goal.goal_type}`">Günlük hedef ({{ GOAL_META[goal.goal_type].unit }})</label>
              <input
                :id="`goal-${goal.goal_type}`"
                v-model.number="drafts[goal.goal_type]"
                type="number"
                :min="goal.min"
                :max="goal.max"
                class="field-input"
                :placeholder="`${goal.min}–${goal.max}`"
              />
            </div>
            <button type="submit" class="btn-primary" :disabled="saving === goal.goal_type">
              <LoaderCircle v-if="saving === goal.goal_type" class="h-4 w-4 animate-spin" /><Save v-else class="h-4 w-4" /> Kaydet
            </button>
            <button v-if="goal.target" type="button" class="btn-ghost !px-3" :disabled="saving === goal.goal_type" aria-label="Hedefi kaldır" @click="remove(goal)">
              <Trash2 class="h-4 w-4" />
            </button>
          </form>
          <p v-if="goalErrors[goal.goal_type]" class="field-error" role="alert">{{ goalErrors[goal.goal_type] }}</p>
          <p v-else-if="savedType === goal.goal_type" class="text-xs font-semibold text-aqua-700 dark:text-aqua-300" role="status">Hedefin güncellendi.</p>
        </article>
      </section>

      <!-- Geçmiş -->
      <section class="card p-5">
        <h2 class="font-bold text-slate-900 dark:text-white">Son 14 gün</h2>
        <p class="mb-4 text-xs text-slate-500 dark:text-slate-400">Her gün, o gün geçerli olan hedefinle değerlendirilir. Turkuaz kutular hedefe ulaştığın günler.</p>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[640px] border-separate border-spacing-1 text-center text-[11px]">
            <thead>
              <tr>
                <th class="w-28 text-left font-bold text-slate-500" scope="col"><span class="sr-only">Hedef</span></th>
                <th v-for="row in history" :key="row.date" scope="col" class="font-semibold text-slate-500 dark:text-slate-400">{{ dayLabel(row.date) }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="goal in goals" :key="goal.goal_type">
                <th scope="row" class="text-left text-xs font-bold text-slate-700 dark:text-slate-200">{{ goal.label.replace('Günlük ', '') }}</th>
                <td v-for="row in history" :key="row.date">
                  <span
                    class="flex h-9 flex-col items-center justify-center rounded-lg font-bold tabular-nums"
                    :class="cellTone(row[goal.goal_type])"
                    :title="row[goal.goal_type].target == null ? 'O gün hedef yoktu' : `${row[goal.goal_type].current} / ${row[goal.goal_type].target}`"
                  >
                    {{ row[goal.goal_type].current }}
                    <span v-if="row[goal.goal_type].target != null" class="text-[9px] font-semibold opacity-80">/{{ row[goal.goal_type].target }}</span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Görevler -->
      <section v-if="g" class="grid gap-4 lg:grid-cols-2">
        <article v-for="group in [{ title: 'Günlük görevler', tasks: dailyTasks }, { title: 'Haftalık görevler', tasks: weeklyTasks }]" :key="group.title" class="card p-5">
          <h2 class="mb-3 flex items-center gap-2 font-bold text-slate-900 dark:text-white"><ListTodo class="h-5 w-5 text-brand-500" /> {{ group.title }}</h2>
          <ul class="space-y-3">
            <li v-for="task in group.tasks" :key="task.id">
              <div class="flex items-center justify-between gap-2 text-sm">
                <span class="font-bold" :class="task.completed ? 'text-aqua-700 dark:text-aqua-300' : 'text-slate-700 dark:text-slate-200'">
                  <CircleCheck v-if="task.completed" class="mr-1 inline h-4 w-4" />{{ task.title }}
                </span>
                <span class="shrink-0 text-xs font-bold tabular-nums text-slate-500">{{ task.progress }}/{{ task.target }} · +{{ task.points_reward }}</span>
              </div>
              <div class="mt-1 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                <div class="h-full rounded-full" :class="task.completed ? 'bg-aqua-600' : 'bg-brand-600 dark:bg-brand-500'" :style="{ width: `${(task.progress / task.target) * 100}%` }" />
              </div>
            </li>
          </ul>
        </article>
      </section>

      <!-- Rozetler -->
      <section v-if="g" class="card p-5">
        <div class="mb-4 flex items-center justify-between gap-2">
          <h2 class="flex items-center gap-2 font-bold text-slate-900 dark:text-white"><Award class="h-5 w-5 text-accent-600" /> Rozetler</h2>
          <span class="text-xs font-bold text-slate-500 dark:text-slate-400">{{ earnedCount }} / {{ g.badges.length }} kazanıldı · Seviye {{ g.points.level }} · {{ g.points.points }} puan</span>
        </div>
        <BadgeGrid :badges="g.badges" />
      </section>
    </template>
  </div>
</template>
