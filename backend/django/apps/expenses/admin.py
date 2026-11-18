from django.contrib import admin
from django.utils.html import format_html

from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "expense_count")
    list_filter = ("is_active",)
    search_fields = ("name",)

    def expense_count(self, obj):
        return obj.expense_set.count()
    expense_count.short_description = "Expenses"


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = (
        "expense_number", "expense_date", "category",
        "amount", "payment_method", "location", "route_run", "paid_by",
    )
    list_filter = ("category", "payment_method", "location")
    search_fields = ("expense_number", "description", "reference")
    list_select_related = ("category", "payment_method", "location", "paid_by", "route_run__route")
    readonly_fields = ("expense_number", "created_at", "receipt_preview")
    autocomplete_fields = ("category", "payment_method", "location", "route_run", "paid_by")

    fieldsets = (
        ("Expense", {
            "fields": ("expense_number", "expense_date", "category", "amount", "description"),
        }),
        ("Payment", {
            "fields": ("payment_method", "reference", "paid_by"),
        }),
        ("Context", {
            "fields": ("location", "route_run", "receipt_image", "receipt_preview"),
        }),
        ("Audit", {
            "fields": ("created_at",),
        }),
    )

    def receipt_preview(self, obj):
        if not obj.receipt_image:
            return "—"
        return format_html(
            '<a href="{0}" target="_blank"><img src="{0}" style="max-height:120px;border-radius:4px"/></a>',
            obj.receipt_image.url,
        )
    receipt_preview.short_description = "Receipt"