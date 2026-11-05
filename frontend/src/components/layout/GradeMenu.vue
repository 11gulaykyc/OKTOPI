<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronDown, GraduationCap } from 'lucide-vue-next'
import { GRADES, useGradeStore } from '@/stores/grade'

/** Navbar'daki "Sınıflar" açılır menüsü: tıklanınca 9–12. sınıflar altına listelenir. */
const gradeStore = useGradeStore()
const route = useRoute()
const router = useRouter()
const open = ref(false)
const root = ref(null)

// Sınıf sayfalarındayken (ör. /sinif/10, /sinif/10/soru-coz) menü seçili görünür.
const active = computed(() => route.path.startsWith('/sinif/'))

function choose(g) {
  gradeStore.setGrade(g)
  open.value = false
  router.push({ name: 'grade-hub', params: { grade: g } })
}

function onDocClick(event) {
  if (open.value && root.value && !root.value.contains(event.target)) open.value = false
}
function onKeydown(event) {
  if (event.key === 'Escape') open.value = false
}

watch(() => route.fullPath, () => (open.value = false))
onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold transition"
      :class="
        active || open
          ? 'bg-brand-50 text-brand-700 dark:bg-slate-800 dark:text-brand-300'
          : 'text-slate-600 hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-slate-800'
      "
      aria-haspopup="menu"
      :aria-expanded="open"
      @click="open = !open"
    >
      <GraduationCap class="h-4 w-4" aria-hidden="true" />
      Sınıflar
      <span class="rounded-md bg-brand-600 px-1.5 py-0.5 text-[10px] font-bold leading-none text-white" :title="`Şu an ${gradeStore.grade}. sınıf`">
        {{ gradeStore.grade }}
      </span>
      <ChevronDown class="h-4 w-4 transition" :class="{ 'rotate-180': open }" aria-hidden="true" />
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      leave-active-class="transition duration-100 ease-in"
      leave-to-class="opacity-0 -translate-y-1"
    >
      <ul
        v-if="open"
        role="menu"
        aria-label="Sınıflar"
        class="absolute left-0 top-full z-40 mt-2 w-56 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-lg dark:border-slate-700 dark:bg-slate-900"
      >
        <li v-for="g in GRADES" :key="g" role="none">
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm font-semibold transition"
            :class="
              gradeStore.grade === g
                ? 'bg-brand-600 text-white'
                : 'text-slate-700 hover:bg-brand-50 hover:text-brand-700 dark:text-slate-200 dark:hover:bg-slate-800'
            "
            @click="choose(g)"
          >
            <span class="text-base font-bold">{{ g }}.</span>
            Sınıf
            <span
              v-if="g === gradeStore.ownGrade"
              class="ml-auto rounded-full px-2 py-0.5 text-[10px] font-bold"
              :class="gradeStore.grade === g ? 'bg-white/20 text-white' : 'bg-aqua-500/15 text-aqua-600 dark:text-aqua-400'"
            >
              Senin sınıfın
            </span>
          </button>
        </li>
      </ul>
    </Transition>
  </div>
</template>
