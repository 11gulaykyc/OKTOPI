<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LoaderCircle, LogIn } from 'lucide-vue-next'
import AuthShell from '@/components/layout/AuthShell.vue'
import { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({ username: '', password: '' })
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.username.trim(), form.password)
    const next = typeof route.query.next === 'string' && route.query.next.startsWith('/') ? route.query.next : '/'
    router.replace(next)
  } catch (e) {
    error.value = e.response?.status === 401 ? 'Kullanıcı adı/e-posta veya şifre hatalı.' : errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell title="Tekrar hoş geldin!" subtitle="Kaldığın yerden devam etmek için giriş yap." mood="welcome" bubble="Seni yeniden görmek harika! 🐙">
    <form class="space-y-4" novalidate @submit.prevent="submit">
      <div>
        <label class="field-label" for="username">Kullanıcı adı veya e-posta</label>
        <input id="username" v-model="form.username" class="field-input" autocomplete="username" required />
      </div>
      <div>
        <label class="field-label" for="password">Şifre</label>
        <input id="password" v-model="form.password" type="password" class="field-input" autocomplete="current-password" required />
      </div>

      <p v-if="error" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">
        {{ error }}
      </p>

      <button type="submit" class="btn-primary w-full" :disabled="loading || !form.username || !form.password">
        <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
        <LogIn v-else class="h-4 w-4" />
        Giriş Yap
      </button>
    </form>
    <p class="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
      Hesabın yok mu?
      <RouterLink to="/kayit" class="font-bold text-brand-600 hover:underline dark:text-brand-400">Hemen kayıt ol</RouterLink>
    </p>
  </AuthShell>
</template>
