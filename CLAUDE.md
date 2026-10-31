# OKTOPİ — TÜBİTAK 9–12. Sınıf Matematik Öğrenme Platformu (`CLAUDE.md`)

Bu dosya, **Claude Code** için temel mimari hafıza, kodlama standartları ve **3 Geliştiricili (Admin 1, Admin 2, Admin 3)** paralel geliştirme kılavuzudur. Claude Code, herhangi bir göreve başlamadan önce bu dosyadaki kuralları ve sorumluluk sınırlarını dikkate almak zorundadır.

---

## 1. Proje Özeti ve Kesin Kurallar
* **Amaç:** 9, 10, 11 ve 12. sınıf öğrencileri için *Türkiye Yüzyılı Maarif Modeli* uyumlu, kavram yanılgısı (`misconception_tag`) analizli, etkileşimli ve oyunlaştırılmış matematik öğrenme platformu.
* **Sıfır Sahte Veri (No Mock Data in Prod Flow):** Sadece görsel demo üretme. Tüm kullanıcı akışları gerçek PostgreSQL veritabanına bağlanmalı, istatistikler ve test sonuçları sunucu tarafında (Django) gerçek kayıtlardan hesaplanmalıdır.
* **Sunucu Taraflı Doğrulama:** Doğru cevap anahtarları sınav/soru çözümü bitmeden istemciye (Vue.js) gönderilmemelidir. Puan, süre, rozet ve kavram yanılgısı hesaplamaları yalnızca Django backend üzerinde yapılmalıdır.
* **Veri Ayrımı:** Müfredat, konu anlatımları, çözümler ve soru havuzu versiyonlu `JSON` dosyalarında tutulur. Kullanıcılar, profiller, oturumlar, test sonuçları, çalışma süreleri ve rozetler `PostgreSQL` veritabanında tutulur.

---

## 2. Teknoloji Yığını (Tech Stack)
| Katman | Teknoloji / Kütüphane | Temel Sorumluluk |
| :--- | :--- | :--- |
| **Frontend** | Vue.js 3 (Composition API, `<script setup>`) + Vite + Pinia + Vue Router | Kullanıcı arayüzü, durum yönetimi, yönlendirme ve responsive tasarım |
| **Stil / UI** | Tailwind CSS (Dark/Light Mode destekli) + Lucide Icons | Ana renk: Mavi (`#1E40AF` / `#2563EB`), yardımcı: Turkuaz, Açık Mavi, Mor/Bordo vurgular |
| **Backend & API** | Python 3.11+ & Django 5.x + Django REST Framework (DRF) + SimpleJWT | İş kuralları, JWT kimlik doğrulama, içerik servisleri, analiz ve oyunlaştırma motoru |
| **Veritabanı** | PostgreSQL + Django ORM | Kalıcı kullanıcı, test, çalışma oturumu ve analiz verileri |
| **Şema Doğrulama** | Pydantic (Backend JSON okuma) | `content/` altındaki JSON dosyalarının tip ve şema doğrulaması |
| **Matematik & Grafik** | **KaTeX** (LaTeX render) + **JSXGraph** (veya GeoGebra/Desmos Embed API) | Matematiksel formüllerin hızlı gösterimi ve parametreleri değiştirilebilir etkileşimli geometri |

---

## 3. Klasör Yapısı ve 3 Admin İçin Sorumluluk Sınırları (Git Çakışmasını Önleme)

Üç geliştirici aynı anda Claude Code çalıştıracağı için **her admin yalnızca kendi sorumluluk alanındaki klasörlerde** değişiklik yapmalıdır. Ortak dosyalarda (`settings.py`, `router/index.js`) yapılacak değişiklikler faz başlarında senkronize edilir.

