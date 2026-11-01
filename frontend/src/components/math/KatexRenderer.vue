<script setup>
import { computed } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

/**
 * Metin içindeki LaTeX ifadelerini KaTeX ile çizer.
 *   $...$   → satır içi       $$...$$ → blok (ortalanmış)
 * Metnin geri kalanı için hafif Markdown desteklenir: paragraflar, **kalın**, *italik*,
 * "- " ile madde listesi ve "1. " ile numaralı liste. HTML her zaman kaçışlanır.
 *
 * Kullanım:
 *   <KatexRenderer text="$a^{-n} = \frac{1}{a^n}$ demektir." />
 *   <KatexRenderer latex="a^0 = 1" display />      (yalnızca formül)
 *   <KatexRenderer :text="option.text" inline />   (paragraf sarmalayıcısı olmadan)
 */
const props = defineProps({
  text: { type: String, default: '' },
  latex: { type: String, default: '' },
  display: { type: Boolean, default: false },
  inline: { type: Boolean, default: false },
})

function renderMath(expression, displayMode) {
  // throwOnError:false → hatalı LaTeX sayfayı bozmaz, ifade kırmızı kaynak metin olarak görünür.
  return katex.renderToString(expression.trim(), { displayMode, throwOnError: false, strict: 'ignore', output: 'html' })
}

function escapeHtml(value) {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

function inlineMarkdown(value) {
  return value.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/(^|[^*])\*([^*\s][^*]*?)\*/g, '$1<em>$2</em>')
}

// Matematik parçaları önce yer tutucuya alınır ki Markdown/HTML kaçışı LaTeX'i bozmasın.
const MATH_PATTERN = /\$\$([\s\S]+?)\$\$|\$((?:\\\$|[^$\n])+?)\$/g
const PLACEHOLDER = /\u0000(\d+)\u0000/g

function renderText(source, inlineOnly) {
  const pieces = []
  const masked = source.replace(MATH_PATTERN, (_, block, inline) => {
    pieces.push(block !== undefined ? { expr: block, display: true } : { expr: inline, display: false })
    return `\u0000${pieces.length - 1}\u0000`
  })

  const restore = (html) => html.replace(PLACEHOLDER, (_, i) => renderMath(pieces[i].expr, pieces[i].display))
  const line = (value) => inlineMarkdown(escapeHtml(value))

  if (inlineOnly) return restore(masked.split('\n').map(line).join('<br>'))

  const blocks = masked.split(/\n{2,}/).map((b) => b.trim()).filter(Boolean)
  const html = blocks.map((block) => {
    const lines = block.split('\n')
    if (lines.every((l) => /^\s*[-*]\s+/.test(l))) {
      return `<ul>${lines.map((l) => `<li>${line(l.replace(/^\s*[-*]\s+/, ''))}</li>`).join('')}</ul>`
    }
    if (lines.every((l) => /^\s*\d+[.)]\s+/.test(l))) {
      return `<ol>${lines.map((l) => `<li>${line(l.replace(/^\s*\d+[.)]\s+/, ''))}</li>`).join('')}</ol>`
    }
    // Tek başına duran blok formül paragraf içine konmaz.
    const only = block.match(/^\u0000(\d+)\u0000$/)
    if (only && pieces[only[1]].display) return `<div class="katex-block">${block}</div>`
    return `<p>${lines.map(line).join('<br>')}</p>`
  })
  return restore(html.join(''))
}

const html = computed(() => {
  if (props.latex) return renderMath(props.latex, props.display)
  return renderText(props.text || '', props.inline)
})
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html — içerik kaçışlanmış metin + KaTeX çıktısıdır -->
  <span v-if="inline || (latex && !display)" class="katex-renderer" v-html="html" />
  <div v-else class="katex-renderer katex-renderer--block" v-html="html" />
</template>

<style scoped>
.katex-renderer--block :deep(p) {
  margin: 0 0 0.75rem;
}
.katex-renderer--block :deep(p:last-child),
.katex-renderer--block :deep(ul:last-child),
.katex-renderer--block :deep(ol:last-child) {
  margin-bottom: 0;
}
.katex-renderer--block :deep(ul),
.katex-renderer--block :deep(ol) {
  margin: 0 0 0.75rem;
  padding-left: 1.25rem;
}
.katex-renderer--block :deep(ul) {
  list-style: disc;
}
.katex-renderer--block :deep(ol) {
  list-style: decimal;
}
.katex-renderer--block :deep(li + li) {
  margin-top: 0.25rem;
}
.katex-renderer :deep(strong) {
  font-weight: 800;
}
/* Uzun blok formüller dar ekranda sayfayı taşırmaz, kendi içinde kayar. */
.katex-renderer :deep(.katex-display) {
  margin: 0.75rem 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.25rem 0;
}
.katex-renderer :deep(.katex) {
  font-size: 1.08em;
}
</style>
