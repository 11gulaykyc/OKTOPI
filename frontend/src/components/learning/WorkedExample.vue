<script setup>
import { computed, ref } from 'vue'
import { ChevronRight, Eye, RotateCcw } from 'lucide-vue-next'
import KatexRenderer from '@/components/math/KatexRenderer.vue'

const props = defineProps({
  example: { type: Object, required: true },
  index: { type: Number, default: 1 },
})

// Öğrenci önce kendisi düşünsün diye adımlar tek tek açılır.
const shown = ref(0)
const total = computed(() => props.example.steps.length)
const finished = computed(() => shown.value >= total.value)
</script>

<template>
  <article class="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 dark:border-slate-700 dark:bg-slate-800/40 sm:p-5">
    <p class="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">Örnek {{ index }} · {{ example.title }}</p>
    <KatexRenderer :text="example.problem" class="mt-2 font-semibold text-slate-900 dark:text-white" />

    <ol v-if="shown" class="mt-4 space-y-2">
      <li v-for="(step, i) in example.steps.slice(0, shown)" :key="i" class="flex gap-3">
        <span class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
          {{ i + 1 }}
        </span>
        <KatexRenderer :text="step" class="min-w-0 flex-1 text-sm text-slate-700 dark:text-slate-200" />
      </li>
    </ol>

    <div
      v-if="finished"
      class="mt-4 flex flex-wrap items-center gap-2 rounded-xl bg-aqua-50 px-3 py-2 text-sm font-bold text-aqua-700 dark:bg-aqua-500/10 dark:text-aqua-300"
    >
      Cevap: <KatexRenderer :text="example.answer" inline />
    </div>

    <div class="mt-4 flex flex-wrap gap-2">
      <button v-if="!finished" type="button" class="btn-secondary !py-2" @click="shown++">
        <component :is="shown ? ChevronRight : Eye" class="h-4 w-4" />
        {{ shown ? `Sonraki adım (${shown}/${total})` : 'Çözümü adım adım göster' }}
      </button>
      <button v-if="!finished && shown" type="button" class="btn-ghost !py-2" @click="shown = total">Tümünü göster</button>
      <button v-if="finished" type="button" class="btn-ghost !py-2" @click="shown = 0">
        <RotateCcw class="h-4 w-4" /> Gizle
      </button>
    </div>
  </article>
</template>
