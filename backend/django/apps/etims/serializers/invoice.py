from rest_framework import serializers

from ..models import EtimsInvoice


class EtimsInvoiceListSerializer(serializers.ModelSerializer):
    sale_number = serializers.CharField(source="sale.sale_number", read_only=True, default=None)
    return_number = serializers.CharField(source="sales_return.return_number", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    receipt_type_display = serializers.CharField(source="get_receipt_type_display", read_only=True)

    class Meta:
        model = EtimsInvoice
        fields = (
            "id", "receipt_type", "receipt_type_display",
            "sale", "sale_number", "sales_return", "return_number",
            "invoice_number", "invc_no", "org_invc_no",
            "cu_invc_no", "status", "status_display",
            "retry_count", "submitted_at", "created_at",
        )
        read_only_fields = fields


class EtimsInvoiceDetailSerializer(EtimsInvoiceListSerializer):
    class Meta(EtimsInvoiceListSerializer.Meta):
        fields = EtimsInvoiceListSerializer.Meta.fields + (
            "cur_rcpt_no", "tot_rcpt_no",
            "control_code", "receipt_signature",
            "sdc_date_time", "qr_code_data",
            "request_payload", "response_payload",
            "error_message", "last_attempt_at", "next_retry_at",
        )


class EtimsResubmitSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)