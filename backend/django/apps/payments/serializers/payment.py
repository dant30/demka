from decimal import Decimal

from rest_framework import serializers

from ..models import Payment


class PaymentListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    method_code = serializers.CharField(source="method.code", read_only=True)
    method_name = serializers.CharField(source="method.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    sale_number = serializers.CharField(source="sale.sale_number", read_only=True, default=None)
    received_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id", "payment_number",
            "sale", "sale_number",
            "customer", "customer_name",
            "method", "method_code", "method_name",
            "amount", "reference", "status", "status_display",
            "received_by", "received_by_name", "received_at",
        )

    def get_received_by_name(self, obj):
        u = obj.received_by
        return u.get_full_name() or u.username if u else None


class PaymentDetailSerializer(PaymentListSerializer):
    class Meta(PaymentListSerializer.Meta):
        fields = PaymentListSerializer.Meta.fields + (
            "location",
            "mpesa_phone", "mpesa_transaction_id", "mpesa_receipt_number",
            "notes",
        )


class PaymentCreateSerializer(serializers.Serializer):
    """Standalone (on-account) payment."""
    customer = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    method = serializers.CharField(help_text="PaymentMethod.code (CASH, MPESA, CHEQUE, BANK_TRANSFER)")
    reference = serializers.CharField(required=False, allow_blank=True)
    location = serializers.IntegerField(required=False, allow_null=True)
    mpesa_phone = serializers.CharField(required=False, allow_blank=True)
    mpesa_transaction_id = serializers.CharField(required=False, allow_blank=True)
    mpesa_receipt_number = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class PaymentReverseSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)