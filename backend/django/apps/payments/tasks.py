from celery import shared_task
from django.utils import timezone


@shared_task
def reconcile_pending_mpesa() -> dict:
    """
    Periodic task: sweep MpesaTransactions that arrived but weren't
    auto-matched (e.g. payment row was rolled back).
    """
    from .models import MpesaTransaction
    from .services.mpesa_reconciliation_service import MpesaReconciliationService

    unmatched = MpesaTransaction.objects.filter(reconciled=False).order_by("-transaction_date")
    matched, skipped = 0, 0
    for tx in unmatched:
        result = MpesaReconciliationService.auto_match(tx.transaction_id)
        if result:
            matched += 1
        else:
            skipped += 1
    return {"matched": matched, "skipped": skipped, "checked_at": timezone.now().isoformat()}


@shared_task
def send_payment_receipt_sms(payment_id: int) -> dict:
    """Notify the customer via SMS that a payment was received."""
    from core.services.sms import SmsError, SmsService
    from .models import Payment

    try:
        payment = Payment.objects.select_related("customer", "method").get(pk=payment_id)
    except Payment.DoesNotExist:
        return {"sent": False}

    if not payment.customer.phone:
        return {"sent": False}

    body = (
        f"DEMKA: Received {payment.method.name} "
        f"KES {payment.amount} for {payment.customer.name}. "
        f"Ref {payment.payment_number}."
    )
    try:
        SmsService.send(payment.customer.phone, body)
        return {"sent": True}
    except SmsError:
        return {"sent": False}