```text
oktopi/
├── CLAUDE.md                        # Proje hafıza ve faz yönetim dosyası
├── .env.example                     # Ortam değişkenleri şablonu
├── backend/
│   ├── config/                      # Django ana ayarları (settings, urls, wsgi) [Admin 1]
│   ├── apps/
│   │   ├── accounts/                # User, Profile, JWT Auth, Sınıf/Okul seçimi [Admin 1]
│   │   ├── curriculum/              # JSON Şema doğrulayıcı, Konu/OYSS okuyucu API [Admin 2]
│   │   ├── questions/               # Soru havuzu okuyucu ve filtreleme servisi [Admin 2]
│   │   ├── exams/                   # Soru çözümü, Süreli test, Cevap/Yanılgı değerlendirme [Admin 2]
│   │   ├── study_sessions/          # Heartbeat (60sn) aktif çalışma süresi sayacı [Admin 3]
│   │   ├── analytics/               # İstatistikler, Gelişim Haritası, MisconceptionLog [Admin 3]
│   │   └── gamification/            # Puan (Ledger), Seviye, Rozetler, Görevler ve Hedefler [Admin 3]
│   └── manage.py
├── content/                         # Koddan bağımsız eğitim içerikleri [Admin 2]
│   ├── schemas/                     # Pydantic / JSON Schema tanımları
│   ├── curriculum/                  # grade-9/, grade-10/, grade-11/, grade-12/ ve oyss/
│   ├── questions/                   # misconception_tag içeren soru JSON dosyaları
│   └── explanations/                # Adım adım çözüm JSON dosyaları
├── frontend/
│   ├── src/
│   │   ├── assets/mascot/           # 3D Ahtapot maskotu görselleri ve durum ifadeleri [Admin 1]
│   │   ├── components/
│   │   │   ├── layout/              # Navbar, Sidebar, ThemeToggle, MascotToast [Admin 1]
│   │   │   ├── math/                # KatexRenderer.vue, GeometryCanvas.vue (JSXGraph) [Admin 2]
│   │   │   └── dashboard/           # StatCard, MasteryMap, BadgeGrid, StudyTimer [Admin 3]
│   │   ├── stores/                  # auth.js [Admin 1], content.js & exam.js [Admin 2], stats.js [Admin 3]
│   │   ├── views/
│   │   │   ├── auth/                # HomeView, LoginView, RegisterView, ProfileView [Admin 1]
│   │   │   ├── learning/            # TopicListView, TopicDetailView, OyssView [Admin 2]
│   │   │   ├── practice/            # QuestionPracticeView, TimedExamView, ExamResultView [Admin 2]
│   │   │   └── dashboard/           # StudentDashboardView, ErrorAnalysisView, GoalsView [Admin 3]
│   │   ├── router/
│   │   └── services/api.js          # Axios JWT interceptor istemcisi [Admin 1]
└── docs/                            # API sözleşmeleri ve kurulum belgeleri
```

### Geliştirici Rol Dağılımı Özeti
* **ADMİN 1 (Altyapı, Auth, Kullanıcı & UI/Tasarım Sistemi):** Proje iskeleti, PostgreSQL bağlantısı, JWT Kimlik Doğrulama, Kayıt/Giriş/Profil, Ana Sayfa, Tailwind Tema (Dark/Light), 3D Ahtapot Maskotu bileşenleri ve genel Layout.
* **ADMİN 2 (Eğitim İçerik Motoru, Test Sistemi, KaTeX & Geometri):** JSON şema doğrulama (Pydantic), 9–12. sınıf konu/soru JSON dosyaları, OYSS modülü, KaTeX matematik bileşeni, JSXGraph etkileşimli geometri aracı, Soru Çözümü ve Süreli Test motoru.
* **ADMİN 3 (Analitik, Kavram Yanılgısı Motoru, Heartbeat Sayaç & Oyunlaştırma):** 60 saniyelik Heartbeat çalışma süresi sayacı, Öğrenci Paneli (Dashboard), Kavram Yanılgısı (`misconception_tag`) analizi ve Gelişim Haritası, Puan/Seviye/Rozet/Görev oyunlaştırma sistemi.

---

## 4. Kritik Veri Modelleri ve Teknik Kurallar

