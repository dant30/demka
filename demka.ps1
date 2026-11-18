<#
.SYNOPSIS
    Scaffolds the DEMKA Auto Spares & Motorbike Parts Sales system.
.DESCRIPTION
    Creates the full backend (Django + core), frontend, and root structure
    with sample contents. Run from anywhere:
        PS C:\Users\dante> .\demka.ps1
        PS C:\Users\dante> .\demka.ps1 -RootPath "D:\Projects\DEMKA"
#>
param(
    [string]$RootPath = (Join-Path $HOME "DEMKA")
)

$ErrorActionPreference = "Stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

# ============================================================
# Helpers
# ============================================================
function New-Folder {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Write-Text {
    param([string]$Path, [string]$Content = "")
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
    Write-Host "  [file] $Path" -ForegroundColor DarkCyan
}

function To-ClassName {
    param([string]$Name)
    ($Name -split '_' | ForEach-Object {
        if ($_.Length -gt 0) { $_.Substring(0,1).ToUpper() + $_.Substring(1) } else { "" }
    }) -join ''
}

function Get-ClassNames {
    param([string]$Content)
    $m = [regex]::Matches($Content, '(?m)^class\s+(\w+)')
    return @($m | ForEach-Object { $_.Groups[1].Value })
}

# ============================================================
# Root layout
# ============================================================
Write-Host "`n=== DEMKA scaffold: $RootPath ===" -ForegroundColor Green

$rootDirs = @(
    "ci_cd",
    "doc",
    "infrastructure/nginx",
    "infrastructure/scripts",
    "infrastructure/monitoring",
    "infrastructure/docker",
    "tests/e2e",
    "tests/integration",
    "tests/performance"
)
foreach ($d in $rootDirs) { New-Folder (Join-Path $RootPath $d) }

Write-Text (Join-Path $RootPath "README.md") @'
# DEMKA

Auto Spares & Motorbike Parts Sales System.

- `backend/`   – Django project + shared `core/` modules
- `frontend/`  – React (Vite) SPA, including public preorder portal
- `infrastructure/` – nginx, docker, monitoring, scripts
- `ci_cd/`     – pipeline definitions
- `doc/`       – architecture, ERD, API docs
- `tests/`     – e2e, integration, performance suites
'@

# ============================================================
# Backend / Core
# ============================================================
$backendDir = Join-Path $RootPath "backend"
$coreDir    = Join-Path $backendDir "core"
$djangoDir  = Join-Path $backendDir "django"

New-Folder $coreDir
Write-Text (Join-Path $coreDir "__init__.py") '"""DEMKA shared core package (framework-agnostic utilities)."""'

# --- core/authentication ---
New-Folder (Join-Path $coreDir "authentication")
Write-Text (Join-Path $coreDir "authentication/__init__.py") ""
Write-Text (Join-Path $coreDir "authentication/jwt.py") @'
"""JWT helpers built on top of djangorestframework-simplejwt."""
from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
'@
Write-Text (Join-Path $coreDir "authentication/otp.py") @'
"""Phone-based OTP for preorder portal and field customers."""
import secrets
from django.core.cache import cache

OTP_TTL_SECONDS = 300
OTP_LENGTH = 6


def generate_otp(phone: str) -> str:
    otp = "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))
    cache.set(f"otp:{phone}", otp, timeout=OTP_TTL_SECONDS)
    return otp


def verify_otp(phone: str, otp: str) -> bool:
    stored = cache.get(f"otp:{phone}")
    if stored and stored == otp:
        cache.delete(f"otp:{phone}")
        return True
    return False
'@
Write-Text (Join-Path $coreDir "authentication/passwords.py") @'
"""Password strength policies."""
import re

MIN_LENGTH = 8


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < MIN_LENGTH:
        return False, f"Password must be at least {MIN_LENGTH} characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain a digit."
    return True, ""
'@

# --- core/cache ---
New-Folder (Join-Path $coreDir "cache")
Write-Text (Join-Path $coreDir "cache/__init__.py") ""
Write-Text (Join-Path $coreDir "cache/decorators.py") @'
"""Caching decorators."""
from functools import wraps
from django.core.cache import cache


def cache_result(timeout: int = 300, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{key_prefix}:{func.__name__}:{args}:{sorted(kwargs.items())}"
            result = cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key, result, timeout=timeout)
            return result
        return wrapper
    return decorator
'@
Write-Text (Join-Path $coreDir "cache/keys.py") @'
"""Centralised cache key builders."""

def stock_level_key(product_id: int, location_id: int) -> str:
    return f"stock:{product_id}:{location_id}"

def customer_balance_key(customer_id: int) -> str:
    return f"customer:balance:{customer_id}"

def route_run_key(run_id: int) -> str:
    return f"route:run:{run_id}"
'@
Write-Text (Join-Path $coreDir "cache/utils.py") @'
"""Cache helpers."""
from django.core.cache import cache


def invalidate(prefix: str) -> None:
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern(f"{prefix}*")


def get_or_set(key, value, timeout: int = 300):
    v = cache.get(key)
    if v is None:
        cache.set(key, value, timeout=timeout)
        return value
    return v
'@

# --- core/exceptions ---
New-Folder (Join-Path $coreDir "exceptions")
Write-Text (Join-Path $coreDir "exceptions/__init__.py") ""
Write-Text (Join-Path $coreDir "exceptions/api.py") @'
"""DRF global exception handler."""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def demka_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return Response(
            {"success": False, "error": {"code": response.status_code, "message": response.data}},
            status=response.status_code,
        )
    return Response(
        {"success": False, "error": {"code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                                      "message": "Internal server error."}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
'@
Write-Text (Join-Path $coreDir "exceptions/domain.py") @'
"""Domain-level exceptions."""

class DomainError(Exception):
    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class InsufficientStockError(DomainError):
    def __init__(self, product_name: str, requested: int, available: int):
        super().__init__(
            f"Insufficient stock for '{product_name}'. Requested {requested}, available {available}.",
            code="insufficient_stock",
        )


class CreditLimitExceededError(DomainError):
    def __init__(self, customer_name: str):
        super().__init__(f"Credit limit exceeded for '{customer_name}'.", code="credit_limit_exceeded")
'@

# --- core/logging ---
New-Folder (Join-Path $coreDir "logging")
Write-Text (Join-Path $coreDir "logging/__init__.py") ""
Write-Text (Join-Path $coreDir "logging/config.py") @'
"""Reusable LOGGING dict; import into Django settings."""
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} | {levelname:8} | {name} | cid={correlation_id} | {message}",
            "style": "{",
        },
    },
    "filters": {"correlation_id": {"()": "core.logging.correlation.CorrelationIdFilter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["correlation_id"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps":   {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "core":   {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}
'@
Write-Text (Join-Path $coreDir "logging/correlation.py") @'
"""Thread-local correlation id + middleware + logging filter."""
import uuid
import threading
import logging

_local = threading.local()


def get_correlation_id() -> str:
    return getattr(_local, "correlation_id", "-")


def set_correlation_id(value: str | None = None) -> str:
    cid = value or str(uuid.uuid4())
    _local.correlation_id = cid
    return cid


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True


class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cid = request.META.get("HTTP_X_CORRELATION_ID") or set_correlation_id()
        set_correlation_id(cid)
        response = self.get_response(request)
        response["X-Correlation-ID"] = cid
        return response
'@

# --- core/permissions ---
New-Folder (Join-Path $coreDir "permissions")
Write-Text (Join-Path $coreDir "permissions/__init__.py") ""
Write-Text (Join-Path $coreDir "permissions/roles.py") @'
"""Role-based DRF permissions."""
from rest_framework.permissions import BasePermission


class IsBoss(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("BOSS", "ADMIN")


class IsSalesStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("SALES_HELPER", "BOSS", "ADMIN")


class IsFieldAgent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ("FIELD_AGENT", "BOSS", "ADMIN")


class IsOwnerOrBoss(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in ("BOSS", "ADMIN"):
            return True
        return getattr(obj, "created_by_id", None) == request.user.id
'@

# --- core/security ---
New-Folder (Join-Path $coreDir "security")
Write-Text (Join-Path $coreDir "security/__init__.py") ""
Write-Text (Join-Path $coreDir "security/signing.py") @'
"""HMAC payload signing (webhooks, M-Pesa callbacks, etc.)."""
import hmac
import hashlib
import base64
from django.conf import settings


def sign_payload(payload: bytes) -> str:
    key = settings.SECRET_KEY.encode()
    digest = hmac.new(key, payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode()


def verify_signature(payload: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign_payload(payload), signature)
'@

# --- core/services ---
New-Folder (Join-Path $coreDir "services")
Write-Text (Join-Path $coreDir "services/__init__.py") ""
Write-Text (Join-Path $coreDir "services/payment.py") @'
"""M-Pesa Daraja API wrapper (STK Push)."""
import base64
import requests
from datetime import datetime
from django.conf import settings


class MpesaService:
    @staticmethod
    def _base_url() -> str:
        return ("https://api.safaricom.co.ke"
                if settings.MPESA["ENVIRONMENT"] == "production"
                else "https://sandbox.safaricom.co.ke")

    @classmethod
    def get_access_token(cls) -> str:
        key, secret = settings.MPESA["CONSUMER_KEY"], settings.MPESA["CONSUMER_SECRET"]
        auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
        url = f"{cls._base_url()}/oauth/v1/generate?grant_type=client_credentials"
        r = requests.get(url, headers={"Authorization": f"Basic {auth}"}, timeout=15)
        r.raise_for_status()
        return r.json()["access_token"]

    @classmethod
    def stk_push(cls, phone: str, amount: float, account_ref: str) -> dict:
        token = cls.get_access_token()
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        shortcode = settings.MPESA["SHORTCODE"]
        password = base64.b64encode(f"{shortcode}{settings.MPESA['PASSKEY']}{ts}".encode()).decode()
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": ts,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone, "PartyB": shortcode, "PhoneNumber": phone,
            "CallBackURL": settings.MPESA["CALLBACK_URL"],
            "AccountReference": account_ref,
            "TransactionDesc": f"Payment {account_ref}",
        }
        url = f"{cls._base_url()}/mpesa/stkpush/v1/processrequest"
        r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        return r.json()
'@
Write-Text (Join-Path $coreDir "services/sms.py") @'
"""SMS dispatch wrapper (Africa's Talking)."""
import requests
from django.conf import settings


class SmsService:
    @staticmethod
    def send(phone: str, message: str) -> dict:
        provider = settings.SMS["PROVIDER"]
        if provider == "africastalking":
            return SmsService._africastalking(phone, message)
        raise ValueError(f"Unsupported SMS provider: {provider}")

    @staticmethod
    def _africastalking(phone: str, message: str) -> dict:
        url = "https://api.africastalking.com/version1/messaging"
        headers = {
            "apiKey": settings.SMS["API_KEY"],
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "username": settings.SMS["USERNAME"],
            "to": phone,
            "message": message,
            "from": settings.SMS.get("SENDER_ID", ""),
        }
        return requests.post(url, headers=headers, data=data, timeout=15).json()
'@

# --- core/storage ---
New-Folder (Join-Path $coreDir "storage")
Write-Text (Join-Path $coreDir "storage/__init__.py") ""
Write-Text (Join-Path $coreDir "storage/backends.py") @'
"""Private storage backend (not exposed via public URL)."""
from django.core.files.storage import FileSystemStorage


class PrivateStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", "media/private")
        kwargs.setdefault("base_url", None)
        super().__init__(*args, **kwargs)
'@
Write-Text (Join-Path $coreDir "storage/files.py") @'
"""File path helpers."""
import uuid
from pathlib import Path


def build_upload_path(prefix: str, original_filename: str) -> str:
    ext = Path(original_filename).suffix
    return f"{prefix}/{uuid.uuid4().hex}{ext}"
'@

# --- core/throttling ---
New-Folder (Join-Path $coreDir "throttling")
Write-Text (Join-Path $coreDir "throttling/__init__.py") ""
Write-Text (Join-Path $coreDir "throttling/rates.py") @'
"""Scoped throttles."""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = "login"


class OtpRateThrottle(AnonRateThrottle):
    scope = "otp"


class FieldSyncThrottle(UserRateThrottle):
    scope = "field_sync"
'@

# --- core/utils ---
New-Folder (Join-Path $coreDir "utils")
Write-Text (Join-Path $coreDir "utils/__init__.py") ""
Write-Text (Join-Path $coreDir "utils/validators.py") @'
"""Custom validators."""
import re
from django.core.exceptions import ValidationError

KE_PHONE_RE = re.compile(r"^(?:\+254|0)(7\d{8}|1\d{8})$")


def validate_kenyan_phone(value: str) -> None:
    if not KE_PHONE_RE.match(value):
        raise ValidationError(f"'{value}' is not a valid Kenyan phone number.")


def validate_kra_pin(value: str) -> None:
    if not re.match(r"^[A-Z]\d{9}[A-Z]$", value):
        raise ValidationError(f"'{value}' is not a valid KRA PIN.")
'@

# ============================================================
# Backend / Django / config
# ============================================================
New-Folder $djangoDir
New-Folder (Join-Path $djangoDir "config")
New-Folder (Join-Path $djangoDir "config/settings")
New-Folder (Join-Path $djangoDir "requirements")
New-Folder (Join-Path $djangoDir "staticfiles")
New-Folder (Join-Path $djangoDir "media")
New-Folder (Join-Path $djangoDir "logs")

Write-Text (Join-Path $djangoDir "manage.py") @'
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Activate your virtualenv first."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
'@

Write-Text (Join-Path $djangoDir "config/__init__.py") @'
from .celery import app as celery_app

__all__ = ("celery_app",)
'@
Write-Text (Join-Path $djangoDir "config/celery.py") @'
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("demka")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
'@
Write-Text (Join-Path $djangoDir "config/urls.py") @'
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/accounts/",   include("apps.accounts.urls.api")),
    path("api/customers/",  include("apps.customers.urls.api")),
    path("api/suppliers/",  include("apps.suppliers.urls.api")),
    path("api/inventory/",  include("apps.inventory.urls.api")),
    path("api/purchasing/", include("apps.purchasing.urls.api")),
    path("api/sales/",      include("apps.sales.urls.api")),
    path("api/routes/",     include("apps.routes.urls.api")),
    path("api/payments/",   include("apps.payments.urls.api")),
    path("api/expenses/",   include("apps.expenses.urls.api")),
    path("api/reporting/",  include("apps.reporting.urls.api")),
    path("api/etims/",      include("apps.etims.urls.api")),
    path("api/preorders/",  include("apps.preorders.urls.api")),
    path("api/printing/",   include("apps.printing.urls.api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'@
Write-Text (Join-Path $djangoDir "config/asgi.py") @'
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
application = get_asgi_application()
'@
Write-Text (Join-Path $djangoDir "config/wsgi.py") @'
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
application = get_wsgi_application()
'@

Write-Text (Join-Path $djangoDir "config/settings/__init__.py") ""
Write-Text (Join-Path $djangoDir "config/settings/base.py") @'
"""DEMKA base settings — shared across environments."""
import os
import sys
from pathlib import Path
from datetime import timedelta

import environ

# ---- Paths ----------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parent.parent.parent   # backend/django
BACKEND_DIR = BASE_DIR.parent                                  # backend/
PROJECT_DIR = BACKEND_DIR.parent                               # DEMKA/
sys.path.insert(0, str(BACKEND_DIR))  # so `core` is importable

# ---- Environment ---------------------------------------------
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BACKEND_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="unsafe-default-change-in-prod")
DEBUG      = env("DJANGO_DEBUG")
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
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# ---- Celery --------------------------------------------------
CELERY_BROKER_URL     = env("CELERY_BROKER_URL",     default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT   = ["json"]
CELERY_TASK_SERIALIZER  = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

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

SMS = {
    "PROVIDER":  env("SMS_PROVIDER",  default="africastalking"),
    "API_KEY":   env("SMS_API_KEY",   default=""),
    "USERNAME":  env("SMS_USERNAME",  default=""),
    "SENDER_ID": env("SMS_SENDER_ID", default="DEMKA"),
}
'@
Write-Text (Join-Path $djangoDir "config/settings/development.py") @'
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
'@
Write-Text (Join-Path $djangoDir "config/settings/production.py") @'
from .base import *  # noqa

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
'@

# ---- requirements ----
Write-Text (Join-Path $djangoDir "requirements/base.txt") @'
Django>=5.0,<5.1
djangorestframework>=3.15
djangorestframework-simplejwt>=5.3
django-cors-headers>=4.3
django-filter>=24.2
drf-spectacular>=0.27
django-environ>=0.11
django-celery-results>=2.5
psycopg[binary]>=3.1
celery>=5.3
redis>=5.0
requests>=2.31
Pillow>=10.2
'@
Write-Text (Join-Path $djangoDir "requirements/development.txt") @'
-r base.txt
django-debug-toolbar>=4.4
black>=24.3
isort>=5.13
flake8>=7.0
pytest>=8.1
pytest-django>=4.8
coverage>=7.4
'@
Write-Text (Join-Path $djangoDir "requirements/production.txt") @'
-r base.txt
gunicorn>=21.2
whitenoise>=6.6
'@

# ============================================================
# Backend / Django / apps
# ============================================================
$appsDir = Join-Path $djangoDir "apps"
New-Folder $appsDir
Write-Text (Join-Path $appsDir "__init__.py") '"""DEMKA Django apps package."""'

# -----------------------------------------------------------
# App definitions: name -> model files (filename -> content)
# -----------------------------------------------------------
$Apps = @(
    @{
        Name = "accounts"
        Models = @{
            "user" = @'
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN        = "ADMIN",        "Admin"
        BOSS         = "BOSS",         "Boss"
        SALES_HELPER = "SALES_HELPER", "Sales Helper"
        FIELD_AGENT  = "FIELD_AGENT",  "Field Agent"

    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SALES_HELPER)

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserLocationAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="location_assignments")
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50, null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
'@
        }
    },
    @{
        Name = "customers"
        Models = @{
            "customer" = @'
from django.db import models


class Customer(models.Model):
    class Type(models.TextChoices):
        RETAIL   = "RETAIL",   "Retail"
        RESELLER = "RESELLER", "Reseller"
        WALK_IN  = "WALK_IN",  "Walk-in"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    customer_type = models.CharField(max_length=20, choices=Type.choices, default=Type.RETAIL)
    business_name = models.CharField(max_length=200, blank=True)
    kra_pin = models.CharField(max_length=20, blank=True)
    physical_address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_terms_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class CustomerRouteAssignment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="route_assignments")
    route = models.ForeignKey("routes.Route", on_delete=models.CASCADE)
    assigned_from = models.DateField()
    assigned_to = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True)


class CustomerContact(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=50, blank=True)
'@
        }
    },
    @{
        Name = "suppliers"
        Models = @{
            "supplier" = @'
from django.db import models


class Supplier(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    kra_pin = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    payment_terms_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE)
    supplier_part_number = models.CharField(max_length=100, blank=True)
    last_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField(default=0)
'@
        }
    },
    @{
        Name = "inventory"
        Models = @{
            "product" = @'
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    applies_to = models.CharField(
        max_length=20,
        choices=[("MOTORBIKE", "Motorbike"), ("AUTO", "Auto"), ("BOTH", "Both")],
        default="BOTH",
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = "PIECE", "Piece"
        SET   = "SET",   "Set"
        PAIR  = "PAIR",  "Pair"
        LITRE = "LITRE", "Litre"

    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    product_type = models.CharField(
        max_length=20,
        choices=[("MOTORBIKE_PART", "Motorbike Part"),
                 ("AUTO_PART", "Auto Part"),
                 ("ACCESSORY", "Accessory")],
        default="AUTO_PART",
    )
    brand = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_stocked = models.BooleanField(default=True)
    reorder_level = models.PositiveIntegerField(default=0)
    reorder_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    compatibility_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"
'@
            "stock" = @'
from django.db import models


class StockLocation(models.Model):
    class Type(models.TextChoices):
        SHOP      = "SHOP",      "Shop"
        FIELD     = "FIELD",     "Field"
        WAREHOUSE = "WAREHOUSE", "Warehouse"

    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=Type.choices, default=Type.SHOP)
    assigned_agent = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class StockLevel(models.Model):
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE, related_name="levels")
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE, related_name="levels")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.PositiveIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "location")


class StockMovement(models.Model):
    class Type(models.TextChoices):
        SALE          = "SALE",          "Sale"
        PURCHASE      = "PURCHASE",      "Purchase"
        TRANSFER_IN   = "TRANSFER_IN",   "Transfer In"
        TRANSFER_OUT  = "TRANSFER_OUT",  "Transfer Out"
        ADJUSTMENT    = "ADJUSTMENT",    "Adjustment"
        RETURN        = "RETURN",        "Return"
        SPECIAL_ORDER = "SPECIAL_ORDER", "Special Order"

    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=Type.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)


class StockTransfer(models.Model):
    class Status(models.TextChoices):
        PENDING     = "PENDING",     "Pending"
        IN_TRANSIT  = "IN_TRANSIT",  "In Transit"
        RECEIVED    = "RECEIVED",    "Received"
        CANCELLED   = "CANCELLED",   "Cancelled"

    from_location = models.ForeignKey(StockLocation, on_delete=models.CASCADE, related_name="transfers_out")
    to_location   = models.ForeignKey(StockLocation, on_delete=models.CASCADE, related_name="transfers_in")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    initiated_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="transfers_initiated")
    received_by  = models.ForeignKey("accounts.User", null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name="transfers_received")
    created_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
'@
        }
    },
    @{
        Name = "purchasing"
        Models = @{
            "purchase_order" = @'
from django.db import models


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT     = "DRAFT",     "Draft"
        SENT      = "SENT",      "Sent"
        PARTIAL   = "PARTIAL",   "Partial"
        RECEIVED  = "RECEIVED",  "Received"
        CANCELLED = "CANCELLED", "Cancelled"

    po_number = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    expected_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class PurchaseOrderItem(models.Model):
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity_ordered = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
'@
            "grn" = @'
from django.db import models


class GoodsReceivedNote(models.Model):
    grn_number = models.CharField(max_length=30, unique=True)
    po = models.ForeignKey("purchasing.PurchaseOrder", null=True, blank=True, on_delete=models.SET_NULL)
    supplier = models.ForeignKey("suppliers.Supplier", on_delete=models.PROTECT)
    received_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    received_at = models.DateTimeField(auto_now_add=True)
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)


class GoodsReceivedItem(models.Model):
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name="items")
    po_item = models.ForeignKey("purchasing.PurchaseOrderItem", null=True, blank=True, on_delete=models.SET_NULL)
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
'@
        }
    },
    @{
        Name = "sales"
        Models = @{
            "sale" = @'
from django.db import models


class Sale(models.Model):
    class Channel(models.TextChoices):
        SHOP  = "SHOP",  "Shop"
        FIELD = "FIELD", "Field"

    class Status(models.TextChoices):
        DRAFT     = "DRAFT",     "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        INVOICED  = "INVOICED",  "Invoiced"
        PAID      = "PAID",      "Paid"
        PARTIAL   = "PARTIAL",   "Partial"
        CANCELLED = "CANCELLED", "Cancelled"
        RETURNED  = "RETURNED",  "Returned"

    sale_number = models.CharField(max_length=30, unique=True)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    sale_type = models.CharField(
        max_length=20,
        choices=[("STANDARD", "Standard"), ("SPECIAL_ORDER", "Special Order")],
        default="STANDARD",
    )
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="sales")
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)
    route = models.ForeignKey("routes.Route", null=True, blank=True, on_delete=models.SET_NULL)
    agent = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="sales_made")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_credit_sale = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    etims_invoice_number = models.CharField(max_length=50, blank=True)
    etims_status = models.CharField(
        max_length=20,
        choices=[("NA", "N/A"), ("PENDING", "Pending"), ("SENT", "Sent"), ("FAILED", "Failed")],
        default="NA",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
'@
            "special_order" = @'
from django.db import models


class SpecialOrder(models.Model):
    class Status(models.TextChoices):
        ORDERED   = "ORDERED",   "Ordered"
        ARRIVED   = "ARRIVED",   "Arrived"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    sale_item = models.OneToOneField("sales.SaleItem", on_delete=models.CASCADE, related_name="special_order")
    supplier = models.ForeignKey("suppliers.Supplier", null=True, blank=True, on_delete=models.SET_NULL)
    purchase_order_item = models.ForeignKey("purchasing.PurchaseOrderItem", null=True, blank=True, on_delete=models.SET_NULL)
    customer_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_arrival_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORDERED)
    notes = models.TextField(blank=True)
