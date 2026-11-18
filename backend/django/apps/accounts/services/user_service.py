"""User-related domain services."""
from django.db import transaction

from apps.accounts.models import UserLocationAssignment


class UserService:

    @staticmethod
    @transaction.atomic
    def assign_location(user, location, is_primary: bool = False) -> UserLocationAssignment:
        if is_primary:
            UserLocationAssignment.objects.filter(user=user).update(is_primary=False)
        obj, _ = UserLocationAssignment.objects.update_or_create(
            user=user,
            location=location,
            defaults={"is_primary": is_primary},
        )
        return obj

    @staticmethod
    @transaction.atomic
    def deactivate(user) -> None:
        user.is_active = False
        user.save(update_fields=["is_active"])