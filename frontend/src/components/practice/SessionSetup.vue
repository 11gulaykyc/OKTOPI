<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Crosshair, LoaderCircle, Play } from 'lucide-vue-next'
import { errorMessage } from '@/services/api'
import { useContentStore } from '@/stores/content'
import { useGradeStore } from '@/stores/grade'

/**
 * Soru çözümü / süreli test başlatma formu. Konu listesi göz atılan sınıfın müfredatından gelir;
 * yalnızca soru havuzunda sorusu olan konular seçilebilir.
 */
const props = defineProps({
  mode: { type: String, required: true, validator: (v) => ['practice', 'timed'].includes(v) },
  loading: { type: Boolean, default: false },
  initialTopic: { type: String, default: '' },
  initialMistakes: { type: Boolean, default: false },
})
const emit = defineEmits(['start'])

const content = useContentStore()
const gradeStore = useGradeStore()

const curriculum = ref(null)
const loadError = ref('')
const form = reactive({
  topic_id: props.initialTopic,
  difficulty: '',
  count: 10,
  duration_minutes: null,
  mistakes_only: props.initialMistakes,
})

watch(
  () => gradeStore.grade,
  async (grade) => {
    loadError.value = ''
    try {
      curriculum.value = await content.fetchGrade(grade)
      if (form.topic_id && !topics.value.some((t) => t.id === form.topic_id)) form.topic_id = ''
    } catch (e) {
      loadError.value = errorMessage(e, 'Konular yüklenemedi.')
    }
  },
  { immediate: true },
)

const topics = computed(() =>
  (curriculum.value?.themes ?? []).flatMap((theme) => theme.topics.filter((t) => t.question_count > 0)),
)
const available = computed(() => {
  if (form.topic_id) return topics.value.find((t) => t.id === form.topic_id)?.question_count ?? 0
  return topics.value.reduce((sum, t) => sum + t.question_count, 0)
})
const defaultMinutes = computed(() => Math.max(1, Math.ceil((Math.min(form.count, available.value || form.count) * 90) / 60)))

function submit() {
  const payload = { grade: gradeStore.grade, topic_id: form.topic_id, difficulty: form.difficulty, count: Number(form.count) }
  if (props.mode === 'practice') payload.mistakes_only = form.mistakes_only
  if (props.mode === 'timed' && form.duration_minutes) payload.duration_minutes = Number(form.duration_minutes)
  emit('start', payload)
}
</script>

<template>
  <form class="card space-y-4 p-5" @submit.prevent="submit">
    <p v-if="loadError" class="text-sm font-semibold text-rose-600 dark:text-rose-400" role="alert">{{ loadError }}</p>

    <div v-if="curriculum && !topics.length" class="rounded-xl bg-slate-50 p-4 text-sm text-slate-600 dark:bg-slate-800/50 dark:text-slate-300">
      {{ gradeStore.grade }}. sınıf için soru havuzu henüz hazırlanıyor. Üst bardan başka bir sınıf seçebilirsin.
    </div>

    <template v-else>
      <div class="grid gap-4 sm:grid-cols-2">
        <div class="sm:col-span-2">
          <label class="field-label" for="setup-topic">Konu</label>
          <select id="setup-topic" v-model="form.topic_id" class="field-input">
            <option value="">{{ gradeStore.grade }}. sınıf · tüm konular karışık</option>
            <option v-for="t in topics" :key="t.id" :value="t.id">{{ t.title }} ({{ t.question_count }} soru)</option>
          </select>
        </div>
        <div>
          <label class="field-label" for="setup-difficulty">Zorluk</label>
          <select id="setup-difficulty" v-model="form.difficulty" class="field-input">
            <option value="">Karışık</option>
            <option value="easy">Kolay</option>
            <option value="medium">Orta</option>
            <option value="hard">Zor</option>
          </select>
        </div>
        <div>
          <label class="field-label" for="setup-count">Soru sayısı</label>
          <input id="setup-count" v-model.number="form.count" type="number" min="1" max="30" class="field-input" />
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">Havuzda bu seçime uygun en fazla {{ available }} soru var.</p>
        </div>
        <div v-if="mode === 'timed'" class="sm:col-span-2">
          <label class="field-label" for="setup-duration">Süre (dakika)</label>
          <input
            id="setup-duration"
            v-model.number="form.duration_minutes"
            type="number"
            min="1"
            max="120"
            class="field-input"
            :placeholder="`Varsayılan: ${defaultMinutes} dk (soru başına 1,5 dk)`"
          />
        </div>
      </div>

      <label
        v-if="mode === 'practice'"
        class="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 p-3 text-sm has-[:checked]:border-wine-500 has-[:checked]:bg-rose-50 dark:border-slate-700 dark:has-[:checked]:bg-rose-500/10"
      >
        <input v-model="form.mistakes_only" type="checkbox" class="mt-0.5 h-4 w-4 accent-wine-600" />
        <span>
          <span class="flex items-center gap-1.5 font-bold text-slate-800 dark:text-slate-100"><Crosshair class="h-4 w-4 text-wine-600" /> Hata Avcısı modu</span>
          <span class="text-slate-500 dark:text-slate-400">Yalnızca daha önce yanlış yaptığın ve henüz doğru çözmediğin sorular gelsin.</span>
        </span>
      </label>

      <div class="flex justify-end">
        <button type="submit" class="btn-primary" :disabled="loading || !curriculum">
          <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
          <Play v-else class="h-4 w-4" />
          {{ mode === 'timed' ? 'Testi başlat' : 'Çözmeye başla' }}
        </button>
      </div>
    </template>
  </form>
</template>
