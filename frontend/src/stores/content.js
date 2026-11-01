import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

/**
 * Müfredat içeriği önbelleği. İçerik sürümlü JSON'lardan gelir ve oturum boyunca değişmez;
 * bu yüzden sınıf/konu verisi bir kez çekilip saklanır. Kullanıcıya özel ilerleme burada tutulmaz.
 */
export const useContentStore = defineStore('content', () => {
  const grades = ref({}) // grade -> müfredat ağacı
  const topics = ref({}) // topic_id -> konu detayı
  const oyss = ref(null)
  const pending = new Map()

  function once(key, loader) {
    if (!pending.has(key)) {
      pending.set(
        key,
        loader().finally(() => pending.delete(key)),
      )
    }
    return pending.get(key)
  }

  async function fetchGrade(grade) {
    if (grades.value[grade]) return grades.value[grade]
    return once(`grade:${grade}`, async () => {
      const { data } = await api.get(`/curriculum/grades/${grade}/`)
      grades.value[grade] = data
      return data
    })
  }

  async function fetchTopic(topicId) {
    if (topics.value[topicId]) return topics.value[topicId]
    return once(`topic:${topicId}`, async () => {
      const { data } = await api.get(`/curriculum/topics/${topicId}/`)
      topics.value[topicId] = data
      return data
    })
  }

  async function fetchOyss() {
    if (oyss.value) return oyss.value
    return once('oyss', async () => {
      oyss.value = (await api.get('/curriculum/oyss/')).data
      return oyss.value
    })
  }

  /** Konunun sorularını cevap anahtarı OLMADAN getirir. */
  async function fetchTopicQuestions(topicId) {
    const { data } = await api.get('/questions/', { params: { topic_id: topicId } })
    return data.results
  }

  return { grades, topics, oyss, fetchGrade, fetchTopic, fetchOyss, fetchTopicQuestions }
})
