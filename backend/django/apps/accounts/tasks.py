from celery import shared_task
from django.contrib.auth import get_user_model

from core.services.sms import SmsService


User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_sms(self, user_id: int):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    if not user.phone:
        return

    try:
        SmsService.send(
            user.phone,
            f"Welcome to DEMKA, {user.get_full_name() or user.username}. "
            f"Your account is ready.",
        )
    except Exception as exc:
        raise self.retry(exc=exc)