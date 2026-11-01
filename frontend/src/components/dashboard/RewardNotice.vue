<script setup>
import { computed } from 'vue'
import { CircleCheck, Sparkles, Target } from 'lucide-vue-next'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'

/**
 * Sunucunun döndürdüğü ödülleri ({ points, badges, tasks, goals }) gösterir.
 * Rozet veya hedef/görev tamamlandıysa maskot kutlar; yalnızca puan varsa küçük bir etiket görünür.
 */
const props = defineProps({
  rewards: { type: Object, default: null },
  compact: { type: Boolean, default: false },
})

const r = computed(() => props.rewards || { points: 0, badges: [], tasks: [], goals: [] })
const celebrate = computed(() => r.value.badges?.length || r.value.tasks?.length || r.value.goals?.length)

const title = computed(() => {
  const badges = r.value.badges || []
  if (badges.length === 1) return `Yeni rozet: ${badges[0].name}`
  if (badges.length > 1) return `${badges.length} yeni rozet kazandın`
  if (r.value.goals?.length) return 'Günlük hedefini tamamladın'
  return 'Bir görevi tamamladın'
})
const message = computed(() => {
  const badges = r.value.badges || []
  if (badges.length === 1) return badges[0].description
  if (badges.length > 1) return badges.map((b) => b.name).join(', ')
  return ''
})
</script>

<template>
  <MascotFeedback v-if="celebrate" state="badge" :title="title" :message="message" :compact="compact">
    <span v-if="r.points" class="inline-flex items-center gap-1 rounded-full bg-accent-600 px-2.5 py-0.5 text-xs font-bold text-white dark:bg-accent-500">
      <Sparkles class="h-3.5 w-3.5" /> +{{ r.points }} puan
    </span>
    <span
      v-for="task in r.tasks"
      :key="task.id"
      class="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-0.5 text-xs font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
    >
      <CircleCheck class="h-3.5 w-3.5 text-aqua-600" /> {{ task.title }}
    </span>
    <span
      v-for="goal in r.goals"
      :key="goal.goal_type"
      class="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-0.5 text-xs font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-200"
    >
      <Target class="h-3.5 w-3.5 text-aqua-600" /> {{ goal.label }}: {{ goal.target }}
    </span>
  </MascotFeedback>
  <p
    v-else-if="r.points"
    class="inline-flex items-center gap-1 rounded-full bg-accent-100 px-2.5 py-0.5 text-xs font-bold text-accent-600 dark:bg-accent-600/20 dark:text-accent-400"
    role="status"
  >
    <Sparkles class="h-3.5 w-3.5" /> +{{ r.points }} puan
  </p>
</template>
