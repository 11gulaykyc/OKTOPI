<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { BookOpen, ChartColumn, ChevronRight, Lightbulb, PencilLine, Timer } from 'lucide-vue-next'
import MascotBanner from '@/components/layout/MascotBanner.vue'
import OktopiMascot from '@/components/layout/OktopiMascot.vue'
import api, { errorMessage } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { GRADES, useGradeStore } from '@/stores/grade'

const auth = useAuthStore()
const gradeStore = useGradeStore()
const router = useRouter()
const grades = ref([]) // /curriculum/grades/ özetleri (tema ve konu sayısı)
const loadError = ref('')

/*
 * Bilgilendirme kartları. Görseller hazır olduğunda `frontend/src/assets/home/` altına koyup
 * `image` alanına import edilen dosyayı vermek yeterli; görsel yokken ikon gösterilir.
 */
const features = [
  {
    title: 'Konu anlatımı',
    text: 'Her konu kısa bölümler, formüller ve adım adım çözülmüş örneklerle, akran diliyle anlatılıyor.',
    icon: BookOpen,
    image: null,
  },
  {
    title: 'Soru çözümü',
    text: 'Konu konu soru çöz. Yanlış bir şık seçtiğinde hangi kavramı karıştırdığını söylüyor ve ilgili bölüme götürüyor.',
    icon: PencilLine,
    image: null,
  },
  {
    title: 'Süreli çözüm',
    text: 'İstersen soru çözümüne süre ekle, sınav temposunda kendini dene.',
    icon: Timer,
    image: null,
  },
  {
    title: 'Gelişimini gör',
    text: 'Çalışma süren, başarı oranın, puanın ve rozetlerin panelde. Süre yalnızca gerçekten çalışırken sayılıyor.',
    icon: ChartColumn,
    image: null,
  },
]

const steps = [
  { title: 'Sınıfını seç', text: '9, 10, 11 veya 12. sınıf.' },
  { title: 'Ne yapacağını seç', text: 'Konu anlatımı ya da soru çözümü.' },
  { title: 'Konunu seç', text: 'Çalışmak istediğin konuya tıkla ve başla.' },
]

function gradeSummary(grade) {
  return grades.value.find((g) => g.grade === grade)
}

function chooseGrade(grade) {
  gradeStore.setGrade(grade)
  router.push({ name: 'grade-hub', params: { grade } })
}

onMounted(async () => {
  try {
    grades.value = (await api.get('/curriculum/grades/')).data
  } catch (e) {
    loadError.value = errorMessage(e)
  }
})
</script>

