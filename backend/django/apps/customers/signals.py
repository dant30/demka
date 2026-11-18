"""Customers signals — cache invalidation and post-create hooks."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.cache.invalidation import invalidate_customer

from .models import Customer


@receiver(post_save, sender=Customer)
def customer_post_save(sender, instance, created, **kwargs):
    invalidate_customer(instance.pk)
    if created:
        try:
            from .tasks import send_customer_welcome_sms
            send_customer_welcome_sms.delay(instance.pk)
        except Exception:
            pass