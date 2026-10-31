<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppNavbar from '@/components/layout/AppNavbar.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

useThemeStore()
const auth = useAuthStore()
const route = useRoute()
const sidebarOpen = ref(false)

watch(() => route.fullPath, () => (sidebarOpen.value = false))
</script>

<template>
  <RouterView v-if="route.meta.bare" />
  <div v-else class="min-h-dvh">
    <AppNavbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
    <div class="mx-auto flex max-w-7xl">
      <AppSidebar v-if="auth.isAuthenticated" :open="sidebarOpen" @close="sidebarOpen = false" />
      <main class="min-w-0 flex-1 px-4 py-6 sm:py-8 lg:px-8">
        <RouterView />
      </main>
    </div>
  </div>
</template>