'@
            "sale_return" = @'
from django.db import models


class SalesReturn(models.Model):
    return_number = models.CharField(max_length=30, unique=True)
    original_sale = models.ForeignKey("sales.Sale", on_delete=models.PROTECT, related_name="returns")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT)
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_method = models.ForeignKey("payments.PaymentMethod", null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class SalesReturnItem(models.Model):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey("sales.SaleItem", on_delete=models.PROTECT)
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    restock = models.BooleanField(default=True)
    location = models.ForeignKey("inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL)
'@
        }
    },
    @{
        Name = "routes"
        Models = @{
            "route" = @'
from django.db import models


class Route(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    default_agent = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class RouteSchedule(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.PositiveSmallIntegerField()  # 0=Mon .. 6=Sun
    is_active = models.BooleanField(default=True)


class RouteRun(models.Model):
    class Status(models.TextChoices):
        PLANNED     = "PLANNED",     "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED   = "COMPLETED",   "Completed"
        CANCELLED   = "CANCELLED",   "Cancelled"

    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="runs")
    agent = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    stock_location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)
    run_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    opening_stock_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_stock_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)


class RouteChangeLog(models.Model):
    route = models.ForeignKey(Route, on_delete=models.PROTECT)
    change_type = models.CharField(max_length=30)
    affected_customers = models.JSONField(default=list, blank=True)
    previous_agent = models.ForeignKey("accounts.User", null=True, blank=True,
                                        on_delete=models.SET_NULL, related_name="route_changes_from")
    new_agent = models.ForeignKey("accounts.User", null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="route_changes_to")
    reason = models.TextField()
    changed_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="route_changes_made")
    changed_at = models.DateTimeField(auto_now_add=True)