### 4.1. Kavram Yanılgısı (`misconception_tag`) JSON Soru Şeması
`content/questions/` altındaki her soru JSON objesi aşağıdaki yapıyı zorunlu olarak desteklemelidir:
```json
{
  "id": "q-9-exp-001",
  "version": "1.0",
  "grade": 9,
  "topic": "Üslü İfadeler ve Denklemler",
  "subtopic": "Negatif Kuvvet",
  "learning_outcome": "MAT.9.1.2",
  "difficulty": "medium",
  "question_text": "$-2^{-3}$ ifadesinin değeri kaçtır?",
  "options": [
    {
      "key": "A",
      "text": "$-8$",
      "is_correct": false,
      "misconception_tag": "MISC_EXP_NEG_POWER_AS_MULTIPLICATION",
      "misconception_detail": "Üslü sayılarda negatif kuvveti çarpmaya dönüştürme veya kuvveti tabanla çarpma yanılgısı.",
      "recommended_subtopic_id": "top-9-exp-neg"
    },
    {
      "key": "B",
      "text": "$\\frac{1}{8}$",
      "is_correct": false,
      "misconception_tag": "MISC_EXP_NEG_SIGN_CONFUSION",
      "misconception_detail": "Negatif kuvvetin sayının işaretini pozitif yaptığı yanılgısı veya parantezsiz kuvvet kuralını gözden kaçırma.",
      "recommended_subtopic_id": "top-9-exp-sign"
    },
    {
      "key": "C",
      "text": "$-\\frac{1}{8}$",
      "is_correct": true,
      "misconception_tag": null,
      "misconception_detail": null,
      "recommended_subtopic_id": null
    }
  ],
  "step_by_step_solution": "1. Parantez olmadığı için eksi işareti kuvvetten etkilenmez...\n2. $2^{-3} = \\frac{1}{2^3} = \\frac{1}{8}$...\n3. Sonuç $-\\frac{1}{8}$ olur."
}
```
* **Kural:** Öğrenci yanlış şıkkı seçtiğinde, backend sadece `is_correct: false` dönmez; seçilen şıkkın `misconception_tag` değerini `MisconceptionLog` tablosuna yazar ve öğrenciyi `recommended_subtopic_id` konu özetine yönlendirir.

### 4.2. Çalışma Süresi (Heartbeat) Kuralı
* Sekme arka planda unutulduğunda sahte çalışma süresi yazılmasını önlemek için: Frontend yalnızca kullanıcı aktifken (fare/klavye etkileşimi veya aktif test ekranı) her **60 saniyede bir** `/api/study-sessions/heartbeat/` uç noktasına ping atar. Son ping'den sonra 2 dakikadan fazla süre geçmişse oturum süresi dondurulur.

### 4.3. Oyunlaştırma Güvenliği (Idempotency)
* Puan ve rozet kazanımları `transaction.atomic()` içinde çalışmalıdır. Aynı testin veya görevin çift tıklama / tekrarlı API isteği ile mükerrer puan kazandırması `UniqueConstraint` veya `idempotency_key` ile engellenmelidir.

---

## 5. AŞAMALI GELİŞTİRME PLANI (FAZLAR VE CLAUDE KOMUTLARI)

Geliştirme **4 Fazda** tamamlanacaktır. Her fazda 3 Admin kendi bilgisayarında Claude Code'a aşağıdaki ilgili promptu verecektir. **Faz 1'de önce Admin 1 temel iskeleti kurup Git'e pushlamalı, ardından Admin 2 ve Admin 3 pull yaparak kendi görevlerine başlamalıdır.**

---

### FAZ 1: Proje İskeleti, Kimlik Doğrulama, JSON Motoru ve Temel Veri Modelleri

#### 👤 Faz 1 — Admin 1 Komutu (Altyapı, Auth & Tasarım İskeleti)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 1** rolündesin. Faz 1 görevlerini uygula:
> 1. `backend/` (Django 5 + DRF + SimpleJWT + PostgreSQL) ve `frontend/` (Vue 3 + Vite + Pinia + Vue Router + Tailwind CSS) klasör iskeletini kur. `.env.example` dosyasını oluştur.
> 2. `backend/apps/accounts/` uygulamasını oluştur. Özel `User` ve `StudentProfile` modellerini yaz (Alanlar: kullanıcı adı, e-posta, yaş grubu, okul türü [Anadolu Lisesi / Fen Lisesi], sınıf düzeyi [9, 10, 11, 12], başlangıç seviye durumu).
> 3. Kayıt, Giriş (JWT), Profil Görüntüleme ve Sınıf/Profil Güncelleme API uç noktalarını (`/api/auth/...`) ve birim testlerini yaz.
> 4. Frontend tarafında Mavi/Turkuaz renk paletini, Dark/Light mode desteğini, `Navbar`, `Sidebar`, 3D Ahtapot Maskotu geri bildirim bileşenini (`MascotBanner.vue`) ve Ana Sayfa, Giriş, Kayıt, Profil ekranlarını (`views/auth/`) oluşturup backend ile entegre et."

