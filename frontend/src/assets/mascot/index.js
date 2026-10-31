/**
 * OKTOPİ ahtapot maskotu — duygu durumu → görsel eşlemesi.
 *
 * Gerçek 3D maskot görselleri hazır olduğunda:
 *   1. Dosyaları bu klasöre koyun (ör. welcome.png, happy.png ...). Önerilen: şeffaf arka planlı,
 *      kare (en az 512x512) PNG veya WebP.
 *   2. Aşağıdaki ilgili satırı `new URL('./welcome.png', import.meta.url).href` biçiminde doldurun.
 * Değeri null olan durumlar için yerleşik SVG yer tutucu çizilir.
 */
export const MASCOT_IMAGES = {
  welcome: null, // Karşılama: el sallayan, gülümseyen
  happy: null, // Doğru cevap: mutlu
  celebrate: null, // Rozet / hedef kazanımı: kutlama
  thinking: null, // Düşünme / ipucu
  encourage: null, // Zorlanma / hata: teşvik edici, şefkatli
}

export const MASCOT_MOODS = Object.keys(MASCOT_IMAGES)
