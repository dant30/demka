from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SMS_PROVIDER = "console"
CACHES = {
	"default": {
		"BACKEND": "django.core.cache.backends.locmem.LocMemCache",
		"LOCATION": "demka-development",
	},
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_STORE_EAGER_RESULT = False