#### 👤 Faz 1 — Admin 2 Komutu (JSON Şema Doğrulayıcı & Örnek Müfredat)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 2** rolündesin. Faz 1 görevlerini uygula:
> 1. `content/schemas/` altında Pydantic kullanarak Konu Anlatımı (`TopicSchema`), Soru (`QuestionSchema` - `misconception_tag` zorunlu kurallarıyla) ve OYSS (`OyssSchema`) doğrulama şemalarını yaz.
> 2. `content/curriculum/` altında 9, 10, 11 ve 12. sınıflar için Türkiye Yüzyılı Maarif Modeli uyumlu konu ağacını ve 9. sınıf için tam kapsamlı örnek konu anlatımı + `content/questions/` altında `misconception_tag` içeren en az 15 örnek matematik/geometri sorusunu JSON olarak oluştur.
> 3. `backend/apps/curriculum/` ve `backend/apps/questions/` uygulamalarını kur. JSON dosyalarını doğrulayan `validate_content` Django management komutunu yaz. Hatalı JSON varsa açık hata fırlatsın.
> 4. Sınıf ve konuya göre içerikleri ve soruları (doğru cevap anahtarını gizleyerek!) sunan salt-okunur API uç noktalarını (`/api/curriculum/...`, `/api/questions/...`) ve testlerini yaz."

#### 👤 Faz 1 — Admin 3 Komutu (Analitik, Sayaç ve Oyunlaştırma Modelleri)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 3** rolündesin. Faz 1 görevlerini uygula:
> 1. `backend/apps/study_sessions/`, `backend/apps/analytics/` ve `backend/apps/gamification/` uygulamalarını ve PostgreSQL modellerini oluştur.
> 2. Modelleri eksiksiz tanımla: `StudySession` (başlangıç, son heartbeat zamanı, toplam aktif saniye), `TopicProgress` (konu tamamlama ve başarı oranı), `MisconceptionLog` (kullanıcı, soru_id, misconception_tag, alt_konu_id, tarih), `PointLedger` (puan hareketleri, idempotency_key), `Badge`, `UserBadge`, `DailyTask`, `PersonalGoal`.
> 3. 60 saniyelik Heartbeat çalışma süresi API'sini (`/api/study-sessions/heartbeat/`) yaz: Arka planda 2 dakikadan uzun süre hareketsiz kalan oturumlara fazladan süre eklenmesin.
> 4. Bu modellerin migration dosyalarını ve Heartbeat hesaplama birim testlerini oluşturup çalıştır."

---

### FAZ 2: Konu Anlatımı, KaTeX, OYSS ve Öğrenci Paneli (Dashboard)

#### 👤 Faz 2 — Admin 1 Komutu (Sınıf Geçiş Sistemi, Navigasyon & Maskot Durumları)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 1** rolündesin. Faz 2 görevlerini uygula:
> 1. Öğrencinin kendi sınıfını varsayılan görmesini ancak üst bardaki 'Sınıf Seçici' (9, 10, 11, 12. Sınıf) ile kısıtlama olmadan diğer sınıfların içeriklerine geçiş yapabilmesini sağlayan global Pinia state (`useAuthStore` / `useGradeStore`) yapısını kur.
> 2. Ahtapot maskotunun bağlama göre değişen durum bileşenini (`MascotFeedback.vue`) geliştir: Karşılama, Doğru Cevap, Rozet Kazanımı ve Zorlanma/Hata durumlarında teşvik edici ('Harikasın böyle devam!', 'Bu kavramı birlikte tekrar inceleyelim') mesajlar göstersin.
> 3. Tüm sayfalar için mobil ve masaüstü tam uyumlu (responsive) AppLayout yapısını ve korumalı rota (Navigation Guard) kurallarını tamamla."

