<script setup>
import { LogOut, Menu, UserRound } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import OktopiMascot from './OktopiMascot.vue'
import ThemeToggle from './ThemeToggle.vue'

defineEmits(['toggle-sidebar'])

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <header
    class="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur dark:border-slate-800 dark:bg-slate-900/85"
  >
    <div class="mx-auto flex h-16 max-w-7xl items-center gap-2 px-4">
      <button
        v-if="auth.isAuthenticated"
        type="button"
        class="btn-ghost !p-2.5 lg:hidden"
        aria-label="Menüyü aç"
        @click="$emit('toggle-sidebar')"
      >
        <Menu class="h-5 w-5" />
      </button>

      <RouterLink to="/" class="flex items-center gap-2" aria-label="OKTOPİ ana sayfa">
        <OktopiMascot mood="happy" :size="36" />
        <span class="text-xl font-extrabold tracking-tight text-brand-800 dark:text-brand-300">
          OKTOP<span class="text-aqua-500">İ</span>
        </span>
      </RouterLink>

      <div class="ml-auto flex items-center gap-1 sm:gap-2">
        <ThemeToggle />
        <template v-if="auth.isAuthenticated">
          <RouterLink to="/profil" class="btn-ghost !px-3" title="Profil">
            <UserRound class="h-5 w-5" />
            <span class="hidden max-w-32 truncate sm:inline">{{ auth.displayName }}</span>
          </RouterLink>
          <button type="button" class="btn-ghost !p-2.5" title="Çıkış yap" aria-label="Çıkış yap" @click="logout">
            <LogOut class="h-5 w-5" />
          </button>
        </template>
        <template v-else>
          <RouterLink to="/giris" class="btn-ghost">Giriş Yap</RouterLink>
          <RouterLink to="/kayit" class="btn-primary hidden sm:inline-flex">Ücretsiz Kayıt Ol</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
