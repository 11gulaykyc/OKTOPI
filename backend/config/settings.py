"""OKTOPİ Django ayarları.

Tüm gizli/ortama bağlı değerler kök dizindeki `.env` dosyasından okunur
(`.env.example` şablonuna bakınız).
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent

load_dotenv(REPO_DIR / ".env")

# content/schemas Pydantic modellerinin `content.schemas` olarak içe aktarılabilmesi için.
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
DEBUG = env_bool("DJANGO_DEBUG", False)
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("DJANGO_SECRET_KEY ortam değişkeni tanımlanmalıdır.")
    SECRET_KEY = "dev-only-insecure-key"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Üçüncü parti
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    # OKTOPİ uygulamaları
    "apps.accounts",
    "apps.curriculum",
    "apps.questions",
    "apps.exams",
    "apps.study_sessions",
    "apps.analytics",
    "apps.gamification",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "oktopi"),
        "USER": os.getenv("POSTGRES_USER", "postgres"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "OPTIONS": {"connect_timeout": 5},
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.accounts.validators.UppercasePasswordValidator"},
]

LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST Framework / JWT ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # Tüm hatalar tek biçimde döner: {"detail": "Türkçe mesaj", "code": "...", "fields": {...}}
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# --- OpenAPI / Swagger (/api/docs/) ---
# Mobil uygulama da aynı API'yi kullanacağı için şema varsayılan olarak yayındadır;
# API_DOCS_ENABLED=False ile kapatılabilir.
API_DOCS_ENABLED = env_bool("API_DOCS_ENABLED", True)
SPECTACULAR_SETTINGS = {
    "TITLE": "OKTOPİ API",
    "DESCRIPTION": (
        "9–12. sınıf matematik öğrenme platformunun REST API'si.\n\n"
        "**Kimlik doğrulama:** `POST /api/auth/login/` ile alınan `access` token'ı "
        "`Authorization: Bearer <token>` başlığıyla gönderin (Swagger'da sağ üstteki *Authorize*). "
        "Süresi dolan token `POST /api/auth/token/refresh/` ile yenilenir.\n\n"
        "**Hata biçimi:** Tüm hatalar `{\"detail\": \"Türkçe mesaj\", \"code\": \"...\", \"fields\": {...}}` biçimindedir.\n\n"
        "**Güvenlik kuralı:** Doğru cevap anahtarı ve çözümler yalnızca cevap gönderildikten "
        "(süreli testte test bittikten) sonra döner."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SCHEMA_PATH_PREFIX": r"/api/",
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "auth", "description": "Kayıt, JWT giriş, profil ve başlangıç seviye testi"},
        {"name": "curriculum", "description": "Müfredat ağacı, konu anlatımları, OYSS (herkese açık)"},
        {"name": "questions", "description": "Soru havuzu (cevap anahtarı gizli) ve pekiştirme kontrolü"},
        {"name": "exams", "description": "Soru çözümü ve süreli test motoru"},
        {"name": "study-sessions", "description": "60 sn heartbeat ile aktif çalışma süresi"},
        {"name": "analytics", "description": "Panel, Gelişim Haritası, Hata Analizi, konu ilerlemesi"},
        {"name": "gamification", "description": "Puan, seviye, rozet, görev ve hedefler"},
    ],
    "SWAGGER_UI_SETTINGS": {"persistAuthorization": True, "displayRequestDuration": True, "docExpansion": "none"},
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "UPDATE_LAST_LOGIN": True,
}

# --- CORS (Vite geliştirme sunucusu) ---
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

# --- OKTOPİ içerik & çalışma süresi ayarları ---
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", REPO_DIR / "content"))

# Heartbeat: istemci 60 sn'de bir ping atar; 120 sn'den uzun sessizlik oturumu dondurur.
HEARTBEAT_INTERVAL_SECONDS = 60
HEARTBEAT_IDLE_TIMEOUT_SECONDS = 120
