<script setup>
import { Clapperboard } from 'lucide-vue-next'
import ComingSoonPanel from '@/components/layout/ComingSoonPanel.vue'

const plans = [
  { title: 'Matematikçiler', text: 'Ünlü matematikçilerin hayatlarından kısa ve ilginç kesitler.' },
  { title: 'Fıkralar ve hikâyeler', text: 'Matematikle ilgili eğlenceli fıkralar ve bilinmeyen hikâyeler.' },
  { title: 'Kısa sözler', text: 'Matematik ve bilim üzerine akılda kalan sözler.' },
  { title: 'Bilim kesitleri', text: 'Matematiğin günlük hayatta ve bilimde nerelerde karşımıza çıktığını anlatan kısa videolar.' },
]
</script>

<template>
  <ComingSoonPanel
    :icon="Clapperboard"
    eyebrow="Keşfet"
    title="Akış"
    description="Kaydırarak izleyebileceğin kısa videolar: matematikçiler, fıkralar, hikâyeler ve bilim üzerine."
    :plans="plans"
  />
</template>
