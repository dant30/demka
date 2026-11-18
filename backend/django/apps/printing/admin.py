from django.contrib import admin

from .models import Printer, PrintJob


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = (
        "name", "printer_type", "transport_summary",
        "assigned_location", "assigned_user",
        "paper_width_mm", "is_default", "is_active",
    )
    list_filter = ("printer_type", "is_active", "is_default", "paper_width_mm")
    search_fields = ("name", "identifier", "ip_address", "bt_mac_address")
    list_select_related = ("assigned_location", "assigned_user")
    readonly_fields = ("created_at", "updated_at", "transport_summary")

    fieldsets = (
        ("Identity", {"fields": ("name", "printer_type", "is_active", "is_default")}),
        ("Network / WiFi", {"fields": ("ip_address", "port")}),
        ("USB", {"fields": ("usb_vendor_id", "usb_product_id")}),
        ("Bluetooth", {"fields": ("bt_mac_address", "bt_rfcomm_channel", "identifier")}),
        ("Placement", {"fields": ("assigned_location", "assigned_user")}),
        ("Behaviour", {"fields": ("paper_width_mm", "supports_cash_drawer", "notes")}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = (
        "id", "document_type", "reference_type", "reference_id",
        "printer", "status", "attempts", "created_at", "printed_at",
    )
    list_filter = ("status", "document_type", "printer")
    search_fields = ("reference_type", "reference_id")
    list_select_related = ("printer", "created_by")
    readonly_fields = (
        "escpos_data", "payload", "attempts", "error_message",
        "last_attempt_at", "created_at", "printed_at",
    )

    def has_add_permission(self, request):
        return False