'@
        }
    },
    @{
        Name = "payments"
        Models = @{
            "payment" = @'
from django.db import models


class PaymentMethod(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=50)
    requires_reference = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REVERSED  = "REVERSED",  "Reversed"

    payment_number = models.CharField(max_length=30, unique=True)
    sale = models.ForeignKey("sales.Sale", null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="payments")
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    received_at = models.DateTimeField(auto_now_add=True)
    location = models.ForeignKey("inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    mpesa_phone = models.CharField(max_length=20, blank=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)


class MpesaTransaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    account_reference = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateTimeField()
    raw_payload = models.JSONField(default=dict)
    matched_payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    reconciled = models.BooleanField(default=False)


class CustomerLedgerEntry(models.Model):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="ledger_entries")
    entry_type = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
'@
        }
    },
    @{
        Name = "expenses"
        Models = @{
            "expense" = @'
from django.db import models


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Expense(models.Model):
    expense_number = models.CharField(max_length=30, unique=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    expense_date = models.DateField()
    paid_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    payment_method = models.ForeignKey("payments.PaymentMethod", on_delete=models.PROTECT)
    reference = models.CharField(max_length=100, blank=True)
    receipt_image = models.ImageField(upload_to="receipts/", null=True, blank=True)
    location = models.ForeignKey("inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL)
    route_run = models.ForeignKey("routes.RouteRun", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
'@
        }
    },
    @{
        Name = "reporting"
        Models = @{}   # reports are view-based, no dedicated models
    },
    @{
        Name = "etims"
        Models = @{
            "etims" = @'
from django.db import models


class EtimsConfig(models.Model):
    environment = models.CharField(max_length=20, default="sandbox")
    device_serial = models.CharField(max_length=100)
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200)
    pin = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)


class EtimsInvoice(models.Model):
    sale = models.OneToOneField("sales.Sale", on_delete=models.CASCADE, related_name="etims_invoice")
    invoice_number = models.CharField(max_length=50)
    control_code = models.CharField(max_length=50, blank=True)
    qr_code_data = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("PENDING", "Pending"), ("SUBMITTED", "Submitted"),
                 ("FAILED", "Failed"), ("RETRY", "Retry")],
        default="PENDING",
    )
    response_payload = models.JSONField(default=dict, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
'@
        }
    },
    @{
        Name = "preorders"
        Models = @{
            "preorder" = @'
from django.db import models


class PreorderCustomerSession(models.Model):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=10)
    otp_expires_at = models.DateTimeField()
    session_token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Preorder(models.Model):
    class Status(models.TextChoices):
        SUBMITTED       = "SUBMITTED",       "Submitted"
        CONFIRMED       = "CONFIRMED",       "Confirmed"
        IN_PREPARATION  = "IN_PREPARATION",  "In Preparation"
        READY           = "READY",           "Ready"
        DELIVERED       = "DELIVERED",       "Delivered"
        CANCELLED       = "CANCELLED",       "Cancelled"

    preorder_number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="preorders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    total_estimated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    preferred_pickup_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)


class PreorderItem(models.Model):
    preorder = models.ForeignKey(Preorder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price_estimated = models.DecimalField(max_digits=12, decimal_places=2)
    available_in_stock = models.BooleanField(default=False)
'@
        }
    },
    @{
        Name = "printing"
        Models = @{
            "printer" = @'
from django.db import models


class Printer(models.Model):
    class Type(models.TextChoices):
        BLUETOOTH = "BLUETOOTH", "Bluetooth"
        USB       = "USB",       "USB"
        NETWORK   = "NETWORK",   "Network"

    name = models.CharField(max_length=100)
    printer_type = models.CharField(max_length=20, choices=Type.choices)
    identifier = models.CharField(max_length=100)
    assigned_location = models.ForeignKey("inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL)
    assigned_user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    paper_width_mm = models.PositiveIntegerField(default=58)
    is_active = models.BooleanField(default=True)


class PrintJob(models.Model):
    class Status(models.TextChoices):
        QUEUED  = "QUEUED",  "Queued"
        PRINTED = "PRINTED", "Printed"
        FAILED  = "FAILED",  "Failed"

    printer = models.ForeignKey(Printer, null=True, blank=True, on_delete=models.SET_NULL)
    document_type = models.CharField(max_length=30)
    reference_type = models.CharField(max_length=50)
    reference_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    payload = models.JSONField(default=dict)
    escpos_data = models.BinaryField(null=True, blank=True)
    created_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(null=True, blank=True)
'@
        }
    },
    @{
        Name = "common"
        Models = @{
            "base" = @'
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
'@
        }
    }
)

