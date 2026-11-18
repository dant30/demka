from django.contrib import admin

from .models import (
    GoodsReceivedItem,
    GoodsReceivedNote,
    PurchaseOrder,
    PurchaseOrderItem,
)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("line_total",)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "po_number", "supplier", "status", "expected_date",
        "subtotal", "tax", "total", "created_by", "created_at",
    )
    list_filter = ("status", "supplier")
    search_fields = ("po_number", "supplier__name", "notes")
    readonly_fields = ("po_number", "subtotal", "tax", "total", "created_at")
    inlines = [PurchaseOrderItemInline]


class GoodsReceivedItemInline(admin.TabularInline):
    model = GoodsReceivedItem
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("po_item",)


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    list_display = (
        "grn_number", "supplier", "po", "location",
        "received_by", "received_at",
    )
    list_filter = ("supplier", "location")
    search_fields = ("grn_number", "supplier__name", "po__po_number")
    readonly_fields = ("grn_number", "received_at")
    inlines = [GoodsReceivedItemInline]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "po", "product", "quantity_ordered", "quantity_received",
        "unit_cost", "line_total",
    )
    list_select_related = ("po", "product")
    search_fields = ("po__po_number", "product__sku", "product__name")


@admin.register(GoodsReceivedItem)
class GoodsReceivedItemAdmin(admin.ModelAdmin):
    list_display = ("grn", "product", "quantity_received", "unit_cost")
    list_select_related = ("grn", "product")