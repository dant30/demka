"""Accounts-specific DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


BOSS_ROLES = ("BOSS", "ADMIN")


class IsBossOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )


class IsBossOrSelf(BasePermission):
    """BOSS/ADMIN can manage assignments; other users can only view their own."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return getattr(request.user, "role", None) in BOSS_ROLES

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "role", None) in BOSS_ROLES:
            return True
        if obj.__class__.__name__ == "User":
            return obj.id == request.user.id
        return getattr(obj, "user_id", None) == request.user.id