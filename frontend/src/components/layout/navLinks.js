import { BookA, Clapperboard, Languages } from 'lucide-vue-next'

/** Navbar ve mobil menüde ortak kullanılan keşif bölümleri. */
export const exploreLinks = [
  { label: 'Matematik Sözlüğü', short: 'Sözlük', icon: BookA, to: '/sozluk' },
  { label: 'MathLingo', short: 'MathLingo', icon: Languages, to: '/mathlingo', hint: 'Matematiği İngilizce öğren' },
  { label: 'Akış', short: 'Akış', icon: Clapperboard, to: '/akis' },
]
