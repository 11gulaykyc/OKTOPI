# API Kullanımı (Mobil ve Diğer İstemciler)

Canlı ve her zaman güncel referans: **`/api/docs/`** (Swagger). Makine okur şema: `/api/schema/` (OpenAPI 3).
Mobil uygulama için istemci kodu bu şemadan üretilebilir (ör. `openapi-generator`).

## Kimlik doğrulama

```http
POST /api/auth/login/
Content-Type: application/json

{ "username": "ayse", "password": "…" }        // kullanıcı adı veya e-posta
```

Yanıttaki `access` token her isteğe eklenir:

```http
Authorization: Bearer <access>
```

`access` süresi dolunca (`401`), `refresh` ile yenilenir. Her yenilemede yeni bir `refresh` da verilir, eskisini değiştirin:

```http
POST /api/auth/token/refresh/
{ "refresh": "<refresh>" }
```

Swagger'da sağ üstteki **Authorize** düğmesine `access` token'ı yapıştırarak korumalı uç noktaları deneyebilirsiniz.

## Hata biçimi

```json
{ "detail": "Bu konu seçilen sınıfta yok.", "code": "invalid", "fields": { "topic_id": ["Bu konu seçilen sınıfta yok."] } }
```

| HTTP | `code` örnekleri | İstemci ne yapmalı? |
| --- | --- | --- |
| 400 | `invalid` | `detail`'i göster; `fields` varsa ilgili form alanının altına yaz |
| 401 | `not_authenticated`, `token_not_valid` | Token'ı yenile, olmazsa giriş ekranına dön |
| 404 | `not_found` | Kayıt yok veya kullanıcıya ait değil |
| 409 | `conflict`, `time_up` | Oturum durumu değişmiş (ör. süre doldu); oturumu yeniden yükle |
| 5xx | — | Genel mesaj göster; ayrıntı sunucu kaydındadır |

## Önemli uç noktalar

| İşlem | Uç nokta |
| --- | --- |
| Kayıt / giriş / profil | `POST /api/auth/register/`, `POST /api/auth/login/`, `GET/PATCH /api/auth/me/` |
| Müfredat ve konu anlatımı | `GET /api/curriculum/grades/{grade}/`, `GET /api/curriculum/topics/{topic_id}/` |
| Soru çözümü | `POST /api/exams/practice/start/` → `POST /api/exams/submit-answer/` → `POST /api/exams/finish-exam/` |
| Süreli test | `POST /api/exams/timed/start/` → cevaplar → `POST /api/exams/finish-exam/` |
| Çalışma süresi | `POST /api/study-sessions/heartbeat/` (yalnızca kullanıcı aktifken, 60 sn'de bir) |
| Panel | `GET /api/analytics/dashboard-summary/` |
| Gelişim Haritası | `GET /api/analytics/mastery-map/?grade=9` |
| Hata Analizi | `GET /api/analytics/error-analysis/?grade=9` |
| Oyunlaştırma | `GET /api/gamification/summary/`, `PUT /api/gamification/goals/` |

## İstemci sorumlulukları

- Doğru cevabı, puanı veya süreyi **hesaplamayın**. Sunucunun döndürdüğünü gösterin.
- Süreli testte geri sayımı `deadline − server_now` farkıyla başlatın. Cihaz saatine güvenmeyin.
- Heartbeat'i uygulama arka plandayken göndermeyin. Sunucu zaten 120 sn'den uzun boşlukları saymaz, ama gereksiz istek pil tüketir.
- Gelişim Haritası'nda `level: "insufficient"` ve Hata Analizi'nde `enough_data: false` durumlarını kesin tanı gibi göstermeyin. "Daha fazla soru çözerek analizi netleştirebilirsin" gibi bir mesaj kullanın.
