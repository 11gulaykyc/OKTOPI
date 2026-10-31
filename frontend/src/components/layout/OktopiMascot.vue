<script setup>
import { computed } from 'vue'
import { MASCOT_IMAGES } from '@/assets/mascot'

const props = defineProps({
  mood: { type: String, default: 'welcome' },
  size: { type: [Number, String], default: 120 },
})

const image = computed(() => MASCOT_IMAGES[props.mood] ?? null)
const uid = `m${Math.random().toString(36).slice(2, 8)}`

const moodLabels = {
  welcome: 'el sallıyor',
  happy: 'mutlu',
  celebrate: 'kutlama yapıyor',
  thinking: 'düşünüyor',
  encourage: 'cesaret veriyor',
}
const alt = computed(() => `Oktopi ahtapot ${moodLabels[props.mood] ?? ''}`.trim())
</script>

<template>
  <img v-if="image" :src="image" :alt="alt" :width="size" :height="size" class="select-none object-contain" />
  <svg
    v-else
    :width="size"
    :height="size"
    viewBox="0 0 200 200"
    role="img"
    :aria-label="alt"
    class="mascot select-none"
    :class="`mascot--${mood}`"
  >
    <defs>
      <radialGradient :id="`${uid}-body`" cx="0.38" cy="0.3" r="0.8">
        <stop offset="0" stop-color="#60A5FA" />
        <stop offset="0.55" stop-color="#2563EB" />
        <stop offset="1" stop-color="#1E3A8A" />
      </radialGradient>
      <linearGradient :id="`${uid}-arm`" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#2563EB" />
        <stop offset="1" stop-color="#14B8A6" />
      </linearGradient>
    </defs>

    <!-- Gölge -->
    <ellipse cx="100" cy="188" rx="58" ry="7" fill="currentColor" opacity="0.08" />

    <!-- Kollar -->
    <g :stroke="`url(#${uid}-arm)`" stroke-width="15" stroke-linecap="round" fill="none">
      <path d="M58 118 C40 138 30 150 36 172" />
      <path d="M76 128 C68 150 62 162 70 180" />
      <path d="M124 128 C132 150 138 162 130 180" />
      <path d="M142 118 C160 138 170 150 164 172" />
      <path v-if="mood === 'welcome' || mood === 'celebrate'" class="wave" d="M150 98 C172 88 180 66 172 44" />
      <path v-else d="M150 104 C170 116 178 128 176 146" />
      <path v-if="mood === 'celebrate'" class="wave-alt" d="M50 98 C28 88 20 66 28 44" />
      <path v-else-if="mood === 'thinking'" d="M54 108 C40 112 44 96 62 92" />
      <path v-else d="M50 104 C30 116 22 128 24 146" />
    </g>
    <!-- Vantuz noktaları -->
    <g fill="#CCFBF1" opacity="0.8">
      <circle cx="38" cy="160" r="3" />
      <circle cx="68" cy="166" r="3" />
      <circle cx="132" cy="166" r="3" />
      <circle cx="162" cy="160" r="3" />
    </g>

    <!-- Gövde -->
    <path d="M100 22 C146 22 162 58 160 88 C158 116 136 132 100 132 C64 132 42 116 40 88 C38 58 54 22 100 22 Z" :fill="`url(#${uid}-body)`" />
    <ellipse cx="78" cy="48" rx="16" ry="9" fill="#fff" opacity="0.25" transform="rotate(-20 78 48)" />

    <!-- Yanaklar -->
    <ellipse cx="66" cy="98" rx="10" ry="6" fill="#F472B6" opacity="0.45" />
    <ellipse cx="134" cy="98" rx="10" ry="6" fill="#F472B6" opacity="0.45" />

    <!-- Gözler -->
    <template v-if="mood === 'happy' || mood === 'celebrate'">
      <path d="M68 80 Q78 68 88 80" stroke="#0F172A" stroke-width="5" fill="none" stroke-linecap="round" />
      <path d="M112 80 Q122 68 132 80" stroke="#0F172A" stroke-width="5" fill="none" stroke-linecap="round" />
    </template>
    <template v-else>
      <circle cx="78" cy="78" r="14" fill="#fff" />
      <circle cx="122" cy="78" r="14" fill="#fff" />
      <g class="pupils" :transform="mood === 'thinking' ? 'translate(4 -5)' : ''">
        <circle cx="80" cy="80" r="7" fill="#0F172A" />
        <circle cx="124" cy="80" r="7" fill="#0F172A" />
        <circle cx="83" cy="77" r="2.4" fill="#fff" />
        <circle cx="127" cy="77" r="2.4" fill="#fff" />
      </g>
      <template v-if="mood === 'encourage'">
        <path d="M64 60 L88 64" stroke="#0F172A" stroke-width="4" stroke-linecap="round" />
        <path d="M136 60 L112 64" stroke="#0F172A" stroke-width="4" stroke-linecap="round" />
      </template>
    </template>

    <!-- Ağız -->
    <path v-if="mood === 'thinking'" d="M92 108 Q100 104 108 108" stroke="#0F172A" stroke-width="4" fill="none" stroke-linecap="round" />
    <ellipse v-else-if="mood === 'celebrate'" cx="100" cy="106" rx="11" ry="9" fill="#0F172A" />
    <path v-else d="M86 102 Q100 116 114 102" stroke="#0F172A" stroke-width="4.5" fill="none" stroke-linecap="round" />

    <!-- Durum süslemeleri -->
    <g v-if="mood === 'celebrate'" class="sparkles" fill="#FACC15">
      <path d="M30 26 l4 9 9 4 -9 4 -4 9 -4 -9 -9 -4 9 -4z" />
      <path d="M170 18 l3 7 7 3 -7 3 -3 7 -3 -7 -7 -3 7 -3z" />
      <circle cx="186" cy="60" r="4" fill="#A855F7" />
      <circle cx="14" cy="70" r="4" fill="#14B8A6" />
    </g>
    <text v-if="mood === 'thinking'" x="160" y="40" font-size="34" font-weight="800" fill="#A855F7" class="bob">?</text>
    <path
      v-if="mood === 'encourage'"
      class="bob"
      d="M168 44 c-6 -10 -20 -4 -14 8 l14 14 14 -14 c6 -12 -8 -18 -14 -8z"
      fill="#F43F5E"
    />
  </svg>
</template>

<style scoped>
.mascot {
  overflow: visible;
}
.wave {
  transform-origin: 150px 100px;
  animation: wave 1.6s ease-in-out infinite;
}
.wave-alt {
  transform-origin: 50px 100px;
  animation: wave 1.6s ease-in-out infinite reverse;
}
.bob,
.sparkles {
  animation: bob 2s ease-in-out infinite;
}
@keyframes wave {
  0%,
  100% {
    transform: rotate(0deg);
  }
  50% {
    transform: rotate(-14deg);
  }
}
@keyframes bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .wave,
  .wave-alt,
  .bob,
  .sparkles {
    animation: none;
  }
}
</style>
