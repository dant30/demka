"""Expenses-specific DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


BOSS_ROLES = ("BOSS", "ADMIN")
STAFF_ROLES = ("SALES_HELPER", "FIELD_AGENT", "BOSS", "ADMIN")


class CanViewExpenses(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanCreateExpense(BasePermission):
    """Any staff member can record an expense (fuel, minor costs, etc.)."""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanManageExpenses(BasePermission):
    """Editing/deleting an expense is boss-only — financial audit safety."""

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


class CanManageExpenseCategories(BasePermission):
    """Read: any staff. Write: boss only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "role", None) in BOSS_ROLES