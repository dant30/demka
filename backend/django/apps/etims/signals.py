"""eTIMS signals — auto-queue submissions on state change."""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="sales.SalesReturn")
def queue_credit_note(sender, instance, **kwargs):
    if instance.status != "COMPLETED":
        return
    if instance.etims_invoices.filter(receipt_type="R", status="SUBMITTED").exists():
        return
    try:
        from .tasks import process_etims_outbox
        from .services import ETIMSService
        ETIMSService.submit_credit_note(instance.pk)
    except Exception as exc:
        logger.warning("Credit note submission queued but failed immediately: %s", exc)
        try:
            process_etims_outbox.delay()
        except Exception:
            pass