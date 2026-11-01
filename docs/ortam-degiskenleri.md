# Ortam Değişkenleri (`.env`)

Tüm değerler kök dizindeki `.env` dosyasından okunur. Şablon `.env.example` dosyasındadır. `.env` dosyası **git'e eklenmez**.
Backend `backend/config/settings.py`, frontend ise `frontend/vite.config.js` (`envDir: '..'`) üzerinden aynı dosyayı kullanır.

## Django

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | — (zorunlu) | Uzun ve rastgele bir anahtar. `DJANGO_DEBUG=True` iken boş bırakılırsa yalnızca geliştirme amaçlı güvensiz bir anahtar kullanılır. |
| `DJANGO_DEBUG` | `False` | Geliştirmede `True`. Sunucuda **mutlaka** `False`. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Virgülle ayrılmış alan adları (ör. `api.oktopi.example`). |

Anahtar üretmek için:

```powershell
.\backend\.venv\Scripts\python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

## PostgreSQL

| Değişken | Varsayılan |
| --- | --- |
| `POSTGRES_DB` | `oktopi` |
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | (boş) |
| `POSTGRES_HOST` | `127.0.0.1` |
| `POSTGRES_PORT` | `5432` |

## Kimlik doğrulama (SimpleJWT)

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `JWT_ACCESS_MINUTES` | `30` | Erişim (access) token ömrü, dakika |
| `JWT_REFRESH_DAYS` | `7` | Yenileme (refresh) token ömrü, gün. Her yenilemede yeni refresh token verilir. |

## API dokümantasyonu

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `API_DOCS_ENABLED` | `True` | `/api/docs/` (Swagger), `/api/redoc/` ve `/api/schema/` adreslerini açar. Mobil ekip şemaya erişemeyecekse `False` yapın. |

## CORS

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | API'yi tarayıcıdan çağıran istemcilerin adresleri. Geliştirmede Vite proxy kullanıldığı için gerekmez. Ayrı alan adındaki web istemcisi için gereklidir. |

Mobil uygulamalar tarayıcı olmadığı için CORS'tan etkilenmez.

## İçerik

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `CONTENT_DIR` | `<depo>/content` | Konu, soru ve OYSS JSON dosyalarının bulunduğu klasör. |

## Frontend (Vite)

| Değişken | Varsayılan | Açıklama |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` | API'nin tam adresi (ör. `https://api.oktopi.example/api`). Boşsa aynı alan adındaki `/api` kullanılır. Bu değer derleme (`npm run build`) sırasında pakete gömülür. |

## Sunucu (production) kontrol listesi

- [ ] `DJANGO_DEBUG=False`
- [ ] Güçlü, depoda bulunmayan `DJANGO_SECRET_KEY`
- [ ] `DJANGO_ALLOWED_HOSTS` gerçek alan adlarını içeriyor
- [ ] `CORS_ALLOWED_ORIGINS` yalnızca gerçek web istemcisinin adresini içeriyor
- [ ] `python manage.py migrate` ve `python manage.py validate_content` hatasız çalıştı
- [ ] `python manage.py collectstatic` (yönetim paneli statik dosyaları için; Swagger arayüzü CDN'den yüklenir)
