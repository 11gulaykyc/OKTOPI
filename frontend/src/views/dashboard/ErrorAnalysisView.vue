<script setup>
import { computed, ref, watch } from 'vue'
import { BookOpen, CircleCheck, Crosshair, FileQuestion, LoaderCircle, Map as MapIcon, Repeat, RotateCcw, TriangleAlert } from 'lucide-vue-next'
import MasteryMap from '@/components/dashboard/MasteryMap.vue'
import StatCard from '@/components/dashboard/StatCard.vue'
import MascotFeedback from '@/components/layout/MascotFeedback.vue'
import KatexRenderer from '@/components/math/KatexRenderer.vue'
import { errorMessage } from '@/services/api'
import { useGradeStore } from '@/stores/grade'
import { useStatsStore } from '@/stores/stats'
import { formatShortDate } from '@/utils/date'

/**
 * Hata Analizi ve Gelişim Haritası. Tüm hesaplar sunucuda gerçek cevaplardan yapılır.
 * Yeterli veri yoksa sonuçlar kesin tanı gibi sunulmaz.
 */
const stats = useStatsStore()
const gradeStore = useGradeStore()

const loading = ref(true)
const error = ref('')
const map = ref(null)
const analysis = ref(null)
const showAllMistakes = ref(false)
const showResolved = ref(false)

const MISTAKE_PREVIEW = 5

async function load(grade) {
  loading.value = true
  error.value = ''
  showAllMistakes.value = false
  try {
    const [mapData, analysisData] = await Promise.all([stats.fetchMasteryMap(grade), stats.fetchErrorAnalysis(grade)])
    map.value = mapData
    analysis.value = analysisData
  } catch (e) {
    error.value = errorMessage(e, 'Analiz verileri yüklenemedi.')
  } finally {
    loading.value = false
  }
}
watch(() => gradeStore.grade, load, { immediate: true })

const totals = computed(() => analysis.value?.totals)
const minAnswers = computed(() => analysis.value?.thresholds.min_answers_for_diagnosis ?? 5)
const openPatterns = computed(() => (analysis.value?.patterns ?? []).filter((p) => !p.resolved))
const resolvedPatterns = computed(() => (analysis.value?.patterns ?? []).filter((p) => p.resolved))
const mistakes = computed(() => analysis.value?.mistakes ?? [])
const visibleMistakes = computed(() => (showAllMistakes.value ? mistakes.value : mistakes.value.slice(0, MISTAKE_PREVIEW)))

function hunterLink(topicId) {
  return { name: 'practice', query: { hata: '1', ...(topicId ? { konu: topicId } : {}) } }
}

function summaryLink(rec) {
  return { name: 'topic-detail', params: { topicId: rec.topic_id }, query: rec.section_id ? { bolum: rec.section_id } : {} }
}
</script>

