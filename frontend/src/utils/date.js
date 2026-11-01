function isoDate(d) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** Tarih seçici için min/max (yaş sınırı yok; yalnızca gelecek tarih ve çok eski yıllar engellenir). */
export function birthDateLimits(minYear) {
  return { min: minYear ? `${minYear}-01-01` : undefined, max: isoDate(new Date()) }
}

export function formatLongDate(value) {
  if (!value) return ''
  return new Date(`${value}T00:00:00`).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })
}
