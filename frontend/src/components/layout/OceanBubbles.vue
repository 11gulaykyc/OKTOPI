<script setup>
/**
 * Arka planda sürekli ve rastgele yükselen baloncuklar (canvas).
 *
 * İki derinlik katmanı vardır:
 *   - far  : uzaktaki küçük, soluk, yavaş baloncuklar (derinlik hissi verir)
 *   - near : öndeki büyük, parlak, 3B gölgelendirilmiş baloncuklar (ileride içlerine yazı yazılacak)
 *
 * Kurallar:
 * - Boyut, hız, yalpalama ve saydamlık her baloncuk için rastgeledir.
 * - Baloncuklar birbirine değmez: çakışan çiftler her karede aralarında boşluk kalacak şekilde itilir,
 *   yeni baloncuk yalnızca boş bir yerden doğar.
 * - Üstten çıkan baloncuk alttan yeniden doğar; akış hiç durmaz.
 * - Hareket azaltma tercihi olan kullanıcılarda çizilmez; sekme arka plandayken rAF kendiliğinden durur.
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'

const LAYERS = {
  far: { minR: 4, maxR: 11, speed: [8, 18], alpha: [0.25, 0.45], wobble: [3, 8], area: 20000, max: 55, gap: 4 },
  near: { minR: 16, maxR: 44, speed: [18, 34], alpha: [0.6, 0.95], wobble: [6, 16], area: 26000, max: 42, gap: 10 },
}

// Öndeki baloncukların içinde yazacak matematik ifadeleri; baloncuk boyutuna göre uygun uzunluktaki havuzdan seçilir.
const MATH_TERMS = {
  short: [
    '0', '1', '2', '3', '5', '7', '9', '+', '−', '×', '÷', '=', '±', '≠', '≤', '≥', '%', '°',
    'π', 'e', 'i', '∑', '∏', '∫', '∂', '∞', 'Δ', 'θ', 'α', 'β', 'λ', 'φ', 'x', 'y',
    'x²', '2ⁿ', 'n!', '√2', '∈', '∪', '∩', '⊂', '∅', 'ℝ', 'ℕ', 'ℤ', 'ℚ', '∠', '⊥', '△', '∥', '½',
  ],
  medium: [
    'a³', '10⁻²', 'x⁻¹', '3⁴', 'eˣ', '√x', '√16', '∛27', '∜81', 'log', 'ln x', 'sin', 'cos', 'tan', 'cot',
    'lim', 'f(x)', '|x|', 'dx', '¾', 'aₙ', '∑aₙ', '∫dx', 'πr²', '2³=8', 'x₁', 'f′(x)', 'dy/dx', 'P(A)',
  ],
  long: [
    'a²+b²=c²', 'Δ=b²−4ac', 'log₂8=3', 'sin²x+cos²x', 'lim x→∞', '∫₀¹ x dx', '∑ₖ₌₁ⁿ k', '(a+b)²',
    '√(a²+b²)', 'y=mx+n', 'f(g(x))', 'eⁱᶿ', 'aᵐ·aⁿ', '(xⁿ)′', 'ln(e)=1', 'x=−b/2a', 'C(n,r)', '√a·√b',
  ],
}
const MATH_FONT = '"Cambria Math", "STIX Two Math", "Latin Modern Math", "Times New Roman", serif'

const canvas = ref(null)
let ctx = null
let bubbles = []
let frame = 0
let lastTime = 0
let width = 0
let height = 0
let motionQuery = null

const rand = (min, max) => min + Math.random() * (max - min)
const targetCount = (layer) => {
  const cfg = LAYERS[layer]
  return Math.max(6, Math.min(cfg.max, Math.round((width * height) / cfg.area)))
}
const gapBetween = (a, b) => Math.max(LAYERS[a.layer].gap, LAYERS[b.layer].gap)

function overlaps(x, y, r, layer) {
  const gap = LAYERS[layer].gap
  return bubbles.some((o) => Math.hypot(o.x - x, o.y - y) < o.r + r + Math.max(gap, LAYERS[o.layer].gap))
}

// Baloncuğun boyutuna uygun, şu an ekranda görünmeyen bir ifade seçer ve sığacak yazı boyutunu hesaplar.
function pickLabel(r) {
  const pool = [...MATH_TERMS.short]
  if (r >= 24) pool.push(...MATH_TERMS.medium)
  if (r >= 34) pool.push(...MATH_TERMS.long, ...MATH_TERMS.long) // büyük baloncuklarda formüller öne çıksın
  const visible = new Set(bubbles.map((b) => b.label))
  const fresh = pool.filter((term) => !visible.has(term))
  const label = (fresh.length ? fresh : pool)[Math.floor(Math.random() * (fresh.length || pool.length))]

  // Yazı, baloncuğun iç çapının ~%75'ine sığacak şekilde küçültülür.
  let size = r * (label.length <= 2 ? 0.95 : 0.7)
  ctx.font = `${size}px ${MATH_FONT}`
  const w = ctx.measureText(label).width
  const maxW = r * 1.5
  if (w > maxW) size *= maxW / w
  return { label, fontSize: size }
}

// Boş bir yer bulunamazsa null döner; eksik baloncuk sonraki karelerde tamamlanır.
function makeBubble(layer, startAnywhere = false) {
  const cfg = LAYERS[layer]
  const r = layer === 'near' && Math.random() < 0.35 ? rand(27, cfg.maxR) : rand(cfg.minR, layer === 'near' ? 26 : cfg.maxR)
  for (let attempt = 0; attempt < 12; attempt++) {
    const x = rand(r, Math.max(r, width - r))
    const y = startAnywhere ? rand(r, height - r) : height + r + rand(0, 160)
    if (!overlaps(x, y, r, layer)) {
      return {
        layer,
        r,
        x,
        y,
        speed: rand(...cfg.speed) + r * 0.3, // px/sn
        wobbleAmp: rand(...cfg.wobble),
        wobbleFreq: rand(0.3, 0.9),
        phase: rand(0, Math.PI * 2),
        alpha: rand(...cfg.alpha),
        ...(layer === 'near' ? pickLabel(r) : { label: null, fontSize: 0 }),
      }
    }
  }
  return null
}

function fill(layer, startAnywhere) {
  const target = targetCount(layer)
  let count = bubbles.filter((b) => b.layer === layer).length
  const tries = startAnywhere ? target * 3 : 1
  for (let i = 0; count < target && i < tries; i++) {
    const b = makeBubble(layer, startAnywhere)
    if (b) {
      bubbles.push(b)
      count++
    }
  }
}

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  width = window.innerWidth
  height = window.innerHeight
  canvas.value.width = width * dpr
  canvas.value.height = height * dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  for (const layer of Object.keys(LAYERS)) {
    const target = targetCount(layer)
    let seen = 0
    bubbles = bubbles.filter((b) => b.layer !== layer || ++seen <= target)
  }
  fill('near', true)
  fill('far', true)
}

// Çakışan baloncukları merkezlerini birleştiren doğru boyunca ayırır; küçük olan daha çok yer değiştirir.
function separate() {
  for (let i = 0; i < bubbles.length; i++) {
    for (let j = i + 1; j < bubbles.length; j++) {
      const a = bubbles[i]
      const b = bubbles[j]
      const dx = b.x - a.x
      const dy = b.y - a.y
      const min = a.r + b.r + gapBetween(a, b)
      if (Math.abs(dx) >= min || Math.abs(dy) >= min) continue
      const dist = Math.hypot(dx, dy) || 0.01
      if (dist < min) {
        const overlap = min - dist
        const wa = b.r / (a.r + b.r)
        const nx = dx / dist
        const ny = dy / dist
        a.x -= nx * overlap * wa
        a.y -= ny * overlap * wa
        b.x += nx * overlap * (1 - wa)
        b.y += ny * overlap * (1 - wa)
      }
    }
  }
}

function drawFar(b, dark) {
  const { x, y, r, alpha: a } = b
  const tint = dark ? '125, 211, 252' : '14, 165, 233'
  const g = ctx.createRadialGradient(x, y, r * 0.2, x, y, r)
  g.addColorStop(0, `rgba(255, 255, 255, ${0.04 * a})`)
  g.addColorStop(0.8, `rgba(${tint}, ${0.18 * a})`)
  g.addColorStop(1, `rgba(${tint}, ${0.45 * a})`)
  ctx.beginPath()
  ctx.arc(x, y, r, 0, Math.PI * 2)
  ctx.fillStyle = g
  ctx.fill()
  ctx.beginPath()
  ctx.arc(x - r * 0.35, y - r * 0.35, r * 0.22, 0, Math.PI * 2)
  ctx.fillStyle = `rgba(255, 255, 255, ${0.5 * a})`
  ctx.fill()
}

function drawNear(b, dark) {
  const { x, y, r, alpha: a } = b
  const body = dark ? '186, 230, 253' : '255, 255, 255'
  const edge = dark ? '125, 211, 252' : '14, 165, 233'

  // 1) Gövde: ortası neredeyse saydam, kenara doğru yoğunlaşan (Fresnel etkisi), ışık sol üstten.
  const g = ctx.createRadialGradient(x - r * 0.25, y - r * 0.3, r * 0.05, x, y, r)
  g.addColorStop(0, `rgba(${body}, ${0.1 * a})`)
  g.addColorStop(0.55, `rgba(${body}, ${0.04 * a})`)
  g.addColorStop(0.85, `rgba(${edge}, ${0.18 * a})`)
  g.addColorStop(1, `rgba(${edge}, ${0.5 * a})`)
  ctx.beginPath()
  ctx.arc(x, y, r, 0, Math.PI * 2)
  ctx.fillStyle = g
  ctx.fill()

  // 2) Kenar çizgisi: ışık alan sol üst parlak, gölgede kalan sağ alt koyu.
  const rim = ctx.createLinearGradient(x - r, y - r, x + r, y + r)
  rim.addColorStop(0, `rgba(255, 255, 255, ${0.9 * a})`)
  rim.addColorStop(0.5, `rgba(${edge}, ${0.45 * a})`)
  rim.addColorStop(1, `rgba(${dark ? '56, 189, 248' : '2, 132, 199'}, ${0.65 * a})`)
  ctx.lineWidth = Math.max(1.2, r * 0.06)
  ctx.strokeStyle = rim
  ctx.stroke()

  // 3) Sabun köpüğü yanardönerliği: kenarın hemen içinde ince mor-turkuaz parıltı.
  ctx.beginPath()
  ctx.arc(x, y, r * 0.9, Math.PI * 0.05, Math.PI * 0.7)
  ctx.lineWidth = Math.max(1, r * 0.05)
  ctx.strokeStyle = `rgba(196, 181, 253, ${0.35 * a})`
  ctx.stroke()
  ctx.beginPath()
  ctx.arc(x, y, r * 0.9, Math.PI * 1.1, Math.PI * 1.45)
  ctx.strokeStyle = `rgba(94, 234, 212, ${0.35 * a})`
  ctx.stroke()

  // 4) Alt iç yansıma: karşı duvardan dönen ışığın oluşturduğu hilal.
  ctx.beginPath()
  ctx.arc(x, y, r * 0.78, Math.PI * 0.2, Math.PI * 0.8)
  ctx.lineWidth = Math.max(1, r * 0.08)
  ctx.lineCap = 'round'
  ctx.strokeStyle = `rgba(255, 255, 255, ${0.28 * a})`
  ctx.stroke()

  // 5) Matematik ifadesi: baloncuğun içinde, parlamanın altında kalır (cam arkasındaymış gibi).
  if (b.label) {
    ctx.font = `${b.fontSize}px ${MATH_FONT}`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillStyle = dark ? `rgba(224, 242, 254, ${0.85 * a})` : `rgba(3, 105, 161, ${0.8 * a})`
    ctx.shadowColor = dark ? 'rgba(14, 165, 233, 0.6)' : 'rgba(255, 255, 255, 0.9)'
    ctx.shadowBlur = b.r * 0.15
    ctx.fillText(b.label, x, y + b.fontSize * 0.04)
    ctx.shadowBlur = 0
    ctx.shadowColor = 'transparent'
  }

  // 6) Ana parlama ve küçük ikincil nokta.
  ctx.beginPath()
  ctx.ellipse(x - r * 0.4, y - r * 0.42, r * 0.24, r * 0.12, -Math.PI / 4, 0, Math.PI * 2)
  ctx.fillStyle = `rgba(255, 255, 255, ${0.9 * a})`
  ctx.fill()
  ctx.beginPath()
  ctx.arc(x - r * 0.12, y - r * 0.62, r * 0.06, 0, Math.PI * 2)
  ctx.fillStyle = `rgba(255, 255, 255, ${0.75 * a})`
  ctx.fill()
}

function tick(time) {
  const dt = Math.min(0.05, (time - lastTime) / 1000 || 0)
  lastTime = time
  const t = time / 1000
  const dark = document.documentElement.classList.contains('dark')

  for (const b of bubbles) {
    b.y -= b.speed * dt
    b.x += Math.cos(t * b.wobbleFreq + b.phase) * b.wobbleAmp * b.wobbleFreq * dt
  }
  separate()

  // Ekrandan çıkanları kaldır, yerlerine alttan yenilerini doğur.
  bubbles = bubbles.filter((b) => b.y >= -b.r - 12)
  fill('near', false)
  fill('far', false)

  ctx.clearRect(0, 0, width, height)
  // Önce uzaktakiler, sonra öndekiler çizilir.
  for (const b of bubbles) {
    b.x = Math.min(width - b.r, Math.max(b.r, b.x))
    if (b.layer === 'far') drawFar(b, dark)
  }
  for (const b of bubbles) if (b.layer === 'near') drawNear(b, dark)

  frame = requestAnimationFrame(tick)
}

function start() {
  if (frame) return
  lastTime = performance.now()
  frame = requestAnimationFrame(tick)
}

function stop() {
  cancelAnimationFrame(frame)
  frame = 0
  ctx?.clearRect(0, 0, width, height)
}

function onMotionChange(e) {
  e.matches ? stop() : start()
}

onMounted(() => {
  ctx = canvas.value.getContext('2d')
  resize()
  window.addEventListener('resize', resize)
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  motionQuery.addEventListener('change', onMotionChange)
  if (!motionQuery.matches) start()
})

onBeforeUnmount(() => {
  stop()
  window.removeEventListener('resize', resize)
  motionQuery?.removeEventListener('change', onMotionChange)
})
</script>

<template>
  <canvas ref="canvas" class="absolute inset-0 h-full w-full" aria-hidden="true" />
</template>
