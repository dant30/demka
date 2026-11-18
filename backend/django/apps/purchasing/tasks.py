from celery import shared_task
from django.utils import timezone


@shared_task
def flag_overdue_pos() -> dict:
    """
    Periodic task: flag POs whose expected_date has passed and status is SENT/PARTIAL.
    Does not change status — just returns them for dashboard highlighting.
    """
    from .models import PurchaseOrder

    today = timezone.now().date()
    overdue = PurchaseOrder.objects.filter(
        status__in=[PurchaseOrder.Status.SENT, PurchaseOrder.Status.PARTIAL],
        expected_date__lt=today,
    ).values("id", "po_number", "supplier__name", "expected_date")
    return {"count": overdue.count(), "pos": list(overdue)}


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def send_po_notification_sms(self, po_id: int):
    """Notify the boss that a PO has been sent to the supplier."""
    from django.contrib.auth import get_user_model
    from core.services.sms import SmsError, SmsService
    from .models import PurchaseOrder

    User = get_user_model()
    try:
        po = PurchaseOrder.objects.select_related("supplier").get(pk=po_id)
    except PurchaseOrder.DoesNotExist:
        return

    boss_phones = list(
        User.objects.filter(role__in=("BOSS", "ADMIN"), is_active=True)
        .exclude(phone="")
        .values_list("phone", flat=True)
    )
    body = (
        f"PO {po.po_number} sent to {po.supplier.name} — "
        f"total KES {po.total}."
    )
    for phone in boss_phones:
        try:
            SmsService.send(phone, body)
        except SmsError:
            # Do not retry on individual SMS failures
            pass