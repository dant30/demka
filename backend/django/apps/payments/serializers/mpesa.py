from decimal import Decimal

from rest_framework import serializers

from ..models import MpesaTransaction


class MpesaTransactionSerializer(serializers.ModelSerializer):
    matched_payment_number = serializers.CharField(
        source="matched_payment.payment_number", read_only=True, default=None,
    )

    class Meta:
        model = MpesaTransaction
        fields = (
            "id", "transaction_id", "mpesa_receipt",
            "phone", "amount", "account_reference",
            "transaction_date",
            "matched_payment", "matched_payment_number",
            "reconciled",
        )
        read_only_fields = fields


class MpesaSTKPushSerializer(serializers.Serializer):
    customer = serializers.IntegerField()
    phone = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("1"))
    account_reference = serializers.CharField(max_length=100)
    sale = serializers.IntegerField(required=False, allow_null=True)


class MpesaReconcileSerializer(serializers.Serializer):
    payment = serializers.IntegerField(
        help_text="ID of the PENDING Payment to link this M-Pesa transaction to.",
    )


class MpesaCallbackPayloadSerializer(serializers.Serializer):
    """Loose validation — Safaricom's payload shape. Used for docs only."""
    Body = serializers.DictField()