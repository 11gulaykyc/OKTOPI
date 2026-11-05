<script setup>
import { Languages } from 'lucide-vue-next'
import ComingSoonPanel from '@/components/layout/ComingSoonPanel.vue'

const plans = [
  { title: 'Terimlerin İngilizcesi', text: 'Üslü ifade → exponent, türev → derivative gibi terimlerin İngilizce karşılıkları.' },
  { title: 'Okunuş', text: 'Formüllerin ve sembollerin İngilizce nasıl okunduğu.' },
  { title: 'Konu konu kelime listeleri', text: 'Her sınıf ve konu için ayrı İngilizce matematik kelime listesi.' },
  { title: 'İngilizce soru örnekleri', text: 'İstersen matematiği İngilizce sorularla da çalışabileceksin.' },
]
</script>

<template>
  <ComingSoonPanel
    :icon="Languages"
    eyebrow="Matematiğin dili: İngilizce"
    title="MathLingo"
    description="Matematik terimlerini ve formülleri İngilizce de öğrenmek isteyenler için hazırlanan bölüm."
    :plans="plans"
  />
</template>
