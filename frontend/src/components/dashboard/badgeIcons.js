import { Award, Compass, Crosshair, Flame, Footprints, Lightbulb, Target, Zap } from 'lucide-vue-next'

// Sunucudaki Badge.icon değerlerinin (Lucide adı, küçük harf) bileşen karşılıkları.
const ICONS = { footprints: Footprints, lightbulb: Lightbulb, flame: Flame, crosshair: Crosshair, zap: Zap, compass: Compass, target: Target }

export function badgeIcon(name) {
  return ICONS[name] || Award
}
