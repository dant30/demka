from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_confirmed_sms(self, preorder_id: int) -> dict:
    from core.services.sms import SmsError, SmsService
    from .models import Preorder

    try:
        preorder = Preorder.objects.select_related("customer").get(pk=preorder_id)
    except Preorder.DoesNotExist:
        return {"sent": False}
    if not preorder.customer.phone:
        return {"sent": False}
    try:
        SmsService.send(
            preorder.customer.phone,
            f"DEMKA: Preorder {preorder.preorder_number} is confirmed. "
            f"Total est. KES {preorder.total_estimated}. We'll notify you when ready.",
        )
        return {"sent": True}
    except SmsError as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_ready_sms(self, preorder_id: int) -> dict:
    from core.services.sms import SmsError, SmsService
    from .models import Preorder

    try:
        preorder = Preorder.objects.select_related("customer").get(pk=preorder_id)
    except Preorder.DoesNotExist:
        return {"sent": False}
    if not preorder.customer.phone:
        return {"sent": False}
    try:
        SmsService.send(
            preorder.customer.phone,
            f"DEMKA: Preorder {preorder.preorder_number} is READY for pickup. "
            f"Please come collect at your earliest convenience.",
        )
        return {"sent": True}
    except SmsError as exc:
        raise self.retry(exc=exc)


@shared_task
def expire_stale_sessions() -> dict:
    """Purge sessions not used in the last 7 days. Run daily."""
    from datetime import timedelta
    from django.utils import timezone
    from .models import PreorderCustomerSession

    cutoff = timezone.now() - timedelta(days=7)
    deleted, _ = PreorderCustomerSession.objects.filter(
        is_active=False, last_activity_at__lt=cutoff,
    ).delete()
    return {"deleted": deleted}