#### 👤 Faz 2 — Admin 2 Komutu (Konu Anlatımı, KaTeX Render ve OYSS Ekranları)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 2** rolündesin. Faz 2 görevlerini uygula:
> 1. Frontend'de `components/math/KatexRenderer.vue` bileşenini oluştur. Metin içindeki satır içi (`$...$`) ve blok (`$$...$$`) LaTeX ifadelerini KaTeX ile hatasız render etsin.
> 2. `TopicListView.vue` ve `TopicDetailView.vue` ekranlarını geliştir: Öğrenme hedefleri, akran diliyle samimi konu anlatımı, formüller, adım adım çözümlü örnekler, konu sonu pekiştirme soruları, son kalınan yeri hatırlama ve 'Tamamlandı Olarak İşaretle' butonu bulunsun.
> 3. OYSS (Ortak Yazılı Sınav Sistemi) bilgilendirme, sınav takvimi ve yazılıya hazırlık ekranını (`OyssView.vue`) oluştur."

#### 👤 Faz 2 — Admin 3 Komutu (Öğrenci Paneli / Dashboard & Çalışma Sayacı UI)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 3** rolündesin. Faz 2 görevlerini uygula:
> 1. Backend'de Öğrenci Paneli özet verilerini tek seferde veya modüler sunan `/api/analytics/dashboard-summary/` uç noktasını yaz (gerçek veritabanı kayıtlarından: toplam çalışma süresi, günlük/haftalık istatistik, çözülen soru, doğru/yanlış/boş, konu başarı oranları, güncel puan/seviye).
> 2. Frontend'de aktif çalışma süresini takip eden ve her 60 saniyede bir aktif etkileşim varsa backend'e heartbeat gönderen `StudyTimer.vue` bileşenini ve composable (`useHeartbeat.js`) yapısını kur.
> 3. `StudentDashboardView.vue` ekranını bilgi yoğunluğu dengeli, modern kartlarla (hızlı erişim, istatistik grafik kartları, son çalışmalar, aktif görevler) oluştur."

---

### FAZ 3: Soru Çözümü, Süreli Test Motoru, Kavram Yanılgısı ve Oyunlaştırma

#### 👤 Faz 3 — Admin 1 Komutu (API Güvenliği, Yetkilendirme ve Başlangıç Seviye Soruları)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 1** rolündesin. Faz 3 görevlerini uygula:
> 1. Kayıt sonrasındaki 'Eğitim seviyesini belirleyici kısa başlangıç soruları' (Onboarding Diagnostic) akışını tamamla ve sonucunu öğrenci profiline işle.
> 2. Tüm backend uç noktalarında yetkilendirme (permission) denetimi yap: Hiçbir öğrenci başka bir öğrencinin test oturumuna, istatistiğine veya profiline erişemesin (IDOR koruması). Bunun için entegrasyon testleri yaz.
> 3. API hata yakalama standartlarını (kullanıcı dostu Türkçe hata mesajları, teknik detayların gizlenmesi) frontend ve backend genelinde birleştir."

#### 👤 Faz 3 — Admin 2 Komutu (Soru Çözümü ve Süreli Test Motoru)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 2** rolündesin. Faz 3 görevlerini uygula:
> 1. `backend/apps/exams/` altında Soru Çözümü (`PracticeSession`) ve Süreli Test (`TimedExamSession`) motorunu kodla.
> 2. Süreli testte başlangıç ve bitiş zamanını sunucu tarafında doğrula; süre dolduğunda testi otomatik tamamla.
> 3. Cevap değerlendirme API'sini (`/api/exams/submit-answer/` ve `/api/exams/finish-exam/`) yaz: Cevabı sunucuda kontrol et, yanlışsa seçilen şıkkın `misconception_tag` bilgisini Admin 3'ün `MisconceptionLog` servisine kaydet, doğru cevabı ve adım adım çözümü dön.
> 4. Frontend'de `QuestionPracticeView.vue`, `TimedExamView.vue` (geri sayım sayaçlı) ve `ExamResultView.vue` (doğru/yanlış/boş, kavram yanılgısı uyarısı ve konu özetine yönlendirme butonu) ekranlarını geliştir."

