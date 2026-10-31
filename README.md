# OKTOPİ

9–12. sınıf öğrencileri için Türkiye Yüzyılı Maarif Modeli uyumlu, kavram yanılgısı analizli matematik öğrenme platformu.
Mimari, kurallar ve geliştirme fazları için [CLAUDE.md](CLAUDE.md) dosyasına bakın.

## Hızlı başlangıç (Windows, geliştirme)

Gereksinimler: Python 3.11+, Node 20+, PostgreSQL 15+.

```powershell
# 1) Ortam değişkenleri
Copy-Item .env.example .env   # DJANGO_SECRET_KEY ve POSTGRES_* değerlerini düzenleyin

# 2) Backend
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py validate_content
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000

# 3) Frontend (yeni terminal)
cd frontend
npm install
npm run dev
```

Uygulama: http://127.0.0.1:5173 · API: http://127.0.0.1:8000/api · Yönetim: http://127.0.0.1:8000/admin

## Testler

```powershell
cd backend
.\.venv\Scripts\python manage.py test apps
```
