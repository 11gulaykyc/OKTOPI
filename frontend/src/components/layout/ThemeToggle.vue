<script setup>
import { Moon, Sun } from 'lucide-vue-next'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
</script>

<template>
  <button
    type="button"
    class="btn-ghost !p-2.5"
    :aria-label="themeStore.theme === 'dark' ? 'Açık temaya geç' : 'Koyu temaya geç'"
    :title="themeStore.theme === 'dark' ? 'Açık tema' : 'Koyu tema'"
    @click="themeStore.toggle()"
  >
    <Sun v-if="themeStore.theme === 'dark'" class="h-5 w-5" />
    <Moon v-else class="h-5 w-5" />
  </button>
</template>