<template>
  <div class="space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">Hata Analizi</h1>
        <p class="text-slate-500 dark:text-slate-400">{{ gradeStore.grade }}. sınıf · konulardaki gelişimin ve tekrar eden kavram yanılgıların</p>
      </div>
      <RouterLink v-if="mistakes.length" :to="hunterLink()" class="btn-primary">
        <Crosshair class="h-4 w-4" /> Tüm yanlışlarımı tekrar çöz
      </RouterLink>
    </header>

    <div v-if="loading" class="flex items-center gap-2 text-slate-500"><LoaderCircle class="h-5 w-5 animate-spin" /> Analiz hazırlanıyor…</div>

    <div v-else-if="error" class="card p-5" role="alert">
      <p class="font-bold text-rose-600 dark:text-rose-400">{{ error }}</p>
      <button type="button" class="btn-secondary mt-3" @click="load(gradeStore.grade)"><RotateCcw class="h-4 w-4" /> Tekrar dene</button>
    </div>

    <template v-else>
      <!-- Dürüst geri bildirim: veri azken tanı koymuyoruz -->
      <MascotFeedback
        v-if="!analysis.enough_data"
        state="welcome"
        :title="totals.answered ? 'Analizin henüz netleşmedi' : 'Analiz için önce biraz soru çözelim'"
        :message="
          totals.answered
            ? `Bu sınıfta şimdiye kadar ${totals.answered} farklı soru çözdün. Aşağıdakiler kesin bir tanı değil, ilk izlenimler. Bu alanda daha fazla soru çözerek analizi netleştirebilirsin (en az ${minAnswers} soru).`
            : 'Çözdüğün sorular ve seçtiğin şıklar burada kavram yanılgısı örüntülerine dönüşecek. Birkaç soru çözerek başlayabilirsin.'
        "
      >
        <RouterLink to="/soru-coz" class="btn-secondary !py-1.5 text-xs"><FileQuestion class="h-4 w-4" /> Soru çöz</RouterLink>
      </MascotFeedback>
      <MascotFeedback
        v-else-if="!openPatterns.length && !mistakes.length"
        state="correct"
        title="Düzeltilecek yanlışın yok"
        message="Şu an açık bir kavram yanılgın görünmüyor. Yeni konulardan soru çözdükçe analiz güncellenecek."
      />

      <section class="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Çözülen soru" :value="totals.answered" hint="farklı soru, ilk deneme" :icon="FileQuestion" />
        <StatCard label="Düzeltilecek" :value="totals.open_mistakes" hint="son cevabı yanlış soru" :icon="Crosshair" tone="wine" />
        <StatCard label="Tekrarlayan" :value="totals.recurring_patterns" hint="açık yanılgı örüntüsü" :icon="Repeat" tone="accent" />
        <StatCard label="Tekrar et" :value="map.review.length" hint="konu" :icon="BookOpen" tone="aqua" />
      </section>

      <!-- Gelişim Haritası -->
      <section class="card p-5">
        <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white"><MapIcon class="h-5 w-5 text-brand-500" /> Gelişim Haritası</h2>
        <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
          Başarı oranı her sorunun yalnızca ilk cevabıyla hesaplanır. Bir konuda {{ minAnswers }} sorudan az çözdüysen “Veri az” görünür.
        </p>
        <div v-if="map.review.length" class="mb-5 rounded-xl bg-rose-50/70 p-3 dark:bg-rose-500/5">
          <p class="text-sm font-bold text-wine-600 dark:text-rose-300">Tekrar çalışman önerilen alanlar</p>
          <ul class="mt-2 flex flex-wrap gap-2">
            <li v-for="t in map.review" :key="t.id">
              <RouterLink
                :to="{ name: 'topic-detail', params: { topicId: t.id } }"
                class="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-sm font-semibold text-slate-700 shadow-sm hover:text-brand-600 dark:bg-slate-900 dark:text-slate-200"
              >
                {{ t.title }}
                <span v-if="t.open_mistakes" class="text-xs text-wine-600 dark:text-rose-300">· {{ t.open_mistakes }} yanlış</span>
              </RouterLink>
            </li>
          </ul>
        </div>
        <MasteryMap :map="map" />
      </section>

      <!-- Kavram yanılgısı örüntüleri -->
      <section class="card p-5">
        <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white"><TriangleAlert class="h-5 w-5 text-wine-500" /> Kavram yanılgıları</h2>
        <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">
          Seçtiğin yanlış şıkların hangi düşünce hatasından geldiği. Bir yanılgı en az {{ analysis.thresholds.min_repeats_for_pattern }} kez görülünce “tekrarlayan” sayılır.
        </p>
        <p v-if="!analysis.patterns.length" class="text-sm text-slate-500 dark:text-slate-400">Henüz kayıtlı bir kavram yanılgın yok.</p>
        <ul class="space-y-3">
          <li v-for="p in openPatterns" :key="p.tag" class="rounded-xl border border-slate-200 p-4 dark:border-slate-800">
            <div class="flex flex-wrap items-center gap-2 text-xs font-bold">
              <span v-if="p.recurring" class="rounded-full bg-rose-50 px-2 py-0.5 text-wine-600 dark:bg-rose-500/15 dark:text-rose-300">Tekrarlayan örüntü</span>
              <span v-else class="rounded-full bg-accent-100 px-2 py-0.5 text-accent-600 dark:bg-accent-600/20 dark:text-accent-400">Tek seferlik · henüz örüntü değil</span>
              <span class="text-slate-500 dark:text-slate-400">{{ p.count }} kez · {{ p.question_count }} soruda · son: {{ formatShortDate(p.last_seen) }}</span>
            </div>
            <KatexRenderer :text="p.detail" class="mt-2 font-semibold text-slate-800 dark:text-slate-100" />
            <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{{ p.topic_title }}</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <RouterLink v-if="p.recommended" :to="summaryLink(p.recommended)" class="btn-secondary !py-1.5 text-xs">
                <BookOpen class="h-4 w-4" /> Konu özeti: {{ p.recommended.title }}
              </RouterLink>
              <RouterLink :to="hunterLink(p.topic_id)" class="btn-ghost !py-1.5 text-xs"><Crosshair class="h-4 w-4" /> Hata Avcısı</RouterLink>
            </div>
          </li>
        </ul>
        <div v-if="resolvedPatterns.length" class="mt-4">
          <button type="button" class="btn-ghost !px-2 !py-1 text-xs" :aria-expanded="showResolved" @click="showResolved = !showResolved">
            <CircleCheck class="h-4 w-4 text-aqua-500" /> Aştığın yanılgılar ({{ resolvedPatterns.length }})
          </button>
          <ul v-if="showResolved" class="mt-2 space-y-2">
            <li v-for="p in resolvedPatterns" :key="p.tag" class="flex gap-2 rounded-xl bg-aqua-50/60 px-3 py-2 text-sm text-slate-600 dark:bg-aqua-500/5 dark:text-slate-300">
              <CircleCheck class="mt-0.5 h-4 w-4 shrink-0 text-aqua-500" />
              <KatexRenderer :text="p.detail" inline />
            </li>
          </ul>
        </div>
      </section>

      <!-- Düzeltilecek yanlışlar -->
      <section class="card p-5">
        <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white"><Crosshair class="h-5 w-5 text-wine-500" /> Düzeltilecek yanlışlar</h2>
        <p class="mb-4 text-sm text-slate-500 dark:text-slate-400">Doğru cevap burada gösterilmez; Hata Avcısı modunda yeniden çözüp kendini dene. Doğru çözdüğün soru listeden düşer.</p>
        <p v-if="!mistakes.length" class="text-sm text-slate-500 dark:text-slate-400">Bu sınıfta düzeltilecek yanlışın yok.</p>
        <ul class="space-y-3">
          <li v-for="m in visibleMistakes" :key="m.question_id" class="min-w-0 rounded-xl border border-slate-200 p-4 dark:border-slate-800">
            <p class="text-xs font-bold text-slate-500 dark:text-slate-400">{{ m.topic }} · {{ m.subtopic }}</p>
            <KatexRenderer :text="m.question_text" class="mt-1 text-slate-800 dark:text-slate-100" />
            <p class="mt-2 text-sm text-wine-600 dark:text-rose-300">
              Senin cevabın: <strong>{{ m.selected_option }})</strong> <KatexRenderer :text="m.selected_text" inline />
            </p>
            <p v-if="m.misconception" class="mt-1 text-sm text-slate-600 dark:text-slate-300">
              <KatexRenderer :text="m.misconception.detail" inline />
            </p>
            <div class="mt-3 flex flex-wrap gap-2">
              <RouterLink :to="hunterLink(m.topic_id)" class="btn-primary !py-1.5 text-xs"><Crosshair class="h-4 w-4" /> Hata Avcısı'nda tekrar çöz</RouterLink>
              <RouterLink v-if="m.recommended" :to="summaryLink(m.recommended)" class="btn-secondary !py-1.5 text-xs">
                <BookOpen class="h-4 w-4" /> Konu özetine git
              </RouterLink>
            </div>
          </li>
        </ul>
        <button v-if="mistakes.length > MISTAKE_PREVIEW && !showAllMistakes" type="button" class="btn-ghost mt-3 text-sm" @click="showAllMistakes = true">
          Tümünü göster ({{ mistakes.length }})
        </button>
      </section>
    </template>
  </div>
</template>
