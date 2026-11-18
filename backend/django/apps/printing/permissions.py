"""Printing-specific DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


BOSS_ROLES = ("BOSS", "ADMIN")
STAFF_ROLES = ("SALES_HELPER", "FIELD_AGENT", "BOSS", "ADMIN")


class CanViewPrinters(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanManagePrinters(BasePermission):
    """Read: any staff. Write (create/edit/delete/configure): boss only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "role", None) in BOSS_ROLES


class CanCreatePrintJob(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanManagePrintJobs(BasePermission):
    """Retry / cancel / mark-printed is boss-only; everyone can queue and read."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "role", None) in BOSS_ROLES


class CanPushEscposToPrinter(BasePermission):
    """Only the job's owner or a boss can push the raw bytes to a printer."""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )