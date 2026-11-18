"""Preorder-specific DRF permissions."""
from rest_framework.permissions import BasePermission


BOSS_ROLES = ("BOSS", "ADMIN")
STAFF_ROLES = ("SALES_HELPER", "FIELD_AGENT", "BOSS", "ADMIN")


class IsPortalCustomer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (
            user is not None
            and getattr(user, "is_authenticated", False)
            and getattr(user, "role", None) == "PORTAL_CUSTOMER"
        )


class IsStaffPreorderViewer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanManagePreorders(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )