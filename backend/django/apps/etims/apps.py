from django.apps import AppConfig


class EtimsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.etims"
    label = "etims"
    verbose_name = "KRA eTIMS"

    def ready(self):
        from . import signals  # noqa: F401