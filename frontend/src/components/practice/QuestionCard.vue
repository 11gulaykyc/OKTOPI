<script setup>
import { CircleCheck, CircleX } from 'lucide-vue-next'
import KatexRenderer from '@/components/math/KatexRenderer.vue'

/**
 * Tek soru ve şıkları. `result` (sunucu değerlendirmesi) verilince doğru/yanlış işaretlenir;
 * verilmezse yalnızca seçim yapılır. Doğru şık bilgisi istemcide ancak `result` ile gelir.
 */
const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: String, default: '' },
  result: { type: Object, default: null },
  index: { type: Number, default: null },
  total: { type: Number, default: null },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const DIFFICULTY = { easy: 'Kolay', medium: 'Orta', hard: 'Zor' }

function optionClass(key) {
  const r = props.result
  if (!r) {
    return props.modelValue === key
      ? 'border-brand-500 bg-brand-50 ring-4 ring-brand-500/15 dark:bg-brand-500/10'
      : 'border-slate-200 hover:border-brand-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'
  }
  if (key === r.correct_option) return 'border-aqua-500 bg-aqua-50 dark:bg-aqua-500/10'
  if (key === r.selected_option) return 'border-rose-500 bg-rose-50 dark:bg-rose-500/10'
  return 'border-slate-200 opacity-60 dark:border-slate-700'
}

function select(key) {
  if (props.disabled || props.result) return
  emit('update:modelValue', key)
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-2 text-xs font-bold">
      <span v-if="index != null" class="rounded-full bg-brand-600 px-2.5 py-0.5 text-white">
        Soru {{ index }}<template v-if="total"> / {{ total }}</template>
      </span>
      <span class="rounded-full bg-slate-100 px-2.5 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ question.subtopic }}</span>
      <span class="rounded-full bg-slate-100 px-2.5 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ DIFFICULTY[question.difficulty] }}</span>
    </div>

    <KatexRenderer :text="question.question_text" class="mt-3 text-[15px] font-semibold text-slate-900 dark:text-white sm:text-base" />

    <fieldset class="mt-4" :disabled="disabled || !!result">
      <legend class="sr-only">Şıklar</legend>
      <div class="grid gap-2 sm:grid-cols-2">
        <label
          v-for="option in question.options"
          :key="option.key"
          class="flex min-h-12 cursor-pointer items-center gap-3 rounded-xl border-2 px-3 py-2 transition has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-brand-500"
          :class="[optionClass(option.key), result || disabled ? 'cursor-default' : '']"
        >
          <input
            type="radio"
            class="sr-only"
            :name="question.id"
            :value="option.key"
            :checked="modelValue === option.key || result?.selected_option === option.key"
            @change="select(option.key)"
          />
          <span
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-sm font-bold"
            :class="modelValue === option.key && !result ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'"
          >
            {{ option.key }}
          </span>
          <KatexRenderer :text="option.text" inline class="min-w-0 flex-1 text-sm text-slate-800 dark:text-slate-100" />
          <CircleCheck v-if="result && option.key === result.correct_option" class="h-5 w-5 shrink-0 text-aqua-600" aria-label="Doğru şık" />
          <CircleX v-else-if="result && option.key === result.selected_option" class="h-5 w-5 shrink-0 text-rose-600" aria-label="Senin seçimin" />
        </label>
      </div>
    </fieldset>
  </div>
</template>
