<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, shallowRef, watch } from 'vue'
import JXG from 'jsxgraph'
import { RotateCcw, ZoomIn, ZoomOut } from 'lucide-vue-next'
import { useThemeStore } from '@/stores/theme'
import KatexRenderer from './KatexRenderer.vue'

/**
 * Konu JSON'undaki `visualizations` kaydını JSXGraph ile çizer (şema: content/schemas/topic.py).
 *   linear      → y = m·x + n, eksen kesişimleri ve eğim üçgeni
 *   parabola    → y = a·x² + b·x + c, kökler, tepe noktası, simetri ekseni
 *   exponential → y = aˣ ve (n, aⁿ) noktası
 *   triangle    → A, B açıları; C = 180° − A − B
 *
 * Dokunmatik ekranlar: tahta işaretçi olaylarını dinlemez; tek parmakla sayfa rahatça kayar.
 * Etkileşim büyük dokunma alanlı yerel kaydırıcılarla (range input) yapılır.
 */
const props = defineProps({
  visualization: { type: Object, required: true },
})

const theme = useThemeStore()
const boardId = `jxg-${props.visualization.id}-${Math.random().toString(36).slice(2, 8)}`
const board = shallowRef(null)

const type = computed(() => props.visualization.type)
const sliders = computed(() => props.visualization.sliders)
const sliderByName = computed(() => Object.fromEntries(sliders.value.map((s) => [s.name, s])))
const values = reactive(Object.fromEntries(props.visualization.sliders.map((s) => [s.name, s.value])))

const aspectRatio = computed(() => {
  const [xMin, yMax, xMax, yMin] = props.visualization.bounds
  return `${xMax - xMin} / ${yMax - yMin}`
})

const PALETTE = {
  light: { axis: '#94a3b8', grid: '#e2e8f0', text: '#334155', main: '#2563eb', accent: '#0d9488', mark: '#be185d', vertex: '#9333ea' },
  dark: { axis: '#64748b', grid: '#1e293b', text: '#cbd5e1', main: '#60a5fa', accent: '#2dd4bf', mark: '#f472b6', vertex: '#c084fc' },
}

// --- Sayı biçimlendirme (LaTeX, Türkçe ondalık virgülü) ---
function round(x, digits = 2) {
  const f = 10 ** digits
  return Math.round(x * f) / f
}
function num(x) {
  const r = round(x)
  return String(Object.is(r, -0) ? 0 : r).replace('.', '{,}')
}
/** Değer yuvarlandıysa "≈", tam ise "=" döner. */
function eq(x) {
  return Math.abs(x - round(x)) > 1e-9 ? '\\approx' : '='
}
/** [[katsayı, 'x^2'], [katsayı, 'x'], [katsayı, '']] → "2x^2 - x + 3" */
function polynomial(terms) {
  let out = ''
  for (const [coef, variable] of terms) {
    if (coef === 0) continue
    const abs = Math.abs(coef)
    const body = variable && abs === 1 ? variable : `${num(abs)}${variable}`
    if (!out) out = coef < 0 ? `-${body}` : body
    else out += coef < 0 ? ` - ${body}` : ` + ${body}`
  }
  return out || '0'
}

// --- Üçgen geometrisi ---
const MIN_THIRD_ANGLE = 5
const rad = (deg) => (deg * Math.PI) / 180

/** A ve B açılarından, verilen bounds içine sığacak şekilde ölçeklenmiş köşe koordinatları. */
function triangleVertices() {
  const alpha = rad(values.A)
  const beta = rad(values.B)
  // AB = 1 iken sinüs teoremiyle AC = sin(B) / sin(A + B)
  const ac = Math.sin(beta) / Math.sin(alpha + beta)
  const raw = [
    [0, 0],
    [1, 0],
    [ac * Math.cos(alpha), ac * Math.sin(alpha)],
  ]
  const xs = raw.map((p) => p[0])
  const ys = raw.map((p) => p[1])
  const [xMin, yMax, xMax, yMin] = props.visualization.bounds
  const pad = 0.12 * Math.min(xMax - xMin, yMax - yMin)
  const width = Math.max(...xs) - Math.min(...xs)
  const height = Math.max(...ys) - Math.min(...ys)
  const scale = Math.min((xMax - xMin - 2 * pad) / width, (yMax - yMin - 2 * pad) / height)
  const dx = xMin + (xMax - xMin - width * scale) / 2 - Math.min(...xs) * scale
  const dy = yMin + (yMax - yMin - height * scale) / 2
  return raw.map(([x, y]) => [x * scale + dx, y * scale + dy])
}

