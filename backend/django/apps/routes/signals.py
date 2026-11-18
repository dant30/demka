"""Routes signals — cache invalidation for route-run keys."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.cache.invalidation import invalidate_route_run

from .models import RouteRun


@receiver([post_save, post_delete], sender=RouteRun)
def route_run_changed(sender, instance, **kwargs):
    invalidate_route_run(instance.pk)