# -----------------------------------------------------------
# Generate each app
# -----------------------------------------------------------
$appFolders = @("models","serializers","services","views","views/api","urls","tests","migrations","management","management/commands")

foreach ($app in $Apps) {
    $name = $app.Name
    $classBase = To-ClassName $name
    $appPath = Join-Path $appsDir $name

    Write-Host "`n[app] $name" -ForegroundColor Yellow

    # ensure all folders
    New-Folder $appPath
    foreach ($f in $appFolders) { New-Folder (Join-Path $appPath $f) }

    # ---- __init__.py ----
    Write-Text (Join-Path $appPath "__init__.py") ""

    # ---- app boilerplate ----
    Write-Text (Join-Path $appPath "apps.py") @"
from django.apps import AppConfig


class ${classBase}Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.$name"
    label = "$name"
    verbose_name = "$classBase"
"@

    Write-Text (Join-Path $appPath "middleware.py") @"
# $name middleware — add custom middleware here if needed.
"@
    Write-Text (Join-Path $appPath "permissions.py") @"
# $name specific DRF permissions.
"@
    Write-Text (Join-Path $appPath "signals.py") @"
# $name signals — connect via apps.py ready().
"@
    Write-Text (Join-Path $appPath "tasks.py") @"
from celery import shared_task  # noqa: F401

# Celery tasks for $name go here.
"@

    Write-Text (Join-Path $appPath "views/__init__.py") ""
    Write-Text (Join-Path $appPath "views/admin_views.py") @"
from django.shortcuts import render  # noqa: F401

# Custom admin views for $name go here.
"@
    Write-Text (Join-Path $appPath "views/api/__init__.py") ""
    Write-Text (Join-Path $appPath "urls/__init__.py") ""
    Write-Text (Join-Path $appPath "urls/api.py") @"
from django.urls import path

urlpatterns = []
"@
    Write-Text (Join-Path $appPath "urls/admin.py") @"
from django.urls import path

urlpatterns = []
"@
    Write-Text (Join-Path $appPath "services/__init__.py") ""
    Write-Text (Join-Path $appPath "serializers/__init__.py") ""
    Write-Text (Join-Path $appPath "tests/__init__.py") ""
    Write-Text (Join-Path $appPath "migrations/__init__.py") ""
    Write-Text (Join-Path $appPath "management/__init__.py") ""
    Write-Text (Join-Path $appPath "management/commands/__init__.py") ""

    # ---- models ----
    $allClasses = @()
    $importLines = @()
    if ($app.Models -and $app.Models.Count -gt 0) {
        foreach ($fname in $app.Models.Keys) {
            Write-Text (Join-Path $appPath "models/$fname.py") $app.Models[$fname]
            $classes = Get-ClassNames $app.Models[$fname]
            if ($classes.Count -gt 0) {
                $allClasses += $classes
                $importLines += "from .$fname import " + ($classes -join ", ")
            }
        }
        Write-Text (Join-Path $appPath "models/__init__.py") (($importLines -join "`n") + "`n")
    } else {
        Write-Text (Join-Path $appPath "models/__init__.py") ""
    }

    # ---- admin.py ----
    if ($allClasses.Count -gt 0) {
        $reg = ($allClasses | ForEach-Object { "admin.site.register($_)" }) -join "`n"
        $adminContent = "from django.contrib import admin`nfrom .models import " + ($allClasses -join ", ") + "`n`n`n" + $reg + "`n"
        Write-Text (Join-Path $appPath "admin.py") $adminContent
    } else {
        Write-Text (Join-Path $appPath "admin.py") "from django.contrib import admin  # noqa: F401`n"
    }
}

