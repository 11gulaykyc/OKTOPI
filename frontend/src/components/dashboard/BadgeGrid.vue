<script setup>
import { Lock } from 'lucide-vue-next'
import { badgeIcon } from './badgeIcons'

defineProps({
  badges: { type: Array, required: true },
  compact: { type: Boolean, default: false },
})

const formatDate = (iso) => new Date(iso).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })
</script>

<template>
  <ul class="grid gap-3" :class="compact ? 'grid-cols-4 sm:grid-cols-7' : 'grid-cols-1 min-[480px]:grid-cols-2 lg:grid-cols-3'">
    <li
      v-for="badge in badges"
      :key="badge.code"
      :title="compact ? `${badge.name}: ${badge.description}` : undefined"
      class="flex items-center gap-3 rounded-xl border p-3"
      :class="[
        badge.earned
          ? 'border-accent-400/50 bg-accent-100/60 dark:border-accent-500/40 dark:bg-accent-600/10'
          : 'border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900',
        compact ? 'flex-col justify-center gap-1.5 !p-2 text-center' : '',
      ]"
    >
      <span
        class="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-full"
        :class="badge.earned ? 'bg-accent-600 text-white dark:bg-accent-500' : 'bg-slate-200 text-slate-400 dark:bg-slate-800 dark:text-slate-500'"
      >
        <component :is="badgeIcon(badge.icon)" class="h-5 w-5" aria-hidden="true" />
        <Lock v-if="!badge.earned" class="absolute -bottom-0.5 -right-0.5 h-4 w-4 rounded-full bg-white p-0.5 text-slate-500 dark:bg-slate-900" aria-hidden="true" />
      </span>
      <span v-if="compact" class="text-[11px] font-bold leading-tight" :class="badge.earned ? 'text-slate-800 dark:text-slate-100' : 'text-slate-400'">
        {{ badge.name }}
      </span>
      <span v-else class="min-w-0">
        <span class="block text-sm font-bold" :class="badge.earned ? 'text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400'">
          {{ badge.name }}
          <span class="sr-only">{{ badge.earned ? '(kazanıldı)' : '(henüz kazanılmadı)' }}</span>
        </span>
        <span class="block text-xs text-slate-500 dark:text-slate-400">{{ badge.description }}</span>
        <span class="mt-0.5 block text-[11px] font-semibold" :class="badge.earned ? 'text-accent-600 dark:text-accent-400' : 'text-slate-400'">
          {{ badge.earned ? `${formatDate(badge.awarded_at)} tarihinde kazandın` : `+${badge.points_reward} puan` }}
        </span>
      </span>
    </li>
  </ul>
</template>
