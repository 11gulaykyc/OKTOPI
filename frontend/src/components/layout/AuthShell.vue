<script setup>
import { onBeforeUnmount, ref } from 'vue'
import OktopiMascot from './OktopiMascot.vue'
import ThemeToggle from './ThemeToggle.vue'
import oceanVideo from '@/assets/video/auth-ocean.mp4'
import oceanPoster from '@/assets/video/auth-ocean-poster.jpg'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  // Eski arayüz uyumluluğu için tutuluyor; arka plandaki videoda ahtapot zaten göründüğünden kullanılmıyor.
  mood: { type: String, default: 'welcome' },
  bubble: { type: String, default: '' },
})

// Hareket azaltma tercihi olan kullanıcılara video yerine sabit kare gösterilir.
const motionQuery = typeof window !== 'undefined' ? window.matchMedia('(prefers-reduced-motion: reduce)') : null
const reducedMotion = ref(motionQuery?.matches ?? false)
const onMotionChange = (e) => (reducedMotion.value = e.matches)
motionQuery?.addEventListener('change', onMotionChange)
onBeforeUnmount(() => motionQuery?.removeEventListener('change', onMotionChange))
</script>

<template>
  <div class="relative min-h-dvh overflow-hidden bg-[#1a2826]">
    <!-- Tam ekran okyanus videosu. Dikey ekranlarda ahtapot kesilmesin diye tamamı sığdırılır. -->
    <!-- Dikeyde kalan boşluklar videonun üst/alt kenar renkleriyle doldurulur. -->
    <div class="fixed inset-0 bg-gradient-to-b from-[#0d5153] via-[#1a2826] to-[#151316]" aria-hidden="true">
      <img v-if="reducedMotion" :src="oceanPoster" alt="" class="h-full w-full object-cover portrait:object-contain" />
      <video
        v-else
        class="h-full w-full object-cover portrait:object-contain"
        :src="oceanVideo"
        :poster="oceanPoster"
        autoplay
        muted
        loop
        playsinline
        disablepictureinpicture
        preload="auto"
      />
      <div class="absolute inset-0 bg-[#031326]/15" />
    </div>

    <!-- Üst bar -->
    <header class="relative z-10 flex items-center justify-between px-4 py-4 sm:px-8">
      <RouterLink to="/" class="flex items-center gap-2">
        <OktopiMascot character="navigator" mood="happy" :size="36" />
        <span class="text-xl font-bold text-white drop-shadow">OKTO<span class="text-sky-400">Pİ</span></span>
      </RouterLink>
      <span class="dark rounded-xl bg-white/10 text-white backdrop-blur-md">
        <ThemeToggle />
      </span>
    </header>

    <!-- Bulanık cam form kartı (video üzerinde). İçerik her temada açık renkli yazıyla okunsun diye `dark` sınıfı verilir. -->
    <main class="relative z-10 flex min-h-[calc(100dvh-4.25rem)] items-center justify-center px-4 pb-10">
      <div class="glass-card dark w-full max-w-md rounded-3xl border border-white/15 bg-white/5 p-6 shadow-2xl backdrop-blur-md sm:p-8">
        <p v-if="bubble" class="mb-3 text-sm text-aqua-100">{{ bubble }}</p>
        <h1 class="text-2xl font-bold text-white sm:text-3xl">{{ title }}</h1>
        <p v-if="subtitle" class="mt-1.5 text-slate-200">{{ subtitle }}</p>
        <div class="mt-6">
          <slot />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Form alanları da cam görünümüne uysun */
.glass-card :deep(.field-input) {
  background-color: rgb(255 255 255 / 0.06);
  border-color: rgb(255 255 255 / 0.25);
  color: #fff;
}
.glass-card :deep(.field-input::placeholder) {
  color: rgb(255 255 255 / 0.55);
}
.glass-card :deep(.field-input:focus) {
  background-color: rgb(255 255 255 / 0.12);
  border-color: rgb(125 211 252 / 0.8);
}
.glass-card :deep(.field-input option) {
  color: #0f172a;
}
.glass-card :deep(.field-label) {
  color: rgb(255 255 255 / 0.9);
}
</style>