#### 👤 Faz 3 — Admin 3 Komutu (Oyunlaştırma Motoru: Puan, Seviye, Rozet ve Görevler)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 3** rolündesin. Faz 3 görevlerini uygula:
> 1. `backend/apps/gamification/` altında gerçek eylemlere bağlı puan ve rozet motorunu (`transaction.atomic` ve mükerrer ödül korumalı) kodla.
> 2. Şu 7 rozetin kazanım kurallarını sunucu tarafında tanımla: *İlk Adım*, *Meraklı Zihin*, *İstikrarlı Öğrenci*, *Hata Avcısı* (daha önce yanlış yapılan soruyu doğru çözme), *Hız Ustası*, *Matematik Kaşifi*, *Hedef Tamamlandı*.
> 3. Günlük/haftalık görev ilerleme motorunu ve öğrencinin kendi günlük soru/süre hedefini geçmiş verileri bozmadan güncelleyebildiği `GoalsView.vue` ekranını oluştur."

---

### FAZ 4: Etkileşimli Geometri, Gelişim Haritası, Hata Analizi ve Uçtan Uca Testler

#### 👤 Faz 4 — Admin 1 Komutu (Mobil Uyumluluk, Dokümantasyon ve Genel Entegrasyon)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 1** rolündesin. Faz 4 görevlerini uygula:
> 1. Tüm ekranların (Konu anlatımı, Süreli test, Geometri tuvali, Öğrenci paneli) mobil ve masaüstü ekranlarda (responsive) sorunsuz çalıştığını doğrula ve taşmaları düzelt.
> 2. Gelecekte geliştirilecek mobil uygulamanın aynı backend'i kullanabilmesi için OpenAPI / Swagger (`drf-spectacular`) dokümantasyonunu `/api/docs/` altında aktif et.
> 3. `docs/` klasöründe kurulum, `.env` yapılandırması, içerik ekleme kılavuzu ve mimari özet belgelerini oluştur."

#### 👤 Faz 4 — Admin 2 Komutu (Etkileşimli Geometri & Fonksiyon Grafikleri)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 2** rolündesin. Faz 4 görevlerini uygula:
> 1. `components/math/GeometryCanvas.vue` bileşenini **JSXGraph** (veya Mafs/GeoGebra API) kullanarak geliştir.
> 2. Konu JSON dosyalarındaki görselleştirme parametrelerini okuyarak öğrencinin doğru eğimi, parabol katsayıları ($a, b, c$) veya üçgen açılarını kaydırıcılarla (sliders) değiştirip grafik üzerindeki değişimi anlık gözlemleyebileceği etkileşimli modülü konu anlatım sayfalarına bağla.
> 3. Dokunmatik (mobil) ekranlarda grafik etkileşiminin akıcı çalışmasını sağla ve içerik/test akışının uçtan uca testlerini çalıştır."

#### 👤 Faz 4 — Admin 3 Komutu (Gelişim Haritası ve Kavram Yanılgısı Analiz Ekranı)
> **Claude Code'a verilecek komut:**
> "`CLAUDE.md` dosyasını oku. Sen **Admin 3** rolündesin. Faz 4 görevlerini uygula:
> 1. `ErrorAnalysisView.vue` ve `MasteryMap.vue` (Gelişim Haritası) bileşenlerini geliştir.
> 2. Gelişim Haritasında öğrencinin konulara göre ilerlemesini, tekrar çalışması gereken alanları ve `MisconceptionLog` tablosunda biriken kavram yanılgısı örüntülerini göster. (Kural: Yeterli soru verisi yoksa kesin tanı gibi sunma, 'Bu alanda daha fazla soru çözerek analizi netleştirebilirsin' şeklinde dürüst geri bildirim ver).
> 3. Hata Analizi ekranından öğrencinin yanlış yaptığı sorulara ('Hata Avcısı' modunda tekrar çözmek üzere) ve ilgili konu özetlerine doğrudan yönlendirme bağlantılarını kur. Tüm analitik ve oyunlaştırma testlerini çalıştır."