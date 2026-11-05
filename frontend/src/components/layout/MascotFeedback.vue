<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import OktopiMascot from './OktopiMascot.vue'
import { getMascot } from '@/assets/mascot'

/**
 * Bağlama göre değişen ahtapot geri bildirimi.
 *   welcome  → karşılama        correct  → doğru cevap
 *   badge    → rozet / hedef    struggle → zorlanma / hata
 * `message` verilmezse duruma uygun teşvik edici mesajlardan biri seçilir.
 */
const props = defineProps({
  state: { type: String, default: 'welcome', validator: (v) => ['welcome', 'correct', 'badge', 'struggle'].includes(v) },
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  name: { type: String, default: '' },
  compact: { type: Boolean, default: false },
  character: { type: String, default: '' },
})

const route = useRoute()
const mascot = computed(() => getMascot(props.character || route?.meta?.mascot))

const STATES = {
  welcome: {
    mood: 'welcome',
    tone: 'border-brand-200 bg-brand-50 dark:border-brand-500/30 dark:bg-brand-500/10',
    titles: ['Merhaba{name}', 'Tekrar hoş geldin{name}', 'Selam{name}'],
    messages: [
      'Bugün hangi konuya bakmak istersin?',
      'Kısa ama düzenli çalışmak, uzun ve seyrek çalışmaktan daha çok işe yarar.',
      'İstersen kaldığın yerden devam edebilirsin.',
    ],
  },
  correct: {
    mood: 'happy',
    tone: 'border-aqua-300 bg-aqua-50 dark:border-aqua-500/40 dark:bg-aqua-500/10',
    titles: ['Harikasın, böyle devam!', 'Doğru', 'Doğru cevap'],
    messages: [
      'Bu kavram oturmuş görünüyor.',
      'Doğru yoldan gittin.',
      'Bir sonraki soruya geçebilirsin.',
    ],
  },
  badge: {
    mood: 'celebrate',
    tone: 'border-accent-400/50 bg-accent-100 dark:border-accent-500/40 dark:bg-accent-600/15',
    titles: ['Tebrikler', 'Yeni bir rozet kazandın', 'Bir hedefi daha tamamladın'],
    messages: [
      'Çalışmanın karşılığını aldın.',
      'Bunu kendi çabanla kazandın.',
      'Hedefine bir adım daha yaklaştın.',
    ],
  },
  struggle: {
    mood: 'encourage',
    tone: 'border-rose-200 bg-rose-50 dark:border-rose-500/30 dark:bg-rose-500/10',
    titles: ['Bu kavramı birlikte tekrar inceleyelim', 'Burada takılmak normal', 'Bir daha bakalım'],
    messages: [
      'Yanlış cevap, neyi tekrar etmemiz gerektiğini gösterir. Adım adım bakalım.',
      'Bu noktada birçok kişi zorlanıyor. Konu özetine dönüp tekrar deneyelim.',
      'İkinci bakışta genelde daha net görünür.',
    ],
  },
}

const pick = (list) => Math.floor(Math.random() * list.length)
const index = ref({ title: 0, message: 0 })
watch(
  () => props.state,
  (state) => {
    const config = STATES[state]
    index.value = { title: pick(config.titles), message: pick(config.messages) }
  },
  { immediate: true },
)

const config = computed(() => STATES[props.state])
const titleText = computed(
  () => props.title || config.value.titles[index.value.title].replace('{name}', props.name ? ` ${props.name}` : ''),
)
const messageText = computed(() => props.message || config.value.messages[index.value.message])
</script>

<template>
  <div
    class="flex items-center gap-3 rounded-2xl border p-3 sm:gap-4"
    :class="[config.tone, compact ? '' : 'sm:p-4']"
    :role="state === 'struggle' || state === 'correct' ? 'status' : undefined"
  >
    <OktopiMascot :character="mascot.key" :mood="config.mood" :size="compact ? 56 : 80" class="shrink-0" />
    <div class="min-w-0 flex-1">
      <p v-if="!compact" class="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {{ mascot.name }} · {{ mascot.title }}
      </p>
      <p class="font-bold text-slate-900 dark:text-white" :class="compact ? 'text-sm' : 'text-base sm:text-lg'">
        {{ titleText }}
      </p>
      <p class="mt-0.5 text-slate-600 dark:text-slate-300" :class="compact ? 'text-xs sm:text-sm' : 'text-sm'">
        {{ messageText }}
      </p>
      <div v-if="$slots.default" class="mt-2 flex flex-wrap gap-2">
        <slot />
      </div>
    </div>
  </div>
</template>
