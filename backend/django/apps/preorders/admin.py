from django.contrib import admin

from .models import Preorder, PreorderCustomerSession, PreorderItem


class PreorderItemInline(admin.TabularInline):
    model = PreorderItem
    extra = 0
    readonly_fields = (
        "unit_price_estimated", "final_price", "available_quantity",
        "available_in_stock",
    )
    autocomplete_fields = ("product",)


@admin.register(Preorder)
class PreorderAdmin(admin.ModelAdmin):
    list_display = (
        "preorder_number", "customer", "status",
        "total_estimated", "preferred_pickup_date",
        "created_at", "ready_at",
    )
    list_filter = ("status",)
    search_fields = ("preorder_number", "customer__name", "customer__phone")
    readonly_fields = (
        "preorder_number", "created_at", "confirmed_at", "ready_at",
        "delivered_at", "cancelled_at", "cancelled_by", "total_estimated",
    )
    inlines = [PreorderItemInline]


@admin.register(PreorderCustomerSession)
class PreorderCustomerSessionAdmin(admin.ModelAdmin):
    list_display = (
        "customer", "is_active", "attempts",
        "verified_at", "created_at", "last_activity_at",
    )
    list_filter = ("is_active",)
    search_fields = ("customer__name", "customer__phone", "session_token")
    readonly_fields = (
        "otp_code", "session_token", "verified_at", "used_at",
        "attempts", "created_at", "last_activity_at",
        "ip_address", "user_agent",
    )

    def has_add_permission(self, request):
        return False


@admin.register(PreorderItem)
class PreorderItemAdmin(admin.ModelAdmin):
    list_display = (
        "preorder", "product", "quantity",
        "effective_unit_price", "line_total", "available_in_stock",
    )
    list_select_related = ("preorder", "product")
    autocomplete_fields = ("product",)