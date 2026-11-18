from django.apps import AppConfig


class PurchasingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.purchasing"
    label = "purchasing"
    verbose_name = "Purchasing"

    def ready(self):
        from . import signals  # noqa: F401