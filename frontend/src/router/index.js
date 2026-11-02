import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/*
 * meta:
 *   requiresAuth     → giriş yapmamış kullanıcı giriş sayfasına yönlendirilir (dönüş adresi `next`)
 *                      (konular ve OYSS herkese açıktır: ziyaretçiler kayıt olmadan inceleyebilir)
 *   guestOnly        → giriş yapmış kullanıcı ana sayfaya yönlendirilir
 *   bare             → uygulama iskeleti (navbar/sidebar) olmadan çizilir
 *   keepStudyActive  → fare/klavye hareketi olmasa da çalışma süresi sayılır (ör. süreli test)
 *   title            → sekme başlığı
 */
const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/auth/HomeView.vue'),
  },
  {
    path: '/giris',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { guestOnly: true, bare: true, title: 'Giriş Yap' },
  },
  {
    path: '/kayit',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { guestOnly: true, bare: true, title: 'Kayıt Ol' },
  },
  {
    path: '/profil',
    name: 'profile',
    component: () => import('@/views/auth/ProfileView.vue'),
    meta: { requiresAuth: true, title: 'Profilim' },
  },
  {
    path: '/panel',
    name: 'dashboard',
    component: () => import('@/views/dashboard/StudentDashboardView.vue'),
    meta: { requiresAuth: true, title: 'Öğrenci Paneli' },
  },
  {
    path: '/konular',
    name: 'topics',
    component: () => import('@/views/learning/TopicListView.vue'),
    meta: { title: 'Konular' },
  },
  {
    path: '/konular/:topicId',
    name: 'topic-detail',
    component: () => import('@/views/learning/TopicDetailView.vue'),
    meta: { title: 'Konu Anlatımı' },
  },
  {
    path: '/oyss',
    name: 'oyss',
    component: () => import('@/views/learning/OyssView.vue'),
    meta: { title: 'OYSS Hazırlık' },
  },
  {
    path: '/baslangic-testi',
    name: 'diagnostic',
    component: () => import('@/views/auth/DiagnosticView.vue'),
    meta: { requiresAuth: true, title: 'Başlangıç Seviye Testi' },
  },
  {
    path: '/soru-coz',
    name: 'practice',
    component: () => import('@/views/practice/QuestionPracticeView.vue'),
    meta: { requiresAuth: true, title: 'Soru Çöz' },
  },
  {
    path: '/soru-coz/:sessionId(\\d+)',
    name: 'practice-session',
    component: () => import('@/views/practice/QuestionPracticeView.vue'),
    meta: { requiresAuth: true, title: 'Soru Çöz' },
  },
  {
    path: '/sureli-test',
    name: 'timed',
    component: () => import('@/views/practice/TimedExamView.vue'),
    meta: { requiresAuth: true, title: 'Süreli Test' },
  },
  {
    path: '/sureli-test/:sessionId(\\d+)',
    name: 'timed-session',
    component: () => import('@/views/practice/TimedExamView.vue'),
    meta: { requiresAuth: true, keepStudyActive: true, title: 'Süreli Test' },
  },
  {
    path: '/sonuc/:type(practice|timed)/:sessionId(\\d+)',
    name: 'exam-result',
    component: () => import('@/views/practice/ExamResultView.vue'),
    meta: { requiresAuth: true, title: 'Sonuçlar' },
  },
  {
    path: '/hata-analizi',
    name: 'error-analysis',
    component: () => import('@/views/dashboard/ErrorAnalysisView.vue'),
    meta: { requiresAuth: true, title: 'Hata Analizi' },
  },
  {
    path: '/hedeflerim',
    name: 'goals',
    component: () => import('@/views/dashboard/GoalsView.vue'),
    meta: { requiresAuth: true, title: 'Hedeflerim' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

if (import.meta.env.DEV) {
  routes.unshift({
    path: '/dev/maskot',
    name: 'dev-mascot',
    component: () => import('@/views/dev/MascotPreviewView.vue'),
  })
}

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, saved) {
    if (saved) return saved
    // Aynı sayfada yalnızca sorgu değişiyorsa (ör. konu içi bölüm geçişi) kaydırmayı sayfa yönetir.
    if (to.path === from.path) return false
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.init()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'home' }
  }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · OKTOPİ` : 'OKTOPİ — Matematik Öğrenme Platformu'
})

export default router
