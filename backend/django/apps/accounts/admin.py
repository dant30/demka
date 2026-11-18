from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, User, UserLocationAssignment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "phone", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "phone", "email", "first_name", "last_name")
    ordering = ("-created_at",)
    fieldsets = BaseUserAdmin.fieldsets + (
        ("DEMKA", {"fields": ("phone", "role")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("DEMKA", {"fields": ("phone", "role")}),
    )


@admin.register(UserLocationAssignment)
class UserLocationAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "location", "is_primary", "assigned_at")
    list_filter = ("is_primary",)
    search_fields = ("user__username", "location__name")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "model_name", "object_id")
    list_filter = ("action", "model_name")
    search_fields = ("user__username", "model_name", "object_id")
    readonly_fields = (
        "user", "action", "model_name", "object_id",
        "changes", "ip_address", "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False