"""Purchasing-specific DRF permissions — purchasing is boss-only."""
from rest_framework.permissions import BasePermission


BOSS_ROLES = ("BOSS", "ADMIN")


class CanManagePurchasing(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )


class CanViewPurchasing(BasePermission):
    """Read is allowed for bosses only too — POs leak supplier pricing."""
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )