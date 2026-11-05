<script setup>
/**
 * Uygulama içi sayfaların sabit okyanus arka planı. Katmanlar (alttan üste):
 *   1. Baloncuksuz okyanus görseli
 *   2. Yavaşça salınan ışık huzmeleri (derinlik / 3B hissi)
 *   3. Kenarlarda hafif koyulaşma (vinyet)
 *   4. Okunabilirlik perdesi (açık temada beyaz, koyu temada lacivert)
 *   5. Hareketli baloncuklar (OceanBubbles)
 */
import appBackground from '@/assets/backgrounds/app-ocean.webp'
import OceanBubbles from './OceanBubbles.vue'

// Huzmeler sabit tohum değerleriyle tanımlanır; her açılışta aynı, doğal görünen düzen.
const rays = [
  { left: 18, width: 70, angle: 24, duration: 11, delay: -2, opacity: 0.55 },
  { left: 30, width: 120, angle: 20, duration: 14, delay: -6, opacity: 0.7 },
  { left: 41, width: 55, angle: 17, duration: 9, delay: -1, opacity: 0.5 },
  { left: 49, width: 150, angle: 14, duration: 16, delay: -9, opacity: 0.85 },
  { left: 58, width: 80, angle: 11, duration: 12, delay: -4, opacity: 0.6 },
  { left: 66, width: 110, angle: 8, duration: 15, delay: -7, opacity: 0.55 },
  { left: 77, width: 60, angle: 5, duration: 10, delay: -3, opacity: 0.45 },
]
</script>

<template>
  <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
    <img :src="appBackground" alt="" class="h-full w-full object-cover" />

    <div class="ocean-rays absolute inset-0">
      <span
        v-for="(ray, i) in rays"
        :key="i"
        class="ocean-ray"
        :style="{
          left: `${ray.left}%`,
          width: `${ray.width}px`,
          '--angle': `${ray.angle}deg`,
          '--peak': ray.opacity,
          animationDuration: `${ray.duration}s`,
          animationDelay: `${ray.delay}s`,
        }"
      />
    </div>

    <div class="ocean-vignette absolute inset-0" />
    <div class="absolute inset-0 bg-white/70 dark:bg-slate-950/80" />
    <OceanBubbles />
  </div>
</template>

<style scoped>
.ocean-rays {
  mix-blend-mode: screen;
  /* Huzmeler yüzeyde parlak, derine indikçe kaybolur. */
  mask-image: linear-gradient(to bottom, #000 0%, #000 35%, transparent 90%);
}

.ocean-ray {
  position: absolute;
  top: -15%;
  height: 140%;
  transform-origin: top center;
  transform: rotate(var(--angle));
  background: linear-gradient(to bottom, rgba(220, 250, 255, 0.55), rgba(180, 240, 255, 0.15) 60%, transparent);
  filter: blur(14px);
  opacity: var(--peak);
  animation-name: ray-sway;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}

@keyframes ray-sway {
  0% {
    transform: rotate(calc(var(--angle) - 3deg)) scaleX(0.85);
    opacity: calc(var(--peak) * 0.45);
  }
  50% {
    opacity: var(--peak);
  }
  100% {
    transform: rotate(calc(var(--angle) + 3deg)) scaleX(1.15);
    opacity: calc(var(--peak) * 0.6);
  }
}

.ocean-vignette {
  background: radial-gradient(ellipse at 50% 0%, transparent 45%, rgba(3, 30, 60, 0.45) 100%);
}

@media (prefers-reduced-motion: reduce) {
  .ocean-ray {
    animation: none;
  }
}
</style>