# Empty marker files for tracked-but-empty dirs
Write-Text (Join-Path $djangoDir "staticfiles/.gitkeep") ""
Write-Text (Join-Path $djangoDir "media/.gitkeep") ""
Write-Text (Join-Path $djangoDir "logs/.gitkeep") ""

# Backend .env.example
Write-Text (Join-Path $backendDir ".env.example") @'
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=demka
POSTGRES_USER=demka
POSTGRES_PASSWORD=demka
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/2
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_PASSKEY=
MPESA_SHORTCODE=
MPESA_ENV=sandbox
MPESA_CALLBACK_URL=
ETIMS_ENV=sandbox
ETIMS_BASE_URL=
ETIMS_CLIENT_ID=
ETIMS_CLIENT_SECRET=
ETIMS_DEVICE_SERIAL=
ETIMS_PIN=
SMS_PROVIDER=africastalking
SMS_API_KEY=
SMS_USERNAME=
SMS_SENDER_ID=DEMKA
'@

# ============================================================
# Frontend (React + Vite)
# ============================================================
$frontendDir = Join-Path $RootPath "frontend"
$srcDir = Join-Path $frontendDir "src"
foreach ($d in @("public","src","src/api","src/assets","src/components","src/hooks",
                 "src/layouts","src/pages","src/routes","src/services","src/store",
                 "src/styles","src/utils")) {
    New-Folder (Join-Path $frontendDir $d)
}

