<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowRight, CircleCheck, CircleX, LoaderCircle, RotateCcw } from 'lucide-vue-next'
import RewardNotice from '@/components/dashboard/RewardNotice.vue'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import KatexRenderer from '@/components/math/KatexRenderer.vue'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  question: { type: Object, required: true },
  index: { type: Number, default: 1 },
})
const emit = defineEmits(['answered', 'go-to-section'])

const auth = useAuthStore()
const route = useRoute()

const selected = ref('')
const result = ref(null)
const loading = ref(false)
const error = ref('')

const DIFFICULTY = { easy: 'Kolay', medium: 'Orta', hard: 'Zor' }

// Cevap anahtarı istemcide yoktur; doğru şık ve çözüm yalnızca sunucu değerlendirmesinden sonra gelir.
async function check() {
  if (!selected.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.post(`/questions/${props.question.id}/check/`, { selected_option: selected.value })
    result.value = data
    emit('answered', data)
  } catch (e) {
    error.value = errorMessage(e, 'Cevabın kontrol edilemedi. Tekrar dene.')
  } finally {
    loading.value = false
  }
}

function retry() {
  selected.value = ''
  result.value = null
}

function optionClass(key) {
  const r = result.value
  if (!r) {
    return selected.value === key
      ? 'border-brand-500 bg-brand-50 ring-4 ring-brand-500/15 dark:bg-brand-500/10'
      : 'border-slate-200 hover:border-brand-300 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'
  }
  if (key === r.correct_option) return 'border-aqua-500 bg-aqua-50 dark:bg-aqua-500/10'
  if (key === r.selected_option) return 'border-rose-500 bg-rose-50 dark:bg-rose-500/10'
  return 'border-slate-200 opacity-60 dark:border-slate-700'
}

const recommended = computed(() => result.value?.misconception?.recommended)
</script>

<template>
  <article class="card p-4 sm:p-5">
    <div class="flex flex-wrap items-center gap-2 text-xs font-bold">
      <span class="rounded-full bg-brand-600 px-2.5 py-0.5 text-white">Soru {{ index }}</span>
      <span class="rounded-full bg-slate-100 px-2.5 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ question.subtopic }}</span>
      <span class="rounded-full bg-slate-100 px-2.5 py-0.5 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ DIFFICULTY[question.difficulty] }}</span>
    </div>

    <KatexRenderer :text="question.question_text" class="mt-3 font-semibold text-slate-900 dark:text-white" />

    <fieldset class="mt-4" :disabled="!!result || loading">
      <legend class="sr-only">Şıklar</legend>
      <div class="grid gap-2 sm:grid-cols-2">
        <label
          v-for="option in question.options"
          :key="option.key"
          class="flex min-h-12 cursor-pointer items-center gap-3 rounded-xl border-2 px-3 py-2 transition has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-brand-500"
          :class="[optionClass(option.key), result ? 'cursor-default' : '']"
        >
          <input v-model="selected" type="radio" class="sr-only" :name="question.id" :value="option.key" />
          <span
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-sm font-bold"
            :class="selected === option.key && !result ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'"
          >
            {{ option.key }}
          </span>
          <KatexRenderer :text="option.text" inline class="min-w-0 flex-1 text-sm text-slate-800 dark:text-slate-100" />
          <CircleCheck v-if="result && option.key === result.correct_option" class="h-5 w-5 shrink-0 text-aqua-600" aria-label="Doğru şık" />
          <CircleX v-else-if="result && option.key === result.selected_option" class="h-5 w-5 shrink-0 text-rose-600" aria-label="Senin seçimin" />
        </label>
      </div>
    </fieldset>

    <p v-if="error" class="mt-3 text-sm font-semibold text-rose-600 dark:text-rose-400" role="alert">{{ error }}</p>

    <!-- Ziyaretçi: cevap kontrolü sunucuda giriş gerektirir (cevap anahtarı deneme yoluyla bile açılmaz). -->
    <div
      v-if="!auth.isAuthenticated"
      class="mt-4 flex flex-col gap-3 rounded-lg bg-slate-50 px-4 py-3 text-sm dark:bg-slate-800/60 sm:flex-row sm:items-center sm:justify-between"
    >
      <p class="text-slate-600 dark:text-slate-300">Cevabını görmek için kayıt ol.</p>
      <div class="flex shrink-0 gap-2">
        <RouterLink :to="{ name: 'login', query: { next: route.fullPath } }" class="btn-ghost !py-1.5">Giriş yap</RouterLink>
        <RouterLink to="/kayit" class="btn-primary !py-1.5">Kayıt ol</RouterLink>
      </div>
    </div>

    <div v-else-if="!result" class="mt-4 flex justify-end">
      <button type="button" class="btn-primary" :disabled="!selected || loading" @click="check">
        <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
        Cevabı kontrol et
      </button>
    </div>

    <div v-else class="mt-4 space-y-3">
      <MascotFeedback v-if="result.is_correct" state="correct" compact />
      <MascotFeedback
        v-else
        state="struggle"
        compact
        :message="result.misconception?.detail || 'Doğru cevabı ve çözümü aşağıda inceleyebilirsin.'"
      >
        <button v-if="recommended" type="button" class="btn-secondary !py-1.5 text-xs" @click="emit('go-to-section', recommended)">
          <ArrowRight class="h-3.5 w-3.5" /> “{{ recommended.title }}” özetine git
        </button>
      </MascotFeedback>
      <RewardNotice :rewards="result.rewards" compact />

      <details class="rounded-xl border border-slate-200 p-3 dark:border-slate-700" :open="!result.is_correct">
        <summary class="cursor-pointer text-sm font-bold text-slate-800 dark:text-slate-100">Adım adım çözüm</summary>
        <KatexRenderer :text="result.step_by_step_solution" class="mt-2 text-sm text-slate-700 dark:text-slate-200" />
      </details>

      <div class="flex justify-end">
        <button type="button" class="btn-ghost !py-2" @click="retry"><RotateCcw class="h-4 w-4" /> Tekrar dene</button>
      </div>
      <p v-if="result.first_try === false" class="text-right text-xs text-slate-500 dark:text-slate-400">
        Tekrar denemeler konu başarı oranını değiştirmez; ilk cevabın sayılır.
      </p>
    </div>
  </article>
</template>
