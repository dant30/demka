"""Customers-specific DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


BOSS_ROLES = ("BOSS", "ADMIN")
STAFF_ROLES = ("SALES_HELPER", "FIELD_AGENT", "BOSS", "ADMIN")


class CanViewCustomers(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanCreateCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanDeleteCustomer(BasePermission):
    """Only bosses/admin can delete customers — including financial history."""
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )


class CanEditCreditFields(BasePermission):
    """Only bosses can adjust credit_limit / current_balance directly."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "role", None) in BOSS_ROLES