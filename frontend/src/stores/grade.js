import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useAuthStore } from './auth'

const STORAGE_KEY = 'oktopi-browse-grade'
export const GRADES = [9, 10, 11, 12]

function readSaved() {
  try {
    const value = Number(sessionStorage.getItem(STORAGE_KEY))
    return GRADES.includes(value) ? value : null
  } catch {
    return null
  }
}

/**
 * Göz atılan sınıf düzeyi. Varsayılan öğrencinin kendi sınıfıdır; üst bardaki seçiciyle
 * kısıtlama olmadan diğer sınıfların içeriğine geçilebilir. Profildeki sınıf değişmez.
 */
export const useGradeStore = defineStore('grade', () => {
  const auth = useAuthStore()
  const override = ref(readSaved())

  const ownGrade = computed(() => auth.grade)
  const grade = computed(() => override.value ?? ownGrade.value ?? GRADES[0])
  const isOwnGrade = computed(() => ownGrade.value != null && grade.value === ownGrade.value)

  function persist() {
    try {
      if (override.value == null) sessionStorage.removeItem(STORAGE_KEY)
      else sessionStorage.setItem(STORAGE_KEY, String(override.value))
    } catch {}
  }

  function setGrade(value) {
    const g = Number(value)
    if (!GRADES.includes(g)) return
    override.value = g === ownGrade.value ? null : g
    persist()
  }

  function reset() {
    override.value = null
    persist()
  }

  // Başka bir kullanıcı giriş yaptığında ya da çıkış yapıldığında kendi sınıfına dön.
  watch(
    () => auth.user?.id,
    (id, previous) => {
      if (previous !== undefined && id !== previous) reset()
    },
  )

  return { grade, ownGrade, isOwnGrade, setGrade, reset }
})
