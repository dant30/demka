"""Accounts signals — onboarding hooks after user creation."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from apps.accounts.tasks import send_welcome_sms
        send_welcome_sms.delay(instance.id)
    except Exception:
        # never block user creation on a queue hiccup
        pass