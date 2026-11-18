from django.contrib import admin

from .models import Sale, SaleItem, SalesReturn, SalesReturnItem, SpecialOrder


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = (
        "unit_price", "unit_cost", "discount",
        "tax_rate", "line_total", "returned_quantity",
    )


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "sale_number", "channel", "sale_type", "customer",
        "status", "total", "amount_paid", "balance_due",
        "is_credit_sale", "created_at",
    )
    list_filter = ("channel", "status", "sale_type", "is_credit_sale")
    search_fields = ("sale_number", "customer__name", "customer__phone")
    readonly_fields = (
        "sale_number", "subtotal", "tax_amount", "total",
        "amount_paid", "balance_due", "created_at", "confirmed_at",
        "cancelled_at", "cancelled_by", "cancellation_reason",
    )
    inlines = [SaleItemInline]


class SalesReturnItemInline(admin.TabularInline):
    model = SalesReturnItem
    extra = 0
    autocomplete_fields = ("product", "sale_item")


@admin.register(SalesReturn)
class SalesReturnAdmin(admin.ModelAdmin):
    list_display = (
        "return_number", "original_sale", "customer",
        "status", "refund_amount", "created_at",
    )
    list_filter = ("status",)
    search_fields = ("return_number", "original_sale__sale_number", "customer__name")
    readonly_fields = ("return_number", "created_at")
    inlines = [SalesReturnItemInline]


@admin.register(SpecialOrder)
class SpecialOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "sale_item", "supplier", "status",
        "customer_deposit", "expected_arrival_date",
    )
    list_filter = ("status", "supplier")
    search_fields = (
        "sale_item__sale__sale_number",
        "sale_item__product__sku",
        "sale_item__product__name",
    )
    autocomplete_fields = ("supplier", "purchase_order_item")


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = (
        "sale", "product", "quantity", "unit_price", "unit_cost",
        "line_total", "returned_quantity",
    )
    list_select_related = ("sale", "product")
    search_fields = ("sale__sale_number", "product__sku", "product__name")


@admin.register(SalesReturnItem)
class SalesReturnItemAdmin(admin.ModelAdmin):
    list_display = (
        "sales_return", "product", "quantity", "unit_price", "restock", "location",
    )
    list_select_related = ("sales_return", "product")