"""Payments signals — cache invalidation on payment mutations."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.cache.invalidation import invalidate_customer

from .models import Payment


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, **kwargs):
    if instance.customer_id:
        invalidate_customer(instance.customer_id)