"""Inventory-specific DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


BOSS_ROLES = ("BOSS", "ADMIN")
STAFF_ROLES = ("SALES_HELPER", "FIELD_AGENT", "BOSS", "ADMIN")


class CanViewInventory(BasePermission):
    def has_permission(self, request, view):
        return request.user is not None and request.user.is_authenticated


class CanManageProducts(BasePermission):
    """Read: any staff. Write: boss only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "role", None) in BOSS_ROLES


class CanImportProducts(BasePermission):
    """Imports and template downloads are boss-only."""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )


class CanAdjustStock(BasePermission):
    """Manual stock adjustments are boss-only."""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )


class CanInitiateTransfer(BasePermission):
    """Any staff member can initiate a transfer (shop ↔ field van)."""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanViewCostData(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )