<script setup>
import { LogOut, Menu, UserRound } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import StudyTimer from '@/components/dashboard/StudyTimer.vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useRewardStore } from '@/stores/rewards'
import { useStatsStore } from '@/stores/stats'
import GradeMenu from './GradeMenu.vue'
import { exploreLinks } from './navLinks'
import OktopiMascot from './OktopiMascot.vue'
import ThemeToggle from './ThemeToggle.vue'

defineEmits(['toggle-sidebar'])

const auth = useAuthStore()
const stats = useStatsStore()
const router = useRouter()

async function logout() {
  // Açık çalışma oturumunu kapat; hata olsa da çıkış engellenmez (sunucu zaman aşımıyla zaten dondurur).
  try {
    await api.post('/study-sessions/end/')
  } catch {}
  auth.logout()
  stats.reset()
  useRewardStore().clear()
  router.push({ name: 'home' })
}
</script>

<template>
  <header
    class="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur dark:border-slate-800 dark:bg-slate-900/85"
  >
    <div class="mx-auto flex h-16 max-w-7xl items-center gap-2 px-4">
      <button
        type="button"
        class="btn-ghost !p-2.5 lg:hidden"
        aria-label="Menüyü aç"
        @click="$emit('toggle-sidebar')"
      >
        <Menu class="h-5 w-5" />
      </button>

      <RouterLink to="/" class="flex shrink-0 items-center gap-2" aria-label="OKTOPİ ana sayfa">
        <OktopiMascot character="navigator" mood="happy" :size="36" />
        <span class="hidden text-xl font-bold tracking-tight text-brand-800 dark:text-brand-300 min-[400px]:inline">
          OKTO<span class="text-sky-500">Pİ</span>
        </span>
      </RouterLink>

      <!-- Ana gezinme: dar ekranlarda aynı bağlantılar yan menüde yer alır. -->
      <nav class="ml-4 hidden items-center gap-1 lg:flex" aria-label="Ana gezinme">
        <GradeMenu />
        <RouterLink
          v-for="link in exploreLinks"
          :key="link.to"
          :to="link.to"
          :title="link.hint || link.label"
          class="flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-slate-800"
          active-class="!bg-brand-50 !text-brand-700 dark:!bg-slate-800 dark:!text-brand-300"
        >
          <component :is="link.icon" class="h-4 w-4" aria-hidden="true" />
          <span class="xl:hidden">{{ link.short }}</span>
          <span class="hidden xl:inline">{{ link.label }}</span>
        </RouterLink>
      </nav>

      <div class="ml-auto flex items-center gap-1 sm:gap-2">
        <StudyTimer v-if="auth.isAuthenticated" />
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
          <RouterLink to="/kayit" class="btn-primary hidden sm:inline-flex">Kayıt ol</RouterLink>
        </template>
      </div>
    </div>
  </header>
</template>
