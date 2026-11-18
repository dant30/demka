from django.contrib import admin

from .models import CustomerLedgerEntry, MpesaTransaction, Payment, PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "requires_reference", "is_active")
    list_filter = ("is_active", "requires_reference")
    search_fields = ("code", "name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "payment_number", "customer", "method", "amount",
        "status", "sale", "received_by", "received_at",
    )
    list_filter = ("status", "method")
    search_fields = (
        "payment_number", "customer__name", "customer__phone",
        "reference", "mpesa_receipt_number",
    )
    readonly_fields = ("payment_number", "received_at")
    list_select_related = ("customer", "method", "sale", "received_by", "location")


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "mpesa_receipt", "phone", "amount", "account_reference",
        "reconciled", "matched_payment", "transaction_date",
    )
    list_filter = ("reconciled",)
    search_fields = ("mpesa_receipt", "phone", "account_reference", "transaction_id")
    readonly_fields = ("transaction_id", "raw_payload", "transaction_date")


@admin.register(CustomerLedgerEntry)
class CustomerLedgerEntryAdmin(admin.ModelAdmin):
    list_display = (
        "customer", "entry_type", "amount", "balance_after",
        "reference_type", "reference_id", "created_at",
    )
    list_filter = ("entry_type",)
    search_fields = ("customer__name", "customer__phone", "reference_id")
    list_select_related = ("customer",)
    readonly_fields = [f.name for f in CustomerLedgerEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False