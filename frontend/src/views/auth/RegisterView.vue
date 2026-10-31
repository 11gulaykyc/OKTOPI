<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { birthDateLimits } from '@/utils/date'
import { useRouter } from 'vue-router'
import { LoaderCircle, UserPlus } from 'lucide-vue-next'
import AuthShell from '@/components/layout/AuthShell.vue'
import api, { errorMessage, fieldErrors } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const options = ref({ birth_date_age_range: null, school_types: [], grade_levels: [] })
const form = reactive({
  first_name: '',
  username: '',
  email: '',
  password: '',
  grade_level: null,
  school_type: '',
  birth_date: '',
})
const birthDateBounds = computed(() => birthDateLimits(options.value.birth_date_age_range))
const errors = ref({})
const generalError = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/profile-options/')
    options.value = data
  } catch (e) {
    generalError.value = errorMessage(e)
  }
})

async function submit() {
  errors.value = {}
  generalError.value = ''
  loading.value = true
  try {
    await auth.register({
      ...form,
      username: form.username.trim(),
      email: form.email.trim(),
      birth_date: form.birth_date || null,
    })
    router.replace('/')
  } catch (e) {
    errors.value = fieldErrors(e)
    if (!Object.keys(errors.value).length) generalError.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell title="Aramıza katıl!" subtitle="Birkaç bilgiyle hesabını oluştur, sana uygun içerikleri hazırlayalım." mood="celebrate" bubble="Matematik yolculuğuna birlikte çıkalım! ✨">
    <form class="space-y-4" novalidate @submit.prevent="submit">
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="field-label" for="first_name">Adın</label>
          <input id="first_name" v-model="form.first_name" class="field-input" autocomplete="given-name" />
          <p v-if="errors.first_name" class="field-error">{{ errors.first_name }}</p>
        </div>
        <div>
          <label class="field-label" for="username">Kullanıcı adı *</label>
          <input id="username" v-model="form.username" class="field-input" autocomplete="username" required />
          <p v-if="errors.username" class="field-error">{{ errors.username }}</p>
        </div>
      </div>
      <div>
        <label class="field-label" for="email">E-posta *</label>
        <input id="email" v-model="form.email" type="email" class="field-input" autocomplete="email" required />
        <p v-if="errors.email" class="field-error">{{ errors.email }}</p>
      </div>
      <div>
        <label class="field-label" for="password">Şifre *</label>
        <input id="password" v-model="form.password" type="password" class="field-input" autocomplete="new-password" required />
        <p v-if="errors.password" class="field-error">{{ errors.password }}</p>
        <p v-else class="mt-1 text-xs text-slate-400">En az 8 karakter; tamamı rakam olmasın.</p>
      </div>

      <fieldset>
        <legend class="field-label">Sınıfın *</legend>
        <div class="grid grid-cols-4 gap-2">
          <label
            v-for="g in options.grade_levels"
            :key="g.value"
            class="cursor-pointer rounded-xl border-2 py-2.5 text-center text-sm font-bold transition"
            :class="form.grade_level === g.value
              ? 'border-brand-600 bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300'
              : 'border-slate-200 text-slate-600 hover:border-brand-300 dark:border-slate-700 dark:text-slate-300'"
          >
            <input v-model="form.grade_level" type="radio" name="grade" :value="g.value" class="sr-only" />
            {{ g.value }}.
          </label>
        </div>
        <p v-if="errors.grade_level" class="field-error">{{ errors.grade_level }}</p>
      </fieldset>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="field-label" for="school_type">Okul türü *</label>
          <select id="school_type" v-model="form.school_type" class="field-input" required>
            <option value="" disabled>Seç</option>
            <option v-for="s in options.school_types" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
          <p v-if="errors.school_type" class="field-error">{{ errors.school_type }}</p>
        </div>
        <div>
          <label class="field-label" for="birth_date">Doğum tarihi *</label>
          <input
            id="birth_date"
            v-model="form.birth_date"
            type="date"
            class="field-input"
            :min="birthDateBounds.min"
            :max="birthDateBounds.max"
            autocomplete="bday"
            required
          />
          <p v-if="errors.birth_date" class="field-error">{{ errors.birth_date }}</p>
          <p v-else class="mt-1 text-xs text-slate-400">Doğum gününde sana bir sürprizimiz var 🎂</p>
        </div>
      </div>

      <p v-if="generalError" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">
        {{ generalError }}
      </p>

      <button type="submit" class="btn-primary w-full" :disabled="loading">
        <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
        <UserPlus v-else class="h-4 w-4" />
        Hesabımı Oluştur
      </button>
    </form>
    <p class="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
      Zaten hesabın var mı?
      <RouterLink to="/giris" class="font-bold text-brand-600 hover:underline dark:text-brand-400">Giriş yap</RouterLink>
    </p>
  </AuthShell>
</template>
