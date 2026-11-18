"""Routes-specific DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


BOSS_ROLES = ("BOSS", "ADMIN")
FIELD_ROLES = ("FIELD_AGENT", "BOSS", "ADMIN")
STAFF_ROLES = ("SALES_HELPER", "FIELD_AGENT", "BOSS", "ADMIN")


class CanViewRoutes(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in STAFF_ROLES
        )


class CanManageRoutes(BasePermission):
    """Route configuration (create/edit/deactivate/change agent) — boss only."""

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


class CanOperateRun(BasePermission):
    """Field agents can start/complete their own runs; boss can override."""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in FIELD_ROLES
        )

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "role", None) in BOSS_ROLES:
            return True
        return getattr(obj, "agent_id", None) == request.user.id


class CanMaterializeRuns(BasePermission):
    """Auto-planning upcoming runs — boss only."""

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in BOSS_ROLES
        )