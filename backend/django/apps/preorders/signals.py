"""Preorder signals — notify customer on status change."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="preorders.Preorder")
def notify_customer_on_status_change(sender, instance, created, **kwargs):
    if created:
        return
    try:
        if instance.status == "CONFIRMED":
            from .tasks import send_confirmed_sms
            send_confirmed_sms.delay(instance.pk)
        elif instance.status == "READY":
            from .tasks import send_ready_sms
            send_ready_sms.delay(instance.pk)
    except Exception:
        logger.exception("Failed to queue preorder SMS for #%s", instance.pk)