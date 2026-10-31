import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api, { tokenStorage } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const initialized = ref(false)
  let initPromise = null

  const isAuthenticated = computed(() => !!user.value)
  const displayName = computed(() => user.value?.first_name || user.value?.username || '')
  const grade = computed(() => user.value?.profile?.grade_level ?? null)

  async function fetchMe() {
    const { data } = await api.get('/auth/me/')
    user.value = data
    return data
  }

  /** Sayfa yenilendiğinde kayıtlı token ile kullanıcıyı geri yükler (bir kez çalışır). */
  function init() {
    if (!initPromise) {
      initPromise = (async () => {
        if (tokenStorage.access || tokenStorage.refresh) {
          try {
            await fetchMe()
          } catch {
            tokenStorage.clear()
            user.value = null
          }
        }
        initialized.value = true
      })()
    }
    return initPromise
  }

  async function login(username, password) {
    const { data } = await api.post('/auth/login/', { username, password })
    tokenStorage.set(data)
    user.value = data.user
  }

  async function register(payload) {
    const { data } = await api.post('/auth/register/', payload)
    tokenStorage.set(data)
    user.value = data.user
  }

  async function updateProfile(payload) {
    const { data } = await api.patch('/auth/me/', payload)
    user.value = data
    return data
  }

  function logout() {
    tokenStorage.clear()
    user.value = null
  }

  return { user, initialized, isAuthenticated, displayName, grade, init, fetchMe, login, register, updateProfile, logout }
})
