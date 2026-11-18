from django.apps import AppConfig


class PreordersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.preorders"
    label = "preorders"
    verbose_name = "Preorders"

    def ready(self):
        from . import signals  # noqa: F401