function setValue(name, raw) {
  const value = Number(raw)
  values[name] = value
  if (type.value !== 'triangle') return
  // C açısı en az MIN_THIRD_ANGLE kalsın: diğer açı gerekirse kendiliğinden küçülür.
  const other = name === 'A' ? 'B' : 'A'
  const limit = 180 - MIN_THIRD_ANGLE - value
  if (values[other] > limit) values[other] = Math.max(sliderByName.value[other].min, limit)
  if (values.A + values.B > 180 - MIN_THIRD_ANGLE) values[name] = 180 - MIN_THIRD_ANGLE - values[other]
}

function reset() {
  for (const s of sliders.value) values[s.name] = s.value
  board.value?.setBoundingBox([...props.visualization.bounds], false)
}

// --- Tahta ---
let dynamicUpdate = () => {}

function destroy() {
  if (board.value) JXG.JSXGraph.freeBoard(board.value)
  board.value = null
}

function build() {
  destroy()
  const c = PALETTE[theme.theme === 'dark' ? 'dark' : 'light']
  const b = JXG.JSXGraph.initBoard(boardId, {
    boundingbox: [...props.visualization.bounds],
    keepaspectratio: false,
    axis: false,
    showCopyright: false,
    showNavigation: false,
    showInfobox: false,
    registerEvents: { fullscreen: false, keyboard: false, pointer: false, resize: true, wheel: false },
  })
  board.value = b
  dynamicUpdate = () => {}

  const label = { strokeColor: c.text, fontSize: 13, highlight: false }
  const point = (coords, color, name = '', extra = {}) =>
    b.create('point', coords, { name, withLabel: !!name, size: 3, fixed: true, highlight: false, strokeColor: color, fillColor: color, label, ...extra })
  const hidden = (coords) => b.create('point', coords, { visible: false, fixed: true, withLabel: false })

  if (type.value !== 'triangle') {
    // majorHeight: -1 → bölme çizgileri tahta boyunca uzar ve kareli zemin oluşturur.
    const ticks = { majorHeight: -1, minorTicks: 0, insertTicks: false, ticksDistance: 1, drawZero: false, strokeColor: c.grid, strokeOpacity: 1, label }
    for (const dir of [[1, 0], [0, 1]]) {
      b.create('axis', [[0, 0], dir], { strokeColor: c.axis, highlight: false, ticks, name: '', withLabel: false })
    }
  }

  if (type.value === 'linear') {
    const f = (x) => values.m * x + values.n
    b.create('functiongraph', [f], { strokeColor: c.main, strokeWidth: 3, highlight: false })
    const p0 = hidden([0, () => values.n])
    const p1 = hidden([1, () => values.n])
    const p2 = hidden([1, () => values.n + values.m])
    b.create('polygon', [p0, p1, p2], {
      fillColor: c.accent,
      fillOpacity: 0.18,
      highlight: false,
      vertices: { visible: false },
      borders: { strokeColor: c.accent, dash: 2, strokeWidth: 2, highlight: false },
    })
    b.create('text', [0.4, () => values.n - (values.m >= 0 ? 0.45 : -0.25), '1'], label)
    b.create('text', [1.15, () => values.n + values.m / 2, 'm'], { ...label, strokeColor: c.accent })
    point([0, () => values.n], c.main)
    point([() => (values.m ? -values.n / values.m : NaN), 0], c.mark)
  }

  if (type.value === 'parabola') {
    const f = (x) => values.a * x * x + values.b * x + values.c
    const disc = () => values.b ** 2 - 4 * values.a * values.c
    const vx = () => (values.a ? -values.b / (2 * values.a) : NaN)
    const root = (sign) => () => (values.a && disc() >= 0 ? (-values.b + sign * Math.sqrt(disc())) / (2 * values.a) : NaN)
    b.create('functiongraph', [f], { strokeColor: c.main, strokeWidth: 3, highlight: false })
    b.create('line', [hidden([vx, 0]), hidden([vx, 1])], { strokeColor: c.vertex, dash: 2, strokeWidth: 1.5, highlight: false })
    point([vx, () => f(vx())], c.vertex, 'T')
    point([root(-1), 0], c.mark)
    point([root(1), 0], c.mark)
  }

  if (type.value === 'exponential') {
    const f = (x) => values.a ** x
    b.create('functiongraph', [f], { strokeColor: c.main, strokeWidth: 3, highlight: false })
    const foot = hidden([() => values.n, 0])
    const top = point([() => values.n, () => f(values.n)], c.mark)
    const side = hidden([0, () => f(values.n)])
    b.create('segment', [foot, top], { strokeColor: c.mark, dash: 2, highlight: false })
    b.create('segment', [side, top], { strokeColor: c.mark, dash: 2, highlight: false })
  }

  if (type.value === 'triangle') {
    const vertex = (i) => [() => triangleVertices()[i][0], () => triangleVertices()[i][1]]
    const [A, B, C] = ['A', 'B', 'C'].map((name, i) =>
      point(vertex(i), c.main, name, { label: { ...label, fontSize: 15, offset: i === 2 ? [-4, 16] : [i === 0 ? -16 : 8, -12] } }),
    )
    b.create('polygon', [A, B, C], { fillColor: c.main, fillOpacity: 0.08, highlight: false, vertices: { visible: false }, borders: { visible: false } })
    // Kenarlar: a = BC, b = AC, c = AB (her kenar karşısındaki köşenin adını taşır)
    const sides = { a: [B, C], b: [A, C], c: [A, B] }
    const segments = Object.fromEntries(
      Object.entries(sides).map(([name, [p, q]]) => [
        name,
        b.create('segment', [p, q], { strokeWidth: 3, highlight: false, name, withLabel: true, label: { ...label, offset: [6, 6] } }),
      ]),
    )
    const arcs = [
      [B, A, C],
      [C, B, A],
      [A, C, B],
    ]
    for (const [p, q, r] of arcs) {
      b.create('nonreflexangle', [p, q, r], { radius: 0.7, withLabel: false, fillColor: c.accent, fillOpacity: 0.25, strokeColor: c.accent, highlight: false })
    }
    dynamicUpdate = () => {
      // En büyük açının karşısındaki (en uzun) kenar vurgulanır.
      const longest = { A: 'a', B: 'b', C: 'c' }[largestAngle.value]
      for (const [name, seg] of Object.entries(segments)) seg.setAttribute({ strokeColor: name === longest ? c.mark : c.main })
    }
  }

  dynamicUpdate()
  b.update()
}

