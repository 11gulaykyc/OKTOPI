<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppNavbar from './AppNavbar.vue'
import AppSidebar from './AppSidebar.vue'

const auth = useAuthStore()
const route = useRoute()
const sidebarOpen = ref(false)
// Ziyaretçi ana sayfada zaten kayıt/giriş seçeneklerini görür; diğer sayfalarda ince bir şerit gösterilir.
const showGuestBar = computed(() => !auth.isAuthenticated && route.name !== 'home')

watch(() => route.fullPath, () => (sidebarOpen.value = false))

// Mobil menü açıkken arka plan kaymasın; Escape ile kapanır.
watch(sidebarOpen, (open) => document.documentElement.classList.toggle('overflow-hidden', open))
function onKeydown(event) {
  if (event.key === 'Escape') sidebarOpen.value = false
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  document.documentElement.classList.remove('overflow-hidden')
})
</script>

<template>
  <div class="min-h-dvh">
    <a
      href="#ana-icerik"
      class="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-xl focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-white"
    >
      İçeriğe atla
    </a>
    <AppNavbar @toggle-sidebar="sidebarOpen = !sidebarOpen" />
    <div class="mx-auto flex max-w-7xl">
      <AppSidebar :open="sidebarOpen" @close="sidebarOpen = false" />
      <main id="ana-icerik" class="min-w-0 flex-1 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
        <div
          v-if="showGuestBar"
          class="mb-6 flex flex-col gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm dark:border-slate-800 dark:bg-slate-900 sm:flex-row sm:items-center sm:justify-between"
        >
          <p class="text-slate-600 dark:text-slate-300">
            Kayıt olmadan inceliyorsun. Soruları çözmek ve ilerlemeni kaydetmek için hesap açman gerekiyor.
          </p>
          <div class="flex shrink-0 gap-2">
            <RouterLink :to="{ name: 'login', query: { next: route.fullPath } }" class="btn-ghost !py-1.5">Giriş yap</RouterLink>
            <RouterLink to="/kayit" class="btn-primary !py-1.5">Kayıt ol</RouterLink>
          </div>
        </div>
        <RouterView />
      </main>
    </div>
  </div>
</template>