<template>
  <div class="mx-auto max-w-5xl space-y-12">
    <!-- Giriş yapmış öğrenciye kısa karşılama -->
    <template v-if="auth.isAuthenticated">
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
        message="Aşağıdan sınıfını seçerek konu anlatımına ya da soru çözümüne geçebilirsin."
      >
        <a href="#sinif-sec" class="btn bg-white text-brand-700 hover:bg-brand-50">Sınıfını Seç</a>
        <RouterLink to="/panel" class="btn bg-white/15 text-white hover:bg-white/25">Öğrenci Paneli</RouterLink>
      </MascotBanner>
    </template>

    <!-- Tanıtım -->
    <section v-else class="flex flex-col items-center gap-8 pt-4 sm:flex-row sm:items-center">
      <div class="flex-1 text-center sm:text-left">
        <h1 class="text-4xl font-bold leading-tight text-slate-900 dark:text-white sm:text-5xl">Lise matematiği, kendi hızında.</h1>
        <p class="mt-4 text-lg text-slate-600 dark:text-slate-300">
          OKTOPİ, 9–12. sınıf matematik konularını Türkiye Yüzyılı Maarif Modeli programına göre anlatan ve
          soru çözerken nerede takıldığını gösteren bir öğrenme platformu.
        </p>
        <div class="mt-6 flex flex-wrap justify-center gap-3 sm:justify-start">
          <a href="#sinif-sec" class="btn-primary text-base">Sınıfını seç</a>
          <RouterLink to="/kayit" class="btn-secondary text-base">Hesap oluştur</RouterLink>
          <RouterLink to="/giris" class="btn-ghost text-base">Giriş yap</RouterLink>
        </div>
      </div>
      <OktopiMascot mood="welcome" :size="200" class="shrink-0" />
    </section>

    <!-- Neden Oktopi? -->
    <section class="card p-6 sm:p-8">
      <h2 class="text-2xl font-bold text-slate-900 dark:text-white">Neden Oktopi?</h2>
      <p class="mt-3 text-lg font-semibold text-brand-700 dark:text-brand-300">
        Her öğrencinin öğrenme yolculuğu farklıdır. Oktopi, bu yolculuğu daha keşfedilebilir, anlaşılır ve keyifli hâle getirir.
      </p>
      <div class="mt-4 space-y-3 leading-relaxed text-slate-600 dark:text-slate-300">
        <p>
          Matematik, yalnızca formüllerden ve işlem adımlarından ibaret değildir. Kavramları anlamak, aralarındaki ilişkileri
          keşfetmek ve öğrendiklerini farklı problemlerde kullanabilmek gerekir. Oktopi, tam da bu noktadan hareketle matematik
          öğrenme deneyimini yeniden şekillendirir.
        </p>
        <p>
          Klasik öğrenme yöntemlerinin ötesine geçerek konu anlatımlarını, detaylı soru çözümlerini, interaktif matematiksel
          görselleştirmeleri ve süreli testleri tek bir platformda buluşturur. Öğrencilerin yalnızca ne öğrendiğine değil, nasıl
          öğrendiğine de odaklanır.
        </p>
        <p>
          Oyunlaştırma ve gelişim takibiyle öğrenme sürecini daha motive edici hâle getirirken her öğrencinin kendi hızında
          ilerleyebilmesine olanak tanır. Çünkü bizim için başarı, yalnızca soruları doğru cevaplamak değil; öğrenilen bilgiyi
          anlamlandırmak ve kalıcı hâle getirmektir.
        </p>
      </div>
      <p class="mt-5 rounded-2xl bg-gradient-to-r from-brand-600 to-aqua-500 px-5 py-4 text-center font-bold text-white">
        Oktopi ile öğrenmenin sınırlarını değil, keşfedilecek yeni yolları keşfet!
      </p>
    </section>

    <!-- Oktopi adı nereden geliyor? -->
    <section class="card overflow-hidden">
      <div class="bg-gradient-to-br from-brand-800 via-brand-600 to-aqua-500 px-6 py-6 text-white sm:px-8">
        <p class="text-sm font-bold uppercase tracking-wider text-white/70">Merak edenler için</p>
        <h2 class="mt-1 text-2xl font-bold">Oktopi adı nereden geliyor?</h2>
        <p class="mt-2 text-lg font-semibold">
          OKTO<span class="text-sky-200">Pİ</span> = <span class="font-bold">Okto</span>pus (ahtapot) + <span class="font-bold">π</span> (pi)
        </p>
      </div>
      <div class="space-y-3 p-6 leading-relaxed text-slate-600 dark:text-slate-300 sm:p-8">
        <p>
          Adımız iki şeyin buluşmasından doğdu: okyanusların en meraklı canlısı <strong class="text-slate-900 dark:text-white">ahtapot</strong>
          ve matematiğin en ünlü sayısı <strong class="text-slate-900 dark:text-white">π</strong>. Virgülden sonra sonsuza kadar uzanan,
          hiçbir zaman kendini tekrar etmeyen π gibi, matematik de keşfettikçe yeni bir şey gösteren bir dünya.
        </p>
        <p>
          Okyanusu düşün: Yüzeyde dalgalar vardır, ama asıl hayat derinlerde saklıdır. Matematik de böyledir. Yüzeyde formüller ve
          işlemler görürsün; derinlere indikçe kavramların birbirine nasıl bağlandığını, bir fikrin nasıl başka bir fikri doğurduğunu fark
          edersin. Her derinlikte yeni bir keşif seni bekler.
        </p>
        <p>
          Ahtapot ise bu derinliklerin en zeki kâşifidir. Meraklıdır, karşılaştığı her şeyi inceler; bir yol kapanınca başka bir yol bulur,
          bulmacaları çözer ve deneyerek öğrenir. Sekiz koluyla aynı anda birçok şeye uzanabilir. Bir problemi çözmenin de tek bir yolu
          yoktur: Kimi zaman bir grafik, kimi zaman bir formül, kimi zaman farklı bir bakış açısı seni sonuca ulaştırır.
        </p>
        <p>
          İşte Oktopi'de öğrenci, bu okyanusun ahtapotudur. Kendi hızında dalar, merak ettiği yere uzanır, hata yaptığında yön değiştirir
          ve her yeni konuda biraz daha derine iner. Biz de bu yolculukta ona eşlik eden rehberiz.
        </p>
        <p class="pt-2 text-center font-bold text-brand-700 dark:text-brand-300">
          Matematiğin derinliklerine dalmaya hazır mısın? Sekiz kolunla keşfe çık!
        </p>
      </div>
    </section>

    <!-- İçerik hakkında -->
    <section>
      <h2 class="text-xl font-bold text-slate-900 dark:text-white">OKTOPİ'de neler var?</h2>
      <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <article v-for="f in features" :key="f.title" class="card overflow-hidden">
          <img v-if="f.image" :src="f.image" :alt="f.title" class="aspect-[16/9] w-full object-cover" />
          <div v-else class="flex aspect-[16/9] items-center justify-center bg-gradient-to-br from-brand-50 to-aqua-50 dark:from-brand-500/10 dark:to-aqua-500/10">
            <component :is="f.icon" class="h-14 w-14 text-brand-500 dark:text-brand-300" aria-hidden="true" />
          </div>
          <div class="p-5">
            <h3 class="font-bold text-slate-900 dark:text-white">{{ f.title }}</h3>
            <p class="mt-1 text-sm text-slate-600 dark:text-slate-400">{{ f.text }}</p>
          </div>
        </article>
      </div>
    </section>

    <!-- Nasıl çalışır -->
    <section>
      <h2 class="text-xl font-bold text-slate-900 dark:text-white">Nasıl çalışır?</h2>
      <ol class="mt-4 grid gap-4 sm:grid-cols-3">
        <li v-for="(s, i) in steps" :key="s.title" class="flex gap-3">
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white">{{ i + 1 }}</span>
          <div>
            <p class="font-semibold text-slate-900 dark:text-white">{{ s.title }}</p>
            <p class="text-sm text-slate-600 dark:text-slate-400">{{ s.text }}</p>
          </div>
        </li>
      </ol>
    </section>

    <!-- Sınıf seçimi -->
    <section id="sinif-sec" class="scroll-mt-20 rounded-3xl bg-brand-50/70 p-6 dark:bg-brand-500/10 sm:p-8">
      <div class="flex items-center gap-2">
        <Lightbulb class="h-5 w-5 text-brand-600 dark:text-brand-300" aria-hidden="true" />
        <h2 class="text-xl font-bold text-slate-900 dark:text-white">Kaçıncı sınıftasın?</h2>
      </div>
      <p class="mt-1 text-sm text-slate-600 dark:text-slate-400">Sınıfını seç, sonra konu anlatımı ya da soru çözümüyle devam et.</p>

      <div class="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <button
          v-for="g in GRADES"
          :key="g"
          type="button"
          class="card group flex flex-col items-start p-5 text-left transition hover:-translate-y-0.5 hover:border-brand-300 hover:shadow-md dark:hover:border-brand-500/50"
          :class="{ 'ring-2 ring-brand-500': auth.isAuthenticated && g === gradeStore.ownGrade }"
          @click="chooseGrade(g)"
        >
          <span class="text-3xl font-bold text-brand-700 dark:text-brand-300">{{ g }}.</span>
          <span class="font-semibold text-slate-900 dark:text-white">Sınıf</span>
          <span v-if="gradeSummary(g)" class="mt-2 text-xs text-slate-500 dark:text-slate-400">
            {{ gradeSummary(g).theme_count }} tema · {{ gradeSummary(g).topic_count }} konu
          </span>
          <span v-if="auth.isAuthenticated && g === gradeStore.ownGrade" class="mt-2 rounded-full bg-brand-600 px-2 py-0.5 text-[11px] font-bold text-white">
            Senin sınıfın
          </span>
          <ChevronRight class="mt-3 h-4 w-4 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-brand-600" aria-hidden="true" />
        </button>
      </div>
      <p v-if="loadError" class="mt-3 text-sm font-semibold text-rose-600">{{ loadError }}</p>
    </section>
  </div>
</template>
