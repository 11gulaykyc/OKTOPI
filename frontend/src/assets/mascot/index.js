/**
 * OKTOPİ maskot ailesi — her bölümün kendi rehber ahtapotu vardır.
 *
 *   navigator → Kaptan Pusula   : öğrenme yolculuğu (ana sayfa, panel, sınıf/konu anlatımı)
 *   tenebris  → Dr. Tenebris    : soru çözümü, süreli test, sonuçlar ve hata analizi
 *   nori      → Arşivci Nori    : OYSS hazırlık, hedefler ve profil
 *
 * Hangi maskotun görüneceği rotanın `meta.mascot` alanından okunur (bkz. router/index.js);
 * bileşenlere `character` prop'u verilerek elle de seçilebilir.
 * Duygu durumları (mood) ayrı görsel yerine animasyon + küçük durum balonu ile gösterilir.
 */
export const MASCOTS = {
  navigator: {
    key: 'navigator',
    name: 'Kaptan Pusula',
    title: 'Okyanus Haritacısı',
    intro: 'Rotanı birlikte çizelim; hangi konudan başlayacağını ben gösteririm.',
    image: new URL('./navigator.webp', import.meta.url).href,
  },
  tenebris: {
    key: 'tenebris',
    name: 'Dr. Tenebris',
    title: 'Derinlik Bilgini',
    intro: 'Her yanlış cevabın altında bir ipucu yatar; onu birlikte bulacağız.',
    image: new URL('./tenebris.webp', import.meta.url).href,
  },
  nori: {
    key: 'nori',
    name: 'Arşivci Nori',
    title: 'Deniz Tarihçisi',
    intro: 'Öğrendiklerini arşivliyor, sınavlara ve hedeflerine hazırlıyorum.',
    image: new URL('./nori.webp', import.meta.url).href,
  },
}

export const DEFAULT_MASCOT = 'navigator'
export const MASCOT_KEYS = Object.keys(MASCOTS)
export const MASCOT_MOODS = ['welcome', 'happy', 'celebrate', 'thinking', 'encourage']

export const getMascot = (key) => MASCOTS[key] ?? MASCOTS[DEFAULT_MASCOT]
