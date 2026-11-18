from celery import shared_task

from core.services.sms import SmsError, SmsService

from .services.reorder_service import ReorderService


@shared_task
def check_reorder_levels_task() -> dict:
    """
    Periodic task: scan low stock levels and notify the boss via SMS.
    Wire in Celery beat to run daily, e.g. '0 7 * * *'.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    lows = list(ReorderService.low_stock_levels())

    if not lows:
        return {"count": 0}

    boss_phones = list(
        User.objects.filter(role__in=("BOSS", "ADMIN"), is_active=True)
        .exclude(phone__isnull=True)
        .exclude(phone="")
        .values_list("phone", flat=True)
    )

    if not boss_phones:
        return {"count": len(lows), "notified": 0}

    summary = (
        f"DEMKA stock alert: {len(lows)} item(s) at or below reorder level. "
        f"Check the inventory dashboard."
    )

    notified = 0
    for phone in boss_phones:
        try:
            SmsService.send(phone, summary)
            notified += 1
        except SmsError:
            pass

    return {"count": len(lows), "notified": notified}