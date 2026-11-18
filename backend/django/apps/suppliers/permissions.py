"""Suppliers-specific DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


BOSS_ROLES = ("BOSS", "ADMIN")
STAFF_ROLES = ("SALES_HELPER", "FIELD_AGENT", "BOSS", "ADMIN")


class CanViewSuppliers(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanManageSuppliers(BasePermission):
    """Only bosses can create/edit/delete suppliers and their product links."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return (
                request.user is not None
                and request.user.is_authenticated
                and getattr(request.user, "role", None) in STAFF_ROLES
            )
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )


class CanViewPurchasePrices(BasePermission):
    """Cost data (last_purchase_price) is boss-only."""
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )