from celery import shared_task

from core.services.sms import SmsError, SmsService

from .models import Customer


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_customer_welcome_sms(self, customer_id: int):
    try:
        customer = Customer.objects.get(pk=customer_id)
    except Customer.DoesNotExist:
        return

    if not customer.phone:
        return

    try:
        SmsService.send(
            customer.phone,
            f"Karibu {customer.name}! You are now registered at DEMKA "
            f"with code {customer.code}.",
        )
    except SmsError as exc:
        raise self.retry(exc=exc)


@shared_task
def send_bulk_sms(customer_ids: list, message: str) -> dict:
    qs = Customer.objects.filter(pk__in=customer_ids, is_active=True)
    sent, failed = 0, 0
    for customer in qs:
        try:
            SmsService.send(customer.phone, message)
            sent += 1
        except SmsError:
            failed += 1
    return {"sent": sent, "failed": failed}