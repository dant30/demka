from django.contrib import admin

from .models import (
    Category, Product, StockLevel, StockLocation,
    StockMovement, StockTransfer, StockTransferItem,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "applies_to")
    list_filter = ("applies_to",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku", "part_number", "name", "category", "product_type",
        "retail_price", "wholesale_price", "is_stocked", "is_active",
    )
    list_filter = ("product_type", "is_stocked", "is_active", "category")
    search_fields = ("sku", "part_number", "name", "barcode", "brand")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("category",)


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "location_type", "assigned_agent", "is_active")
    list_filter = ("location_type", "is_active")
    search_fields = ("name",)


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ("product", "location", "quantity", "reorder_level", "last_updated")
    list_select_related = ("product", "location")
    search_fields = ("product__sku", "product__name", "location__name")
    readonly_fields = ("last_updated",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "created_at", "movement_type", "product", "location",
        "quantity", "reference_type", "reference_id", "created_by",
    )
    list_filter = ("movement_type", "location", "reference_type")
    search_fields = ("product__sku", "product__name", "reference_id", "notes")
    list_select_related = ("product", "location", "created_by")
    readonly_fields = [f.name for f in StockMovement._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 0
    autocomplete_fields = ("product",)


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = (
        "id", "from_location", "to_location", "status",
        "initiated_by", "received_by", "created_at",
    )
    list_filter = ("status", "from_location", "to_location")
    inlines = [StockTransferItemInline]
    readonly_fields = ("created_at", "received_at")