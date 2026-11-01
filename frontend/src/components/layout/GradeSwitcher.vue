<script setup>
import { GRADES, useGradeStore } from '@/stores/grade'

defineProps({ block: { type: Boolean, default: false } })

const gradeStore = useGradeStore()
</script>

<template>
  <div
    role="radiogroup"
    aria-label="Sınıf seçici"
    class="inline-flex rounded-xl border border-slate-200 bg-slate-100 p-0.5 dark:border-slate-700 dark:bg-slate-800"
    :class="{ 'flex w-full': block }"
  >
    <button
      v-for="g in GRADES"
      :key="g"
      type="button"
      role="radio"
      :aria-checked="gradeStore.grade === g"
      :title="g === gradeStore.ownGrade ? `${g}. sınıf (senin sınıfın)` : `${g}. sınıf içeriklerine geç`"
      class="relative rounded-[10px] px-2.5 py-1.5 text-xs font-bold transition sm:px-3"
      :class="[
        block ? 'flex-1' : '',
        gradeStore.grade === g
          ? 'bg-white text-brand-700 shadow-sm dark:bg-slate-950 dark:text-brand-300'
          : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white',
      ]"
      @click="gradeStore.setGrade(g)"
    >
      {{ g }}<span class="hidden sm:inline">. Sınıf</span>
      <span
        v-if="g === gradeStore.ownGrade"
        class="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-aqua-500"
        aria-hidden="true"
      />
    </button>
  </div>
</template>
