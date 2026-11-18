from celery import shared_task
from django.db.models import Q
from django.utils import timezone


@shared_task
def send_monthly_expense_digest() -> dict:
    """
    Monthly SMS digest to the boss with the previous month's expenses by category.
    Wire in Celery beat: schedule '0 8 1 * *' (1st of month, 8am).
    """
    from django.contrib.auth import get_user_model
    from core.services.sms import SmsError, SmsService
    from .services import ExpenseService

    User = get_user_model()
    today = timezone.now().date()
    # previous month
    first_of_month = today.replace(day=1)
    prev_month_end = first_of_month - timezone.timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    rows = ExpenseService.by_category(prev_month_start, prev_month_end)
    if not rows:
        return {"sent": False, "reason": "no expenses"}

    total = sum(float(r["total"]) for r in rows)
    body_lines = [
        f"DEMKA expenses for {prev_month_start:%b %Y}:",
        f"Total KES {total:,.2f}",
        *[f"- {r['category']}: {float(r['total']):,.0f}" for r in rows[:6]],
    ]
    body = " | ".join(body_lines)[:300]

    boss_phones = list(
        User.objects.filter(role__in=("BOSS", "ADMIN"), is_active=True)
        .exclude(phone="")
        .values_list("phone", flat=True)
    )
    sent = 0
    for phone in boss_phones:
        try:
            SmsService.send(phone, body)
            sent += 1
        except SmsError:
            pass
    return {"sent": sent, "categories": len(rows), "total": total}


@shared_task
def flag_expenses_missing_receipts(days: int = 30) -> dict:
    """
    Return expenses from the last N days with no receipt image.
    Boss reviews these weekly (called from a periodic task / cron).
    """
    from django.utils import timezone
    from .models import Expense

    cutoff = timezone.now().date() - timezone.timedelta(days=days)
    qs = (
        Expense.objects
        .filter(expense_date__gte=cutoff)
        .filter(Q(receipt_image="") | Q(receipt_image__isnull=True))
        .values("id", "expense_number", "expense_date", "amount", "category__name")
    )
    return {"count": qs.count(), "expenses": list(qs)}