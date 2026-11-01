# Kurulum (Geliştirme Ortamı)

## Gereksinimler

| Araç | Sürüm | Not |
| --- | --- | --- |
| Python | 3.11+ | Proje 3.12 ile test edildi |
| Node.js | 20+ | Vite 6 için |
| PostgreSQL | 15+ | Yerel veya Docker; veritabanı adı varsayılan olarak `oktopi` |
| Git | — | |

## 1. Depoyu al ve ortam dosyasını oluştur

```powershell
git clone <depo-adresi> oktopi
cd oktopi
Copy-Item .env.example .env      # macOS/Linux: cp .env.example .env
```

`.env` içinde en az `DJANGO_SECRET_KEY` ve `POSTGRES_*` değerlerini düzenleyin. Tüm değişkenler için: [ortam-degiskenleri.md](ortam-degiskenleri.md).

## 2. Veritabanı

```sql
CREATE DATABASE oktopi;
```

PostgreSQL bir Windows hizmeti olarak kurulmadıysa (taşınabilir kurulum), her oturumda elle başlatın:

```powershell
<pgsql-klasörü>\bin\pg_ctl.exe -D <pgsql-klasörü>\data -l <pgsql-klasörü>\postgres.log start
```

## 3. Backend (Django)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt     # macOS/Linux: .venv/bin/pip
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py validate_content   # content/ JSON dosyalarını doğrular
.\.venv\Scripts\python manage.py createsuperuser    # isteğe bağlı: /admin için
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000
```

> **Windows konsolunda Türkçe karakter hatası** (`UnicodeEncodeError: 'charmap'`) görürseniz komutlardan önce
> `$env:PYTHONUTF8 = "1"` çalıştırın.

## 4. Frontend (Vue 3 + Vite)

Yeni bir terminalde:

```powershell
cd frontend
npm install
npm run dev
```

Vite, `/api` isteklerini `http://127.0.0.1:8000` adresine aktarır (`frontend/vite.config.js`). Bu yüzden geliştirmede CORS ayarı gerekmez.

## 5. Adresler

| Adres | İçerik |
| --- | --- |
| http://127.0.0.1:5173 | Uygulama |
| http://127.0.0.1:8000/api/docs/ | Swagger API dokümantasyonu |
| http://127.0.0.1:8000/api/redoc/ | ReDoc görünümü |
| http://127.0.0.1:8000/admin/ | Django yönetim paneli |
| http://127.0.0.1:8000/api/health/ | Sağlık kontrolü |

## 6. Testler ve kontroller

```powershell
cd backend
.\.venv\Scripts\python manage.py test apps                          # tüm backend testleri (PostgreSQL gerekir)
.\.venv\Scripts\python manage.py test apps.exams.test_e2e            # içerik → test → hata analizi uçtan uca akışı
.\.venv\Scripts\python manage.py validate_content                    # içerik şeması
.\.venv\Scripts\python manage.py spectacular --validate --fail-on-warn --file openapi.yaml   # API şeması

cd ..\frontend
npm run build                                                        # derleme hatası kontrolü
```

Testler sırasında Django geçici bir `test_oktopi` veritabanı oluşturur. Bu nedenle veritabanı kullanıcısının `CREATEDB` yetkisi olmalıdır.

## Sık karşılaşılan sorunlar

| Belirti | Çözüm |
| --- | --- |
| `connection refused` / `could not connect to server` | PostgreSQL çalışmıyor; başlatın ve `POSTGRES_HOST/PORT` değerlerini kontrol edin. |
| `RuntimeError: DJANGO_SECRET_KEY ...` | `.env` yok veya `DJANGO_DEBUG=False` iken anahtar boş. |
| Sayfada "Sunucuya ulaşılamadı" | Backend çalışmıyor ya da 8000 dışında bir portta. |
| `İçerik doğrulaması ... hata ile başarısız` | Bir JSON dosyası şemaya uymuyor; mesajdaki dosya ve alan yolunu düzeltin ([icerik-ekleme.md](icerik-ekleme.md)). |
| İçerik değişikliği görünmüyor | İçerik ilk istekte belleğe alınır; `runserver` sürecini yeniden başlatın. |
