"""Role-based DRF permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class _RolePermission(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return (
            request.user is not None
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in self.allowed_roles
        )


class IsAdmin(_RolePermission):
    allowed_roles = ("ADMIN",)


class IsBoss(_RolePermission):
    allowed_roles = ("BOSS", "ADMIN")


class IsSalesStaff(_RolePermission):
    allowed_roles = ("SALES_HELPER", "BOSS", "ADMIN")


class IsFieldAgent(_RolePermission):
    allowed_roles = ("FIELD_AGENT", "BOSS", "ADMIN")


class IsBossOrReadOnly(_RolePermission):
    allowed_roles = ("BOSS", "ADMIN")

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user is not None and request.user.is_authenticated
        return super().has_permission(request, view)


class IsOwnerOrBoss(BasePermission):
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "role", None) in ("BOSS", "ADMIN"):
            return True
        return getattr(obj, "created_by_id", None) == request.user.id


class IsAssignedAgentOrBoss(BasePermission):
    """Field agents can only see/touch resources assigned to them."""
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "role", None) in ("BOSS", "ADMIN"):
            return True
        if hasattr(obj, "agent_id"):
            return obj.agent_id == request.user.id
        if hasattr(obj, "assigned_agent_id"):
            return obj.assigned_agent_id == request.user.id
        return False