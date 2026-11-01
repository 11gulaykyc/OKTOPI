<script setup>
import { onMounted, ref, watch } from 'vue'
import MascotBanner from '@/components/layout/MascotBanner.vue'
import OktopiMascot from '@/components/layout/OktopiMascot.vue'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useGradeStore } from '@/stores/grade'

const auth = useAuthStore()
const gradeStore = useGradeStore()
const grades = ref([])
const curriculum = ref(null)
const loadError = ref('')

const features = [
  { title: 'Konu anlatımı', text: 'Her konu kısa bölümler, formüller ve adım adım çözülmüş örneklerle anlatılıyor.' },
  { title: 'Hatanın nedeni', text: 'Yanlış bir şık seçtiğinde hangi kavramı karıştırdığını söylüyor ve ilgili bölüme götürüyor.' },
  { title: 'Çalışma süresi', text: 'Sadece sayfada gerçekten çalışırken sayılıyor; sekmeyi açık unutursan süre artmıyor.' },
  { title: 'Puan ve hedefler', text: 'Konu bitirdikçe ve soru çözdükçe puan topluyor, kendine günlük hedef koyabiliyorsun.' },
]

async function loadGrades() {
  try {
    grades.value = (await api.get('/curriculum/grades/')).data
  } catch (e) {
    loadError.value = errorMessage(e)
  }
}

async function loadCurriculum(grade) {
  if (!grade) return
  try {
    curriculum.value = (await api.get(`/curriculum/grades/${grade}/`)).data
  } catch (e) {
    loadError.value = errorMessage(e)
  }
}

onMounted(loadGrades)
// Giriş yapmış öğrenci üst bardaki sınıf seçicide hangi sınıfı seçtiyse onun konu ağacı gösterilir.
watch(() => (auth.isAuthenticated ? gradeStore.grade : null), loadCurriculum, { immediate: true })
</script>

<template>
  <!-- Giriş yapmış öğrenci -->
  <div v-if="auth.isAuthenticated" class="space-y-6">
    <MascotBanner
      v-if="auth.user.profile?.is_birthday_today"
      mood="celebrate"
      :title="`İyi ki doğdun, ${auth.displayName}`"
      :message="`Bugün ${auth.user.profile.age} yaşına girdin. Yeni yaşın sana iyi gelsin.`"
    >
      <RouterLink to="/profil" class="btn bg-white/15 text-white hover:bg-white/25">Profilimi Gör</RouterLink>
    </MascotBanner>
    <MascotBanner
      v-else
      mood="welcome"
      :title="`Merhaba ${auth.displayName}`"
      :message="`${auth.grade}. sınıf konuları aşağıda. Panelden ilerlemeni takip edebilirsin.`"
    >
      <RouterLink to="/panel" class="btn bg-white text-brand-700 hover:bg-brand-50">Öğrenci Paneli</RouterLink>
      <RouterLink to="/konular" class="btn bg-white/15 text-white hover:bg-white/25">Konulara Göz At</RouterLink>
    </MascotBanner>

    <section v-if="curriculum">
      <div class="mb-3 flex items-end justify-between gap-2">
        <div>
          <h2 class="text-xl font-bold text-slate-900 dark:text-white">{{ curriculum.title }}</h2>
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ curriculum.program }}</p>
        </div>
      </div>
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article v-for="theme in curriculum.themes" :key="theme.id" class="card p-5">
          <div class="flex items-center gap-3">
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white">
              {{ theme.order }}
            </span>
            <h3 class="font-bold text-slate-900 dark:text-white">{{ theme.title }}</h3>
          </div>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{{ theme.description }}</p>
          <ul class="mt-3 space-y-1.5">
            <li v-for="topic in theme.topics" :key="topic.id" class="flex items-center justify-between gap-2 text-sm">
              <RouterLink
                :to="{ name: 'topic-detail', params: { topicId: topic.id } }"
                class="truncate font-semibold text-slate-700 hover:text-brand-600 dark:text-slate-200 dark:hover:text-brand-300"
              >
                {{ topic.title }}
              </RouterLink>
              <span v-if="topic.has_content" class="shrink-0 rounded-full bg-aqua-50 px-2 py-0.5 text-[11px] font-bold text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300">
                Anlatım hazır
              </span>
              <span v-else-if="topic.question_count" class="shrink-0 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-bold text-brand-700 dark:bg-brand-500/15 dark:text-brand-300">
                {{ topic.question_count }} soru
              </span>
            </li>
          </ul>
        </article>
      </div>
    </section>
    <p v-if="loadError" class="text-sm font-semibold text-rose-600">{{ loadError }}</p>
  </div>

  <!-- Ziyaretçi -->
  <div v-else class="mx-auto max-w-4xl space-y-10">
    <section class="flex flex-col items-center gap-8 pt-4 sm:flex-row sm:items-center">
      <div class="flex-1 text-center sm:text-left">
        <h1 class="text-4xl font-bold leading-tight text-slate-900 dark:text-white sm:text-5xl">Lise matematiği, kendi hızında.</h1>
        <p class="mt-4 text-lg text-slate-600 dark:text-slate-300">
          9, 10, 11 ve 12. sınıf konuları Maarif Modeli programına göre sıralı. Konuyu oku, soruları çöz,
          nerede takıldığını gör.
        </p>
        <div class="mt-6 flex flex-wrap justify-center gap-3 sm:justify-start">
          <RouterLink to="/kayit" class="btn-primary text-base">Hesap oluştur</RouterLink>
          <RouterLink to="/giris" class="btn-secondary text-base">Giriş yap</RouterLink>
          <RouterLink to="/konular" class="btn-ghost text-base">Kayıt olmadan incele →</RouterLink>
        </div>
      </div>
      <OktopiMascot mood="welcome" :size="200" class="shrink-0" />
    </section>

    <section class="border-t border-slate-200 pt-8 dark:border-slate-800">
      <h2 class="text-xl font-bold text-slate-900 dark:text-white">Neler var?</h2>
      <dl class="mt-4 grid gap-x-10 gap-y-5 sm:grid-cols-2">
        <div v-for="f in features" :key="f.title">
          <dt class="font-semibold text-slate-900 dark:text-white">{{ f.title }}</dt>
          <dd class="mt-1 text-slate-600 dark:text-slate-400">{{ f.text }}</dd>
        </div>
      </dl>
    </section>

    <section v-if="grades.length" class="border-t border-slate-200 pt-8 dark:border-slate-800">
      <h2 class="text-xl font-bold text-slate-900 dark:text-white">Sınıflar</h2>
      <ul class="mt-4 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
        <li v-for="g in grades" :key="g.grade" class="flex items-center justify-between gap-3 px-4 py-3">
          <span class="font-semibold text-slate-900 dark:text-white">{{ g.title }}</span>
          <span class="text-sm text-slate-500 dark:text-slate-400">{{ g.theme_count }} tema, {{ g.topic_count }} konu</span>
        </li>
      </ul>
    </section>
    <p v-if="loadError" class="text-sm font-semibold text-rose-600">{{ loadError }}</p>
  </div>
</template>
