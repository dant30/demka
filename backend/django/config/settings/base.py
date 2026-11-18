"""DEMKA base settings â€” shared across environments."""
import os
import sys
from pathlib import Path
from datetime import timedelta

import environ
from celery.schedules import crontab

# ---- Paths ----------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parent.parent.parent   # backend/django
BACKEND_DIR = BASE_DIR.parent                                  # backend/
PROJECT_DIR = BACKEND_DIR.parent                               # DEMKA/
sys.path.insert(0, str(BACKEND_DIR))  # so `core` is importable

# ---- Environment ---------------------------------------------
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BACKEND_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-default-change-in-prod")
DEBUG = env("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---- Apps -----------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_celery_results",
    "rest_framework_simplejwt.token_blacklist",
]
LOCAL_APPS = [
    "apps.accounts",
    "apps.customers",
    "apps.suppliers",
    "apps.inventory",
    "apps.purchasing",
    "apps.sales",
    "apps.routes",
    "apps.payments",
    "apps.expenses",
    "apps.reporting",
    "apps.etims",
    "apps.preorders",
    "apps.printing",
    "apps.common",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---- Middleware ----------------------------------------------
MIDDLEWARE = [
    "core.logging.correlation.CorrelationIdMiddleware",
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
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# ---- Database (Postgres) -------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     env("POSTGRES_DB",       default="demka"),
        "USER":     env("POSTGRES_USER",     default="demka"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="demka"),
        "HOST":     env("POSTGRES_HOST",     default="localhost"),
        "PORT":     env("POSTGRES_PORT",     default="5432"),
    }
}

# ---- Auth ----------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---- I18N / TZ ----------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

# ---- Static / media -----------------------------------------
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL   = "/media/"
MEDIA_ROOT  = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- DRF -----------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/hour", "user": "1000/hour"},
    "EXCEPTION_HANDLER": "core.exceptions.api.demka_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "BLACKLIST_AFTER_ROTATION": True,
    "ROTATE_REFRESH_TOKENS": True,
}

# ---- Celery --------------------------------------------------
CELERY_BROKER_URL     = env("CELERY_BROKER_URL",     default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT   = ["json"]
CELERY_TASK_SERIALIZER  = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    "daily-reorder-check": {
        "task": "apps.inventory.tasks.check_reorder_levels_task",
        "schedule": 60 * 60 * 24,
    },
    "monthly-expense-digest": {
        "task": "apps.expenses.tasks.send_monthly_expense_digest",
        "schedule": crontab(hour=8, minute=0, day_of_month=1),
    },
    "weekly-missing-receipts": {
        "task": "apps.expenses.tasks.flag_expenses_missing_receipts",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
    "materialize-runs-nightly": {
        "task": "apps.routes.tasks.materialize_upcoming_runs",
        "schedule": crontab(hour=5, minute=0),
        "kwargs": {"days_ahead": 3},
    },
    "variance-sweep-daily": {
        "task": "apps.routes.tasks.flag_cash_variances",
        "schedule": crontab(hour=20, minute=0),
    },
    "run-digest-morning": {
        "task": "apps.routes.tasks.send_daily_run_digest",
        "schedule": crontab(hour=6, minute=30),
    },
    "etims-outbox-every-2-min": {
        "task": "apps.etims.tasks.process_etims_outbox",
        "schedule": crontab(minute="*/2"),
    },
    "etims-code-sync-daily": {
        "task": "apps.etims.tasks.sync_etims_codes",
        "schedule": crontab(hour=3, minute=0),
    },
    "expire-preorder-sessions": {
        "task": "apps.preorders.tasks.expire_stale_sessions",
        "schedule": crontab(hour=2, minute=0),
    },
    "print-queue-tick": {
        "task": "apps.printing.tasks.process_print_queue",
        "schedule": 30.0,
    },
    "cleanup-old-print-jobs": {
        "task": "apps.printing.tasks.cleanup_old_print_jobs",
        "schedule": crontab(hour=3, minute=30),
    },
    "warm-dashboard": {
        "task": "apps.reporting.tasks.warm_dashboard_cache",
        "schedule": crontab(minute="*/5", hour="7-20"),
    },
    "warm-monthly-pnl": {
        "task": "apps.reporting.tasks.warm_monthly_cache",
        "schedule": crontab(minute=0, hour=1),
    },
}

# ---- Cache ---------------------------------------------------
CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": env("REDIS_URL", default="redis://localhost:6379/2"),
}}

# ---- Logging -------------------------------------------------
from core.logging.config import LOGGING  # noqa: E402,F401

SPECTACULAR_SETTINGS = {
    "TITLE": "DEMKA API",
    "DESCRIPTION": "Auto Spares & Motorbike Parts Sales System",
    "VERSION": "1.0.0",
}

# ---- Integration configs ------------------------------------
ETIMS = {
    "ENVIRONMENT":   env("ETIMS_ENV",           default="sandbox"),
    "BASE_URL":      env("ETIMS_BASE_URL",      default=""),
    "CLIENT_ID":     env("ETIMS_CLIENT_ID",     default=""),
    "CLIENT_SECRET": env("ETIMS_CLIENT_SECRET", default=""),
    "DEVICE_SERIAL": env("ETIMS_DEVICE_SERIAL", default=""),
    "PIN":           env("ETIMS_PIN",           default=""),
}

MPESA = {
    "CONSUMER_KEY":    env("MPESA_CONSUMER_KEY",    default=""),
    "CONSUMER_SECRET": env("MPESA_CONSUMER_SECRET", default=""),
    "PASSKEY":         env("MPESA_PASSKEY",         default=""),
    "SHORTCODE":       env("MPESA_SHORTCODE",       default=""),
    "ENVIRONMENT":     env("MPESA_ENV",             default="sandbox"),
    "CALLBACK_URL":    env("MPESA_CALLBACK_URL",    default=""),
}

SMS_ENABLED = env.bool("SMS_ENABLED", default=False)
SMS_PROVIDER = env("SMS_PROVIDER", default="ots")
SMS_API_BASE_URL = env("SMS_API_BASE_URL", default="https://sms.ots.co.ke/api/v3/")
SMS_API_SEND_PATH = env("SMS_API_SEND_PATH", default="sms/send")
SMS_API_TOKEN = env("SMS_API_TOKEN", default="")
SMS_SENDER_ID = env("SMS_SENDER_ID", default="")
SMS_API_TIMEOUT_SECONDS = env.int("SMS_API_TIMEOUT_SECONDS", default=10)

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@demka.local")

if DEBUG:
    SMS_PROVIDER = env("SMS_PROVIDER", default="console")

REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"] = "core.utils.pagination.StandardPagination"
REST_FRAMEWORK["PAGE_SIZE"] = 25
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update({
    "login": "10/min",
    "otp": "5/min",
    "portal_otp_request": "20/hour",
    "portal_otp_verify": "30/hour",
    "print_queue": "500/hour",
    "preorder": "30/hour",
    "reports": "100/hour",
    "field_sync": "2000/hour",
})