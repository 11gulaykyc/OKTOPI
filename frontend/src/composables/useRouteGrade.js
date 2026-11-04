import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGradeStore } from '@/stores/grade'

/**
 * Adresinde sınıf bulunan sayfalar (`/sinif/:grade/...`) için: adresteki sınıf göz atılan sınıf olur,
 * üst bardaki sınıf seçiciyle başka sınıfa geçilirse adres de aynı sayfanın o sınıfına güncellenir.
 */
export function useRouteGrade() {
  const route = useRoute()
  const router = useRouter()
  const gradeStore = useGradeStore()

  const grade = computed(() => Number(route.params.grade))

  watch(grade, (g) => g && gradeStore.setGrade(g), { immediate: true })
  watch(
    () => gradeStore.grade,
    (g) => {
      if (route.params.grade && g !== grade.value) router.replace({ params: { ...route.params, grade: g } })
    },
  )

  return grade
}
