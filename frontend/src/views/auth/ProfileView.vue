<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Cake, CircleCheck, GraduationCap, LoaderCircle, Mail, Save, School, Gauge } from 'lucide-vue-next'
import { birthDateLimits, formatLongDate } from '@/utils/date'
import OktopiMascot from '@/components/layout/OktopiMascot.vue'
import api, { errorMessage, fieldErrors } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const options = ref({ min_birth_year: null, school_types: [], grade_levels: [] })
const birthDateBounds = computed(() => birthDateLimits(options.value.min_birth_year))
const form = reactive({})
const errors = ref({})
const generalError = ref('')
const saved = ref(false)
const saving = ref(false)

function resetForm() {
  const u = auth.user
  Object.assign(form, {
    first_name: u.first_name,
    last_name: u.last_name,
    email: u.email,
    grade_level: u.profile.grade_level,
    school_type: u.profile.school_type,
    birth_date: u.profile.birth_date,
  })
}

onMounted(async () => {
  resetForm()
  try {
    options.value = (await api.get('/auth/profile-options/')).data
    await auth.fetchMe()
    resetForm()
  } catch (e) {
    generalError.value = errorMessage(e)
  }
})

const joined = computed(() =>
  auth.user ? new Date(auth.user.date_joined).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }) : '',
)

async function save() {
  errors.value = {}
  generalError.value = ''
  saved.value = false
  saving.value = true
  try {
    await auth.updateProfile({
      first_name: form.first_name,
      last_name: form.last_name,
      email: form.email.trim(),
      profile: { grade_level: form.grade_level, school_type: form.school_type, birth_date: form.birth_date || null },
    })
    saved.value = true
  } catch (e) {
    errors.value = fieldErrors(e)
    if (!Object.keys(errors.value).length) generalError.value = errorMessage(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-if="auth.user" class="mx-auto max-w-4xl space-y-6">
    <section class="card flex flex-col items-center gap-5 p-6 text-center sm:flex-row sm:text-left">
      <OktopiMascot mood="happy" :size="96" />
      <div class="min-w-0 flex-1">
        <h1 class="truncate text-2xl font-bold text-slate-900 dark:text-white">
          {{ [auth.user.first_name, auth.user.last_name].filter(Boolean).join(' ') || auth.user.username }}
        </h1>
        <p class="text-slate-500 dark:text-slate-400">@{{ auth.user.username }} · {{ joined }} tarihinden beri üye</p>
        <div class="mt-3 flex flex-wrap justify-center gap-2 sm:justify-start">
          <span class="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1 text-xs font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
            <GraduationCap class="h-3.5 w-3.5" /> {{ auth.user.profile.grade_level }}. Sınıf
          </span>
          <span class="inline-flex items-center gap-1.5 rounded-full bg-aqua-50 px-3 py-1 text-xs font-bold text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300">
            <School class="h-3.5 w-3.5" /> {{ auth.user.profile.school_type_display }}
          </span>
          <span
            class="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-3 py-1 text-xs font-bold text-wine-600 dark:bg-rose-500/15 dark:text-rose-300"
            :title="formatLongDate(auth.user.profile.birth_date)"
          >
            <Cake class="h-3.5 w-3.5" /> {{ auth.user.profile.age }} yaş
            <template v-if="auth.user.profile.is_birthday_today"> · Bugün doğum günün</template>
          </span>
          <span class="inline-flex items-center gap-1.5 rounded-full bg-accent-100 px-3 py-1 text-xs font-bold text-accent-600 dark:bg-accent-600/20 dark:text-accent-400">
            <Gauge class="h-3.5 w-3.5" /> Seviye: {{ auth.user.profile.initial_level_display }}
          </span>
        </div>
      </div>
    </section>

    <form class="card space-y-5 p-6" novalidate @submit.prevent="save">
      <h2 class="text-lg font-bold text-slate-900 dark:text-white">Bilgilerini güncelle</h2>
      <div class="grid gap-4 sm:grid-cols-2">
        <div>
          <label class="field-label" for="first_name">Ad</label>
          <input id="first_name" v-model="form.first_name" class="field-input" />
          <p v-if="errors.first_name" class="field-error">{{ errors.first_name }}</p>
        </div>
        <div>
          <label class="field-label" for="last_name">Soyad</label>
          <input id="last_name" v-model="form.last_name" class="field-input" />
          <p v-if="errors.last_name" class="field-error">{{ errors.last_name }}</p>
        </div>
        <div class="sm:col-span-2">
          <label class="field-label" for="email">E-posta</label>
          <div class="relative">
            <Mail class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input id="email" v-model="form.email" type="email" class="field-input !pl-9" />
          </div>
          <p v-if="errors.email" class="field-error">{{ errors.email }}</p>
        </div>
        <div>
          <label class="field-label" for="grade_level">Sınıf</label>
          <select id="grade_level" v-model.number="form.grade_level" class="field-input">
            <option v-for="g in options.grade_levels" :key="g.value" :value="g.value">{{ g.label }}</option>
          </select>
          <p v-if="errors.grade_level" class="field-error">{{ errors.grade_level }}</p>
        </div>
        <div>
          <label class="field-label" for="school_type">Okul türü</label>
          <select id="school_type" v-model="form.school_type" class="field-input">
            <option v-for="s in options.school_types" :key="s.value" :value="s.value">{{ s.label }}</option>
          </select>
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
          />
          <p v-if="errors.birth_date" class="field-error">{{ errors.birth_date }}</p>
        </div>
      </div>

      <p v-if="generalError" class="rounded-xl bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 dark:bg-rose-500/10 dark:text-rose-300" role="alert">
        {{ generalError }}
      </p>
      <p v-if="saved" class="flex items-center gap-2 text-sm font-bold text-aqua-600 dark:text-aqua-400" role="status">
        <CircleCheck class="h-4 w-4" /> Bilgilerin kaydedildi.
      </p>

      <div class="flex justify-end gap-2">
        <button type="button" class="btn-secondary" @click="resetForm">Vazgeç</button>
        <button type="submit" class="btn-primary" :disabled="saving">
          <LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" />
          <Save v-else class="h-4 w-4" />
          Kaydet
        </button>
      </div>
    </form>
  </div>
</template>
