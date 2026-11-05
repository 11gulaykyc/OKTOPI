<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { getMascot } from '@/assets/mascot'

/**
 * Bölüme göre değişen ahtapot maskotu.
 * `character` verilmezse aktif rotanın `meta.mascot` değeri, o da yoksa Kaptan Pusula kullanılır.
 * `mood` → animasyon + durum balonu (görsel her durumda aynıdır).
 */
const props = defineProps({
  mood: { type: String, default: 'welcome' },
  size: { type: [Number, String], default: 120 },
  character: { type: String, default: '' },
  badge: { type: Boolean, default: true },
})

const route = useRoute()
const mascot = computed(() => getMascot(props.character || route?.meta?.mascot))

const moodLabels = {
  welcome: 'el sallıyor',
  happy: 'mutlu',
  celebrate: 'kutlama yapıyor',
  thinking: 'düşünüyor',
  encourage: 'cesaret veriyor',
}
const alt = computed(() => `${mascot.value.name} ${moodLabels[props.mood] ?? ''}`.trim())
const px = computed(() => Number(props.size))
// Çok küçük boyutlarda (ör. navbar logosu) balon ve animasyon gösterilmez.
const showBadge = computed(() => props.badge && px.value >= 56 && props.mood !== 'welcome')
</script>

<template>
  <div
    class="mascot relative inline-block shrink-0 select-none"
    :class="px >= 56 ? `mascot--${mood}` : ''"
    :style="{ width: `${px}px`, height: `${px}px` }"
    role="img"
    :aria-label="alt"
  >
    <img :src="mascot.image" alt="" :width="px" :height="px" class="mascot__img h-full w-full object-contain" draggable="false" />

    <span
      v-if="showBadge"
      class="mascot__badge absolute right-0 top-0 grid place-items-center rounded-full shadow-md ring-2 ring-white dark:ring-slate-900"
      :class="{
        'bg-aqua-500 text-white': mood === 'happy',
        'bg-amber-400 text-white': mood === 'celebrate',
        'bg-accent-500 text-white': mood === 'thinking',
        'bg-rose-500 text-white': mood === 'encourage',
      }"
      :style="{ width: `${Math.round(px * 0.28)}px`, height: `${Math.round(px * 0.28)}px` }"
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" class="h-3/5 w-3/5" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
        <path v-if="mood === 'happy'" d="M5 12.5l4.5 4.5L19 7.5" />
        <path v-else-if="mood === 'celebrate'" fill="currentColor" stroke-width="1.5" d="M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.4 6.7 19.4l1.2-6L3.4 9.3l6-.7z" />
        <template v-else-if="mood === 'thinking'">
          <path d="M9 9a3 3 0 1 1 4.2 2.8c-.8.4-1.2 1-1.2 1.8v.6" />
          <circle cx="12" cy="18" r="0.6" fill="currentColor" />
        </template>
        <path v-else-if="mood === 'encourage'" fill="currentColor" stroke-width="1.5" d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />
      </svg>
    </span>

    <template v-if="mood === 'celebrate' && px >= 56">
      <span class="mascot__spark mascot__spark--1" aria-hidden="true" />
      <span class="mascot__spark mascot__spark--2" aria-hidden="true" />
      <span class="mascot__spark mascot__spark--3" aria-hidden="true" />
    </template>
  </div>
</template>

<style scoped>
.mascot__img {
  filter: drop-shadow(0 6px 10px rgb(15 23 42 / 0.18));
  transform-origin: 50% 90%;
}
.mascot--welcome .mascot__img {
  animation: sway 3.2s ease-in-out infinite;
}
.mascot--happy .mascot__img {
  animation: hop 1.4s ease-in-out infinite;
}
.mascot--celebrate .mascot__img {
  animation: hop 0.9s ease-in-out infinite;
}
.mascot--thinking .mascot__img {
  animation: tilt 3s ease-in-out infinite;
}
.mascot--encourage .mascot__img {
  animation: breathe 2.6s ease-in-out infinite;
}
.mascot__badge {
  animation: pop 0.35s ease-out both, bob 2s 0.35s ease-in-out infinite;
}
.mascot__spark {
  position: absolute;
  width: 9%;
  aspect-ratio: 1;
  border-radius: 9999px;
  animation: twinkle 1.4s ease-in-out infinite;
}
.mascot__spark--1 {
  left: 4%;
  top: 14%;
  background: #facc15;
}
.mascot__spark--2 {
  right: 30%;
  top: 0;
  background: #14b8a6;
  animation-delay: 0.45s;
}
.mascot__spark--3 {
  left: 18%;
  bottom: 18%;
  background: #a855f7;
  animation-delay: 0.9s;
}
@keyframes sway {
  0%,
  100% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(-3deg);
  }
}
@keyframes hop {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  40% {
    transform: translateY(-6%) scale(1.02);
  }
}
@keyframes tilt {
  0%,
  100% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(4deg);
  }
}
@keyframes breathe {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.03);
  }
}
@keyframes bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}
@keyframes pop {
  from {
    transform: scale(0);
  }
  to {
    transform: scale(1);
  }
}
@keyframes twinkle {
  0%,
  100% {
    opacity: 0;
    transform: scale(0.4);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}
@media (prefers-reduced-motion: reduce) {
  .mascot__img,
  .mascot__badge,
  .mascot__spark {
    animation: none !important;
  }
  .mascot__spark {
    opacity: 1;
  }
}
</style>
