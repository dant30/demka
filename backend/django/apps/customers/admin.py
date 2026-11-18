from django.contrib import admin

from .models import Customer, CustomerContact, CustomerRouteAssignment


class CustomerContactInline(admin.TabularInline):
    model = CustomerContact
    extra = 0


class CustomerRouteAssignmentInline(admin.TabularInline):
    model = CustomerRouteAssignment
    extra = 0
    fields = ("route", "assigned_from", "assigned_to", "reason")
    readonly_fields = ("assigned_from",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "code", "name", "phone", "customer_type",
        "credit_limit", "current_balance", "is_active",
    )
    list_filter = ("customer_type", "is_active")
    search_fields = ("code", "name", "phone", "email", "business_name")
    readonly_fields = ("code", "current_balance", "created_at", "updated_at")
    inlines = [CustomerContactInline, CustomerRouteAssignmentInline]
    list_select_related = ("created_by",)


@admin.register(CustomerRouteAssignment)
class CustomerRouteAssignmentAdmin(admin.ModelAdmin):
    list_display = ("customer", "route", "assigned_from", "assigned_to")
    list_filter = ("route",)
    search_fields = ("customer__code", "customer__name", "route__code")


@admin.register(CustomerContact)
class CustomerContactAdmin(admin.ModelAdmin):
    list_display = ("name", "customer", "phone", "role")
    search_fields = ("name", "phone", "customer__name")