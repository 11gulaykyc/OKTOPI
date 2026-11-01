<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { birthDateLimits } from '@/utils/date'
import { useRouter } from 'vue-router'
import { Check, LoaderCircle } from 'lucide-vue-next'
import AuthShell from '@/components/layout/AuthShell.vue'
import api, { errorMessage, fieldErrors } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useGradeStore } from '@/stores/grade'

const auth = useAuthStore()
const router = useRouter()

const options = ref({ min_birth_year: null, school_types: [], grade_levels: [] })
const form = reactive({
  first_name: '',
  last_name: '',
  username: '',
  email: '',
  password: '',
  grade_level: null,
  school_type: '',
  birth_date: '',
})
const birthDateBounds = computed(() => birthDateLimits(options.value.min_birth_year))
const errors = ref({})
const generalError = ref('')
const loading = ref(false)

// İstemci tarafı ön kontroller yalnızca kolaylık içindir; asıl kurallar sunucuda (accounts/validators.py).
const letterCount = (s) => (s.match(/\p{L}/gu) || []).length
const NAME_RE = /^\p{L}+(?:[ '\-’]\p{L}+)*$/u
function nameError(value, min, label) {
  const v = value.trim().replace(/\s+/g, ' ')
  if (!v) return `${label} gerekli.`
  if (!NAME_RE.test(v)) return `${label} yalnızca harflerden oluşmalı.`
  if (letterCount(v) < min) return `${label} en az ${min} harf olmalı.`
  return ''
}
const passwordRules = computed(() => [
  { label: 'En az 8 karakter', ok: form.password.length >= 8 },
  { label: 'En az bir büyük harf', ok: /\p{Lu}/u.test(form.password) },
])

function localErrors() {
  const e = {}
  const first = nameError(form.first_name, 3, 'Ad')
  const last = nameError(form.last_name, 2, 'Soyad')
  if (first) e.first_name = first
  if (last) e.last_name = last
  const username = form.username.trim()
  if (username.length < 2) e.username = 'Kullanıcı adı en az 2 karakter olmalı.'
  else if (/\s/.test(username)) e.username = 'Kullanıcı adında boşluk olamaz.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) e.email = 'Geçerli bir e-posta adresi yaz.'
  if (!passwordRules.value.every((r) => r.ok)) e.password = 'Şifre aşağıdaki koşulları karşılamalı.'
  if (!form.grade_level) e.grade_level = 'Sınıfını seç.'
  if (!form.school_type) e.school_type = 'Okul türünü seç.'
  if (!form.birth_date) e.birth_date = 'Doğum tarihini gir.'
  return e
}

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/profile-options/')
    options.value = data
  } catch (e) {
    generalError.value = errorMessage(e)
  }
})

async function submit() {
  generalError.value = ''
  errors.value = localErrors()
  if (Object.keys(errors.value).length) return
  loading.value = true
  try {
    await auth.register({
      ...form,
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      username: form.username.trim(),
      email: form.email.trim(),
    })
    useGradeStore().reset() // misafirken göz atılan sınıf taşınmasın
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
  <AuthShell title="Hesap oluştur" subtitle="Bilgilerin sınıfına uygun içerikleri göstermek için kullanılır." mood="celebrate">
    <form class="space-y-4" novalidate @submit.prevent="submit">
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="field-label" for="first_name">Ad</label>
          <input id="first_name" v-model="form.first_name" class="field-input" autocomplete="given-name" required />
          <p v-if="errors.first_name" class="field-error">{{ errors.first_name }}</p>
        </div>
        <div>
          <label class="field-label" for="last_name">Soyad</label>
          <input id="last_name" v-model="form.last_name" class="field-input" autocomplete="family-name" required />
          <p v-if="errors.last_name" class="field-error">{{ errors.last_name }}</p>
        </div>
      </div>
      <div>
        <label class="field-label" for="username">Kullanıcı adı</label>
        <input id="username" v-model="form.username" class="field-input" autocomplete="username" spellcheck="false" required />
        <p v-if="errors.username" class="field-error">{{ errors.username }}</p>
        <p v-else class="mt-1 text-sm text-slate-500 dark:text-slate-400">En az 2 karakter. Harf, rakam ve sembol kullanabilirsin.</p>
      </div>
      <div>
        <label class="field-label" for="email">E-posta</label>
        <input id="email" v-model="form.email" type="email" class="field-input" autocomplete="email" required />
        <p v-if="errors.email" class="field-error">{{ errors.email }}</p>
      </div>
      <div>
        <label class="field-label" for="password">Şifre</label>
        <input id="password" v-model="form.password" type="password" class="field-input" autocomplete="new-password" required />
        <p v-if="errors.password" class="field-error">{{ errors.password }}</p>
        <ul class="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-sm" aria-live="polite">
          <li
            v-for="r in passwordRules"
            :key="r.label"
            class="flex items-center gap-1"
            :class="r.ok ? 'text-aqua-700 dark:text-aqua-300' : 'text-slate-500 dark:text-slate-400'"
          >
            <Check class="h-3.5 w-3.5" :class="r.ok ? '' : 'opacity-30'" aria-hidden="true" />
            {{ r.label }}<span class="sr-only">{{ r.ok ? ' (tamam)' : ' (eksik)' }}</span>
          </li>
        </ul>
      </div>

      <fieldset>
        <legend class="field-label">Sınıf</legend>
        <div class="grid grid-cols-4 gap-2">
          <label
            v-for="g in options.grade_levels"
            :key="g.value"
            class="cursor-pointer rounded-lg border py-2.5 text-center text-sm font-semibold transition"
            :class="form.grade_level === g.value
              ? 'border-brand-600 bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300'
              : 'border-slate-300 text-slate-600 hover:border-brand-400 dark:border-slate-700 dark:text-slate-300'"
          >
            <input v-model="form.grade_level" type="radio" name="grade" :value="g.value" class="sr-only" />
            {{ g.value }}. sınıf
          </label>
        </div>
        <p v-if="errors.grade_level" class="field-error">{{ errors.grade_level }}</p>
      </fieldset>

      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="field-label" for="school_type">Okul türü</label>
          <select id="school_type" v-model="form.school_type" class="field-input" required>
            <option value="" disabled>Seç</option>
            <option v-for="s in options.school_types" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
          <p v-if="errors.school_type" class="field-error">{{ errors.school_type }}</p>
        </div>
        <div>
          <label class="field-label" for="birth_date">Doğum tarihi</label>
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
        </div>
      </div>

      <p v-if="generalError" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">
        {{ generalError }}
      </p>

      <button type="submit" class="btn-primary w-full" :disabled="loading">
        <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
        Hesabı oluştur
      </button>
    </form>
    <p class="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
      Zaten hesabın var mı?
      <RouterLink to="/giris" class="font-semibold text-brand-600 hover:underline dark:text-brand-400">Giriş yap</RouterLink>
    </p>
    <p class="mt-3 text-center text-sm">
      <RouterLink to="/konular" class="text-slate-500 hover:text-brand-600 hover:underline dark:text-slate-400 dark:hover:text-brand-400">
        Kayıt olmadan incele →
      </RouterLink>
    </p>
  </AuthShell>
</template>
