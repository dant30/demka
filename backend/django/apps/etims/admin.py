from django.contrib import admin

from .models import EtimsConfig, EtimsInvoice, EtimsItem, EtimsSequence


@admin.register(EtimsConfig)
class EtimsConfigAdmin(admin.ModelAdmin):
    list_display = ("tin", "bhf_id", "environment", "trade_name", "is_active", "initialized_at")
    readonly_fields = ("initialized_at", "last_code_sync_at", "updated_at")

    def has_add_permission(self, request):
        return not EtimsConfig.objects.exists()


@admin.register(EtimsSequence)
class EtimsSequenceAdmin(admin.ModelAdmin):
    list_display = ("tin", "bhf_id", "next_no")
    search_fields = ("tin", "bhf_id")


@admin.register(EtimsItem)
class EtimsItemAdmin(admin.ModelAdmin):
    list_display = ("item_cd", "product", "item_cls_cd", "status", "registered_at")
    list_filter = ("status",)
    search_fields = ("item_cd", "item_cls_cd", "product__sku", "product__name")
    list_select_related = ("product",)
    readonly_fields = ("response_payload", "error_message", "registered_at", "updated_at")


@admin.register(EtimsInvoice)
class EtimsInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invc_no", "receipt_type", "invoice_number",
        "cu_invc_no", "status", "retry_count",
        "submitted_at", "created_at",
    )
    list_filter = ("status", "receipt_type")
    search_fields = ("invoice_number", "cu_invc_no", "receipt_signature", "sale__sale_number")
    list_select_related = ("sale", "sales_return")
    readonly_fields = (
        "invc_no", "org_invc_no", "cu_invc_no", "cur_rcpt_no", "tot_rcpt_no",
        "control_code", "receipt_signature", "sdc_date_time", "qr_code_data",
        "request_payload", "response_payload", "created_at", "submitted_at",
        "last_attempt_at", "next_retry_at", "retry_count", "error_message",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False