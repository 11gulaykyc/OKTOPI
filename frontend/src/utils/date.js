function isoDate(d) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** Tarih seçici için min/max (yalnızca kullanıcıya kolaylık; asıl denetim sunucudadır). */
export function birthDateLimits(range) {
  if (!range) return { min: undefined, max: undefined }
  const today = new Date()
  const max = new Date(today.getFullYear() - range.min, today.getMonth(), today.getDate())
  const min = new Date(today.getFullYear() - range.max - 1, today.getMonth(), today.getDate() + 1)
  return { min: isoDate(min), max: isoDate(max) }
}

export function formatLongDate(value) {
  if (!value) return ''
  return new Date(`${value}T00:00:00`).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })
}