watch(values, () => {
  dynamicUpdate()
  board.value?.update()
})
watch(() => theme.theme, build)
onMounted(build)
onBeforeUnmount(destroy)

function zoom(direction) {
  if (direction > 0) board.value?.zoomIn()
  else board.value?.zoomOut()
}

// --- Okumalar ---
const angleC = computed(() => (type.value === 'triangle' ? 180 - values.A - values.B : null))
const largestAngle = computed(() => {
  const angles = { A: values.A, B: values.B, C: angleC.value }
  return Object.keys(angles).reduce((best, k) => (angles[k] > angles[best] ? k : best), 'A')
})

const readouts = computed(() => {
  const v = values
  if (type.value === 'linear') {
    const lines = [`$y = ${polynomial([[v.m, 'x'], [v.n, '']])}$`]
    if (v.m > 0) lines.push(`Eğim $m = ${num(v.m)} > 0$: $x$ bir artınca $y$ ${num(v.m).replace('{,}', ',')} artar, doğru **yükselir**.`)
    else if (v.m < 0) lines.push(`Eğim $m = ${num(v.m)} < 0$: $x$ bir artınca $y$ ${num(-v.m).replace('{,}', ',')} azalır, doğru **alçalır**.`)
    else lines.push('Eğim $m = 0$: doğru $x$ eksenine **paraleldir** (sabit fonksiyon).')
    lines.push(`$y$ eksenini kestiği nokta: $(0,\\ ${num(v.n)})$`)
    if (v.m) lines.push(`$x$ eksenini kestiği nokta: $\\left(${num(-v.n / v.m)},\\ 0\\right)$`)
    return lines
  }
  if (type.value === 'parabola') {
    const lines = [`$y = ${polynomial([[v.a, 'x^2'], [v.b, 'x'], [v.c, '']])}$`]
    if (!v.a) {
      lines.push('$a = 0$ iken $x^2$ terimi kaybolur: grafik parabol değil, **doğrudur**.')
      return lines
    }
    const d = v.b ** 2 - 4 * v.a * v.c
    lines.push(`$\\Delta = b^2 - 4ac = ${num(d)}$`)
    if (d > 0) {
      const r1 = (-v.b - Math.sqrt(d)) / (2 * v.a)
      const r2 = (-v.b + Math.sqrt(d)) / (2 * v.a)
      const [x1, x2] = [r1, r2].sort((p, q) => p - q)
      lines.push(`$\\Delta > 0$: **iki** gerçek kök, $x_1 ${eq(x1)} ${num(x1)}$ ve $x_2 ${eq(x2)} ${num(x2)}$`)
    } else if (d === 0) {
      lines.push(`$\\Delta = 0$: **çakışık** kök, $x = ${num(-v.b / (2 * v.a))}$ (parabol $x$ eksenine teğet)`)
    } else {
      lines.push('$\\Delta < 0$: gerçek kök **yok** (parabol $x$ eksenini kesmez)')
    }
    const r = -v.b / (2 * v.a)
    const k = v.a * r * r + v.b * r + v.c
    lines.push(`Tepe noktası $T(${num(r)},\\ ${num(k)})$, kollar **${v.a > 0 ? 'yukarı' : 'aşağı'}** bakıyor.`)
    return lines
  }
  if (type.value === 'exponential') {
    const value = v.a ** v.n
    const lines = [`$y = ${num(v.a)}^x$`]
    if (v.n < 0) lines.push(`$${num(v.a)}^{${num(v.n)}} = \\dfrac{1}{${num(v.a)}^{${num(-v.n)}}} ${eq(value)} ${num(value)}$`)
    else lines.push(`$${num(v.a)}^{${num(v.n)}} ${eq(value)} ${num(value)}$`)
    if (v.n < 0) lines.push('Negatif kuvvet **çarpmaya çevrilmez** ve sonucu **negatif yapmaz**: tabanın tersinin pozitif kuvvetidir.')
    if (v.a === 1) lines.push('Taban $1$ iken her kuvvet $1$ verir; grafik yatay bir doğrudur.')
    else if (v.a < 1) lines.push('Taban $0$ ile $1$ arasındayken grafik soldan sağa **azalır**.')
    return lines
  }
  // triangle
  const opposite = { A: 'a = |BC|', B: 'b = |AC|', C: 'c = |AB|' }[largestAngle.value]
  return [
    `$m(\\widehat{A}) + m(\\widehat{B}) + m(\\widehat{C}) = ${v.A}^\\circ + ${v.B}^\\circ + ${angleC.value}^\\circ = 180^\\circ$`,
    `En büyük açı $\\widehat{${largestAngle.value}}$, karşısındaki kenar $${opposite}$ en uzun kenar (pembe).`,
    `$C$ köşesindeki dış açı: $${v.A}^\\circ + ${v.B}^\\circ = ${v.A + v.B}^\\circ$`,
  ]
})

