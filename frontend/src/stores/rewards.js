import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

/**
 * Sayfadan bağımsız kazanılan ödüllerin (ör. çalışma süresiyle gelen rozet, hedef, görev) kuyruğu.
 * Uygulama iskeletindeki RewardToast sıradakini gösterir. Soru cevabı gibi ekranda zaten
 * gösterilen ödüller buraya eklenmez.
 */
export const useRewardStore = defineStore('rewards', () => {
  const queue = ref([])
  let nextId = 1

  const current = computed(() => queue.value[0] ?? null)

  function push(rewards) {
    if (!rewards) return
    const notable = rewards.badges?.length || rewards.tasks?.length || rewards.goals?.length
    if (!notable) return
    queue.value.push({ id: nextId++, rewards })
  }

  function dismiss() {
    queue.value.shift()
  }

  function clear() {
    queue.value = []
  }

  return { queue, current, push, dismiss, clear }
})