Write-Text (Join-Path $frontendDir "package.json") @'
{
  "name": "demka-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint ."
  },
  "dependencies": {
    "axios": "^1.7.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.1",
    "vite": "^5.4.0"
  }
}
'@
Write-Text (Join-Path $frontendDir "vite.config.js") @'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://localhost:8000" } },
});
'@
Write-Text (Join-Path $frontendDir "index.html") @'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DEMKA</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'@
Write-Text (Join-Path $frontendDir ".env.example") "VITE_API_URL=http://localhost:8000/api`nVITE_PREORDER_URL=http://localhost:8000/api/preorders`n"
Write-Text (Join-Path $srcDir "main.jsx") @'
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
'@
Write-Text (Join-Path $srcDir "App.jsx") @'
import { Routes, Route } from "react-router-dom";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<div style={{ padding: 24 }}>DEMKA – bootstrapped.</div>} />
    </Routes>
  );
}
'@
Write-Text (Join-Path $srcDir "styles/index.css") @'
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
'@
Write-Text (Join-Path $srcDir "api/client.js") @'
import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
});

client.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("access_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

export default client;
'@

# ============================================================
# Root-level marker files
# ============================================================
foreach ($d in @("ci_cd","doc","infrastructure/nginx","infrastructure/scripts",
                 "infrastructure/monitoring","infrastructure/docker",
                 "tests/e2e","tests/integration","tests/performance")) {
    Write-Text (Join-Path $RootPath "$d/.gitkeep") ""
}

Write-Host "`n=== DEMKA scaffold complete ===" -ForegroundColor Green
Write-Host "Root: $RootPath" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  cd $djangoDir"
Write-Host "  python -m venv .venv; .\.venv\Scripts\Activate.ps1"
Write-Host "  pip install -r requirements/development.txt"
Write-Host "  Copy-Item ..\.env.example .env"
Write-Host "  python manage.py makemigrations; python manage.py migrate"
Write-Host "  python manage.py runserver"