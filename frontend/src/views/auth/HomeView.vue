<script setup>
import { onMounted, ref, watch } from 'vue'
import { BookOpenCheck, Brain, ChartLine, Clock, Layers, Trophy } from 'lucide-vue-next'
import MascotBanner from '@/components/layout/MascotBanner.vue'
import OktopiMascot from '@/components/layout/OktopiMascot.vue'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const grades = ref([])
const curriculum = ref(null)
const loadError = ref('')

const features = [
  { icon: BookOpenCheck, title: 'Akran dilinde konu anlatımı', text: 'Maarif Modeli uyumlu, adım adım çözümlü örneklerle.' },
  { icon: Brain, title: 'Kavram yanılgısı analizi', text: 'Yanlış şıkkın arkasındaki düşünce hatasını bulur, doğru konuya yönlendirir.' },
  { icon: Clock, title: 'Gerçek çalışma süresi', text: 'Sadece aktifken sayılan süre; sekme açık unutulunca şişmez.' },
  { icon: Trophy, title: 'Rozetler ve hedefler', text: 'Gerçek eylemlerle kazanılan puan, rozet ve görevler.' },
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
watch(() => auth.grade, loadCurriculum, { immediate: true })
</script>

<template>
  <!-- Giriş yapmış öğrenci -->
  <div v-if="auth.isAuthenticated" class="space-y-6">
    <MascotBanner
      v-if="auth.user.profile?.is_birthday_today"
      mood="celebrate"
      :title="`İyi ki doğdun ${auth.displayName}! 🎂`"
      :message="`Bugün ${auth.user.profile.age} yaşına girdin! Yeni yaşında merakın hiç bitmesin, her soruda biraz daha güçlen. Oktopi olarak seninle gurur duyuyoruz! 🎉`"
    >
      <RouterLink to="/profil" class="btn bg-white/15 text-white hover:bg-white/25">Profilimi Gör</RouterLink>
    </MascotBanner>
    <MascotBanner
      v-else
      mood="welcome"
      :title="`Merhaba ${auth.displayName}! 👋`"
      :message="`${auth.grade}. sınıf matematik yolculuğuna hoş geldin. Bugün neyi keşfetmek istersin?`"
    >
      <RouterLink to="/profil" class="btn bg-white/15 text-white hover:bg-white/25">Profilimi Gör</RouterLink>
    </MascotBanner>

    <section v-if="curriculum">
      <div class="mb-3 flex items-end justify-between gap-2">
        <div>
          <h2 class="text-xl font-extrabold text-slate-900 dark:text-white">{{ curriculum.title }}</h2>
          <p class="text-sm text-slate-500 dark:text-slate-400">{{ curriculum.program }}</p>
        </div>
      </div>
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <article v-for="theme in curriculum.themes" :key="theme.id" class="card p-5">
          <div class="flex items-center gap-3">
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-sm font-extrabold text-white">
              {{ theme.order }}
            </span>
            <h3 class="font-extrabold text-slate-900 dark:text-white">{{ theme.title }}</h3>
          </div>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{{ theme.description }}</p>
          <ul class="mt-3 space-y-1.5">
            <li v-for="topic in theme.topics" :key="topic.id" class="flex items-center justify-between gap-2 text-sm">
              <span class="truncate font-semibold text-slate-700 dark:text-slate-200">{{ topic.title }}</span>
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
  <div v-else class="space-y-14">
    <section class="grid items-center gap-8 lg:grid-cols-2">
      <div class="text-center lg:text-left">
        <span class="inline-flex items-center gap-2 rounded-full bg-aqua-50 px-3 py-1 text-xs font-bold text-aqua-700 dark:bg-aqua-500/15 dark:text-aqua-300">
          <Layers class="h-3.5 w-3.5" /> Türkiye Yüzyılı Maarif Modeli uyumlu
        </span>
        <h1 class="mt-4 text-4xl font-extrabold leading-tight text-slate-900 dark:text-white sm:text-5xl">
          Matematiği <span class="text-brand-600 dark:text-brand-400">anlayarak</span> öğren,
          <span class="text-aqua-500">hatalarından</span> güçlen.
        </h1>
        <p class="mt-4 text-lg text-slate-600 dark:text-slate-300">
          OKTOPİ; 9, 10, 11 ve 12. sınıf öğrencileri için konu anlatımı, soru çözümü, süreli test ve kişisel
          gelişim haritasını tek yerde toplar.
        </p>
        <div class="mt-6 flex flex-wrap justify-center gap-3 lg:justify-start">
          <RouterLink to="/kayit" class="btn-primary !px-6 !py-3 text-base">Ücretsiz Başla</RouterLink>
          <RouterLink to="/giris" class="btn-secondary !px-6 !py-3 text-base">Giriş Yap</RouterLink>
        </div>
      </div>
      <div class="relative flex justify-center">
        <div class="absolute inset-0 m-auto h-64 w-64 rounded-full bg-gradient-to-br from-brand-400/40 to-aqua-400/40 blur-3xl" />
        <OktopiMascot mood="welcome" :size="280" class="relative drop-shadow-2xl" />
      </div>
    </section>

    <section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <article v-for="f in features" :key="f.title" class="card p-5">
        <component :is="f.icon" class="h-8 w-8 text-brand-600 dark:text-brand-400" />
        <h3 class="mt-3 font-extrabold text-slate-900 dark:text-white">{{ f.title }}</h3>
        <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ f.text }}</p>
      </article>
    </section>

    <section v-if="grades.length">
      <h2 class="mb-4 flex items-center gap-2 text-xl font-extrabold text-slate-900 dark:text-white">
        <ChartLine class="h-5 w-5 text-aqua-500" /> Sınıf düzeyleri
      </h2>
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <article
          v-for="g in grades"
          :key="g.grade"
          class="card relative overflow-hidden p-5"
        >
          <span class="absolute -right-3 -top-6 text-8xl font-extrabold text-brand-500/10">{{ g.grade }}</span>
          <h3 class="text-lg font-extrabold text-slate-900 dark:text-white">{{ g.title }}</h3>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ g.theme_count }} tema · {{ g.topic_count }} konu</p>
        </article>
      </div>
    </section>
    <p v-if="loadError" class="text-sm font-semibold text-rose-600">{{ loadError }}</p>
  </div>
</template>
