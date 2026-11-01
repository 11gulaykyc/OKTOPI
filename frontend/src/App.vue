<script setup>
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import { useThemeStore } from '@/stores/theme'

useThemeStore()
const route = useRoute()
</script>

<template>
  <RouterView v-if="route.meta.bare" />
  <AppLayout v-else />
</template>
