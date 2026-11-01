import { defineStore } from 'pinia'
import api from '@/services/api'

/**
 * Soru çözümü ve süreli test API'si. Oturum durumu sunucuda tutulur; sayfa yenilense de
 * `/sessions/:tür/:id/` ile kaldığı yerden geri yüklenir. Cevap anahtarı istemcide yoktur:
 * soru çözümünde her cevaptan sonra, süreli testte yalnızca test bittikten sonra gelir.
 */
export const useExamStore = defineStore('exam', () => {
  async function startPractice(payload) {
    return (await api.post('/exams/practice/start/', payload)).data
  }

  async function startTimed(payload) {
    return (await api.post('/exams/timed/start/', payload)).data
  }

  async function fetchSession(type, id) {
    return (await api.get(`/exams/sessions/${type}/${id}/`)).data
  }

  async function fetchResult(type, id) {
    return (await api.get(`/exams/sessions/${type}/${id}/result/`)).data
  }

  async function fetchRecent(limit = 5) {
    return (await api.get('/exams/sessions/', { params: { limit } })).data
  }

  /** Soru çözümünde değerlendirmeyi, süreli testte yalnızca kayıt onayını döner. */
  async function submitAnswer(type, sessionId, questionId, selectedOption) {
    const { data } = await api.post('/exams/submit-answer/', {
      session_type: type,
      session_id: sessionId,
      question_id: questionId,
      selected_option: selectedOption || null,
    })
    return data
  }

  async function finish(type, sessionId) {
    return (await api.post('/exams/finish-exam/', { session_type: type, session_id: sessionId })).data
  }

  return { startPractice, startTimed, fetchSession, fetchResult, fetchRecent, submitAnswer, finish }
})
