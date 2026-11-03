"""
Django settings for CampusReserve.
Implements the backend for Sprint 1 + Sprint 2 user stories (HU1-HU8):
court search/status, reservation, shared-court constraint, cancellation,
and waiting list with automatic notification and expiration.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "accounts",
    "courts",
    "reservations",
    "waitlist",
    "ai",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "campusreserve.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "campusreserve.wsgi.application"

# ─── Database ──────────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── DRF / JWT ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# ─── CORS (React frontend) ─────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
).split(",")

# ─── Celery / Redis (waiting list expiration, HU8) ─────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# How long a student has to confirm a waiting-list offer before it expires
# and is offered to the next student in the queue (FR18 / HU8).
WAITLIST_CONFIRMATION_WINDOW_MINUTES = 10

# ─── Celery beat: periodic weather check (optional) ──────────────────────────
# Run `celery -A campusreserve beat` to enable it. Even without beat, alerts
# are generated when a student opens their notifications.
CELERY_BEAT_SCHEDULE = {
    "check-weather-alerts": {
        "task": "notifications.tasks.check_weather_alerts",
        "schedule": 60 * 60,  # every hour
    },
}

# ─── AI (recommendations + weather report) ────────────────────────────────────
# Any OpenAI-compatible chat API. Default: Google Gemini (free key at
# https://aistudio.google.com/apikey). Leave AI_API_KEY empty to use the
# rule-based fallback (everything still works, just without AI text).
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_BASE_URL = os.environ.get(
    "AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai"
)
AI_MODEL = os.environ.get("AI_MODEL", "gemini-2.5-flash")
AI_TIMEOUT_SECONDS = int(os.environ.get("AI_TIMEOUT_SECONDS", "20"))

# ─── Weather (Open-Meteo, free, no key) ───────────────────────────────────────
# Default coordinates: Universidad EAFIT, Medellín.
CAMPUS_LATITUDE = float(os.environ.get("CAMPUS_LATITUDE", "6.2006"))
CAMPUS_LONGITUDE = float(os.environ.get("CAMPUS_LONGITUDE", "-75.5783"))
# An hour counts as "bad weather" if rain probability >= this % ...
WEATHER_BAD_PROBABILITY = int(os.environ.get("WEATHER_BAD_PROBABILITY", "70"))
# ... or expected rain >= this many mm (storms and heavy rain always count).
WEATHER_BAD_PRECIPITATION_MM = float(os.environ.get("WEATHER_BAD_PRECIPITATION_MM", "2.0"))
