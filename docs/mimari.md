# Mimari Özet

```text
 Tarayıcı / Mobil uygulama
        │  HTTPS + JSON, Authorization: Bearer <JWT>
        ▼
 Vue 3 SPA (Vite, Pinia, Vue Router, Tailwind)          ──►  /api/*  ──►  Django 5 + DRF
                                                                           │
                         ┌─────────────────────────────────────────────────┤
                         ▼                                                 ▼
          content/ JSON (Pydantic ile doğrulanır,           PostgreSQL (Django ORM)
          belleğe alınır): müfredat, anlatım,               kullanıcı, profil, oturum, cevap,
          sorular, cevap anahtarı, OYSS                     yanılgı kaydı, puan, rozet, hedef
```

## Veri ayrımı

| Nerede | Ne | Neden |
| --- | --- | --- |
| `content/` JSON | Müfredat ağacı, konu anlatımları, etkileşimli grafik parametreleri, sorular **ve cevap anahtarları**, OYSS | Sürümlü, kodsuz düzenlenebilir, öğretmen incelemesine uygun |
| PostgreSQL | Kullanıcı/profil, çalışma oturumları, cevaplar (`QuestionAttempt`), kavram yanılgısı kayıtları (`MisconceptionLog`), konu ilerlemesi, puan defteri, rozet, görev, hedef | Kullanıcıya özel, kalıcı, sorgulanabilir |

İçerik `apps/curriculum/content_loader.py` ile ilk istekte yüklenir, şema ve dosyalar arası tutarlılık açısından denetlenir, sonra bellekte tutulur.

## Backend uygulamaları

| Uygulama | Sorumluluk | Sahibi |
| --- | --- | --- |
| `config/` | Ayarlar, URL'ler, ortak hata biçimi (`exceptions.py`), OpenAPI açıklamaları (`openapi.py`) | Admin 1 |
| `accounts` | Özel `User`, `StudentProfile`, JWT kayıt/giriş, profil, başlangıç seviye testi | Admin 1 |
| `curriculum` | İçerik yükleyici, `validate_content` komutu, müfredat/konu/OYSS API'si | Admin 2 |
| `questions` | Soru havuzu API'si; istemciye giden alanları kısıtlayan serializer | Admin 2 |
| `exams` | Soru çözümü ve süreli test motoru, cevap değerlendirme | Admin 2 |
| `study_sessions` | 60 sn heartbeat ile aktif çalışma süresi | Admin 3 |
| `analytics` | Panel özeti, konu ilerlemesi, kavram yanılgısı kayıtları, Gelişim Haritası, Hata Analizi | Admin 3 |
| `gamification` | Puan defteri, seviye, 7 rozet, görevler, kişisel hedefler | Admin 3 |

## Temel akış: soru çözümü → kavram yanılgısı → yönlendirme

```text
POST /api/exams/practice/start/          → sorular (cevap anahtarı YOK)
POST /api/exams/submit-answer/           → sunucu şıkkı içerikten kontrol eder
   ├─ QuestionAttempt kaydı (ilk deneme başarı oranını belirler)
   ├─ yanlışsa MisconceptionLog(misconception_tag, önerilen alt konu)
   ├─ oyunlaştırma motoru (puan/rozet, idempotent)
   └─ yanıt: doğru şık + adım adım çözüm + yanılgı açıklaması + "Konu özetine git" hedefi
GET  /api/analytics/error-analysis/      → yanılgı örüntüleri + düzeltilmemiş yanlışlar
POST /api/exams/practice/start/ {mistakes_only: true}  → Hata Avcısı: yalnızca açık yanlışlar
```

## Değişmez kurallar

- **Cevap anahtarı sunucudadır.** `questions/serializers.py` istemciye yalnızca izin verilen alanları açar. Doğru şık ve çözüm yalnızca cevap gönderildikten sonra döner (süreli testte test bittikten sonra). Hata Analizi ekranı da doğru şıkkı göstermez.
- **Puan, süre, rozet ve yanılgı hesapları backend'de yapılır.** İstemci yalnızca gösterir.
- **Süreli test:** Başlangıç ve bitiş zamanı (`deadline`) sunucuda tutulur. Süre dolduktan sonra gelen cevap reddedilir (`409 time_up`) ve test sunucuda kapatılır. Ağ gecikmesi için 5 sn pay vardır.
- **Heartbeat:** İstemci yalnızca kullanıcı etkileşimdeyken (veya süreli test ekranında) 60 sn'de bir ping atar. 120 sn'den uzun sessizlik süreye eklenmez.
- **İdempotency:** Puan kayıtları `PointLedger.idempotency_key` üzerinde benzersizdir ve `transaction.atomic()` içinde yazılır. Çift tıklama veya tekrarlanan istek mükerrer puan vermez.
- **IDOR koruması:** Tüm kullanıcı verisi sorguları `request.user` ile süzülür; başka öğrencinin oturum kimliği `404` döner.
- **Dürüst analiz:** Bir konuda 5'ten az (ilk deneme) cevap varsa düzey `insufficient` olur ve tanı gibi sunulmaz. Bir yanılgı en az 2 kez görülmeden "tekrarlayan örüntü" sayılmaz (`analytics/services.py` eşikleri).
- **Hata biçimi:** Tüm API hataları `{"detail", "code", "fields?"}` biçiminde, kullanıcı dostu Türkçe mesajla döner. 500 hatalarında teknik ayrıntı gizlenir.

## Frontend yapısı

| Klasör | İçerik |
| --- | --- |
| `services/api.js` | Axios istemcisi, JWT ekleme, süresi dolan token'ı tek seferde yenileme, Türkçe hata çevirisi |
| `stores/` | `auth`, `grade` (göz atılan sınıf), `content`, `exam`, `stats`, `rewards`, `theme` |
| `components/math/` | `KatexRenderer.vue` (LaTeX + hafif Markdown), `GeometryCanvas.vue` (JSXGraph, geç yüklenir) |
| `components/dashboard/` | `StatCard`, `MasteryMap`, `BadgeGrid`, `StudyTimer`, grafikler |
| `composables/useHeartbeat.js` | Etkileşim algılama ve 60 sn heartbeat |
| `views/` | `auth/`, `learning/`, `practice/`, `dashboard/` ekranları |

Responsive düzen: `lg` (1024 px) altında kenar çubuğu çekmeceye dönüşür. Sınıf seçici `md` altında çekmecenin içine taşınır.
Etkileşimli grafikler dokunma olaylarını yakalamaz, böylece mobilde sayfa tek parmakla kayar. Etkileşim büyük kaydırıcılarla yapılır.