const boardLabel = computed(() => `${props.visualization.title}. ${readouts.value[0].replace(/\$/g, '')}`)
</script>

<template>
  <figure class="overflow-hidden rounded-xl border border-aqua-300/60 bg-aqua-50/40 dark:border-aqua-500/30 dark:bg-aqua-500/5">
    <figcaption class="border-b border-aqua-300/40 px-4 py-3 dark:border-aqua-500/20">
      <p class="text-xs font-bold uppercase tracking-wider text-aqua-700 dark:text-aqua-300">Etkileşimli grafik</p>
      <p class="font-bold text-slate-900 dark:text-white">{{ visualization.title }}</p>
      <KatexRenderer v-if="visualization.description" :text="visualization.description" class="mt-1 text-sm text-slate-600 dark:text-slate-300" />
    </figcaption>

    <div class="grid gap-4 p-3 sm:p-4 md:grid-cols-[minmax(0,1fr)_minmax(0,16rem)]">
      <div class="relative min-w-0">
        <div
          :id="boardId"
          class="jxgbox w-full rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900"
          :style="{ aspectRatio }"
          role="img"
          :aria-label="boardLabel"
        />
        <div v-if="type !== 'triangle'" class="absolute right-2 top-2 flex gap-1">
          <button type="button" class="btn-secondary !p-1.5" aria-label="Yakınlaştır" @click="zoom(1)"><ZoomIn class="h-4 w-4" /></button>
          <button type="button" class="btn-secondary !p-1.5" aria-label="Uzaklaştır" @click="zoom(-1)"><ZoomOut class="h-4 w-4" /></button>
        </div>
      </div>

      <div class="min-w-0 space-y-4">
        <div v-for="s in sliders" :key="s.name">
          <div class="flex items-baseline justify-between gap-2">
            <label :for="`${boardId}-${s.name}`" class="text-sm font-semibold text-slate-700 dark:text-slate-200"><KatexRenderer :text="s.label" inline /></label>
            <output :for="`${boardId}-${s.name}`" class="font-mono text-sm font-bold tabular-nums text-brand-700 dark:text-brand-300">
              {{ String(values[s.name]).replace('.', ',') }}{{ type === 'triangle' ? '°' : '' }}
            </output>
          </div>
          <input
            :id="`${boardId}-${s.name}`"
            type="range"
            class="slider mt-1 w-full"
            :min="s.min"
            :max="s.max"
            :step="s.step"
            :value="values[s.name]"
            @input="setValue(s.name, $event.target.value)"
          />
        </div>
        <button type="button" class="btn-ghost !px-2 !py-1 text-xs" @click="reset"><RotateCcw class="h-3.5 w-3.5" /> Başlangıç değerleri</button>
      </div>
    </div>

    <ul class="space-y-1.5 border-t border-aqua-300/40 px-4 py-3 text-sm text-slate-700 dark:border-aqua-500/20 dark:text-slate-200" aria-live="polite">
      <li v-for="(line, i) in readouts" :key="i" class="min-w-0 overflow-x-auto" :class="{ 'text-base font-bold': i === 0 }">
        <KatexRenderer :text="line" inline />
      </li>
    </ul>
  </figure>
</template>

<style scoped>
/* JSXGraph'ın kendi CSS dosyası paket dışına açılmadığı için gereken kurallar burada. */
.jxgbox {
  position: relative;
  overflow: hidden;
  touch-action: pan-y;
}
.jxgbox :deep(.JXGtext) {
  font-family: inherit;
  font-weight: 600;
  white-space: nowrap;
  pointer-events: none;
}

/* Dokunmatik ekranlarda rahat tutulan kaydırıcı */
.slider {
  height: 2rem;
  accent-color: var(--color-brand-600);
  cursor: pointer;
  touch-action: manipulation;
}
</style>
