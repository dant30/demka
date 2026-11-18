"""Printing signals — auto-queue receipts after sales / returns."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="sales.Sale")
def queue_sale_receipt(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.status not in ("CONFIRMED", "PAID", "PARTIAL", "INVOICED"):
        return
    try:
        from .tasks import process_print_queue
        from .services import PrintService
        PrintService.queue_receipt(sale_id=instance.pk, user=instance.agent)
        process_print_queue.delay()
    except Exception:
        logger.exception("Failed to queue receipt for sale #%s", instance.pk)


@receiver(post_save, sender="sales.SalesReturn")
def queue_credit_note(sender, instance, **kwargs):
    if instance.status != "COMPLETED":
        return
    try:
        from .services import PrintService
        PrintService.queue_credit_note(sales_return_id=instance.pk, user=instance.created_by)
    except Exception:
        logger.exception("Failed to queue credit note for return #%s", instance.pk)