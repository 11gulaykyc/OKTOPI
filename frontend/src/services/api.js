import axios from 'axios'

const ACCESS_KEY = 'oktopi-access'
const REFRESH_KEY = 'oktopi-refresh'

export const tokenStorage = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = tokenStorage.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Süresi dolan access token'ı tek seferde yeniler; bekleyen istekler aynı yenilemeyi paylaşır.
let refreshPromise = null
let onAuthFailure = () => {}

export function setAuthFailureHandler(handler) {
  onAuthFailure = handler
}

async function refreshAccessToken() {
  const refresh = tokenStorage.refresh
  if (!refresh) throw new Error('no refresh token')
  const { data } = await axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, { refresh })
  tokenStorage.set(data)
  return data.access
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const isAuthCall = original?.url?.startsWith('/auth/login') || original?.url?.startsWith('/auth/register')
    if (error.response?.status !== 401 || !original || original._retried || isAuthCall) {
      return Promise.reject(error)
    }
    original._retried = true
    try {
      refreshPromise = refreshPromise || refreshAccessToken().finally(() => (refreshPromise = null))
      const access = await refreshPromise
      original.headers.Authorization = `Bearer ${access}`
      return api(original)
    } catch (refreshError) {
      tokenStorage.clear()
      onAuthFailure()
      return Promise.reject(error)
    }
  },
)

/*
 * Sunucu tüm hataları tek biçimde döner (backend/config/exceptions.py):
 *   { detail: 'Türkçe mesaj', code: 'invalid' | 'not_found' | 'time_up' | ..., fields?: { alan: ['mesaj'] } }
 */

/** API hatasını kullanıcıya gösterilebilir Türkçe metne çevirir; teknik ayrıntıyı gizler. */
export function errorMessage(error, fallback = 'Bir şeyler ters gitti. Lütfen tekrar dene.') {
  if (!error?.response) return 'Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.'
  const data = error.response.data
  if (error.response.status >= 500) return 'Sunucuda bir sorun oluştu. Biraz sonra tekrar dene.'
  if (typeof data?.detail === 'string') return data.detail
  return fallback
}

/** Hatanın makine okur kodu (ör. 'time_up'); yoksa boş metin. */
export function errorCode(error) {
  return error?.response?.data?.code || ''
}

/** Alan hatalarını { alan: 'mesaj' } biçimine çevirir (iç içe profil alanları dahil). */
export function fieldErrors(error) {
  const data = error?.response?.data?.fields
  if (!data || typeof data !== 'object') return {}
  const result = {}
  const walk = (obj) => {
    for (const [key, value] of Object.entries(obj)) {
      // Alana bağlı olmayan hata zaten `detail` olarak gelir (errorMessage).
      if (key === 'non_field_errors') continue
      if (Array.isArray(value)) result[key] = String(value[0])
      else if (value && typeof value === 'object') walk(value)
    }
  }
  walk(data)
  return result
}

export default api
