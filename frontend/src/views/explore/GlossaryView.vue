<script setup>
import { BookA } from 'lucide-vue-next'
import ComingSoonPanel from '@/components/layout/ComingSoonPanel.vue'

const plans = [
  { title: 'Terimler', text: 'Fonksiyon, küme, türev gibi matematik terimlerinin kısa ve anlaşılır tanımları.' },
  { title: 'Formüller', text: 'Sınıf ve konuya göre gruplanmış formüller, ne işe yaradıklarıyla birlikte.' },
  { title: 'Semboller', text: 'Matematikte kullanılan sembollerin anlamı ve nasıl okunduğu.' },
  { title: 'Konuya bağlantı', text: 'Her terimden, onun anlatıldığı konu sayfasına tek tıkla geçiş.' },
]
</script>

<template>
  <ComingSoonPanel
    :icon="BookA"
    eyebrow="Keşfet"
    title="Matematik Sözlüğü"
    description="Takıldığın bir terimi ya da unuttuğun bir formülü hızlıca bulabileceğin sözlük hazırlanıyor."
    :plans="plans"
    mascot="nori"
  />
</template>
