from decimal import Decimal

from rest_framework import serializers

from ..models import Preorder


class PriceAdjustmentSerializer(serializers.Serializer):
    item = serializers.IntegerField()
    final_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
    )


class ConfirmPreorderSerializer(serializers.Serializer):
    price_adjustments = PriceAdjustmentSerializer(many=True, required=False, default=list)


class DeliverPreorderSerializer(serializers.Serializer):
    location = serializers.IntegerField()
    payment_method = serializers.CharField(required=False, allow_blank=True)
    amount_paid = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
        default=Decimal("0"),
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
        required=False, default=Decimal("0"),
    )


class CancelPreorderSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class StaffPreorderDetailSerializer(serializers.ModelSerializer):
    from .preorder import PreorderItemSerializer
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    customer_code = serializers.CharField(source="customer.code", read_only=True)
    items = PreorderItemSerializer(many=True, read_only=True)
    converted_sale_number = serializers.CharField(
        source="converted_sale.sale_number", read_only=True, default=None,
    )
    cancelled_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Preorder
        fields = (
            "id", "preorder_number",
            "customer", "customer_name", "customer_phone", "customer_code",
            "status", "status_display",
            "total_estimated", "preferred_pickup_date",
            "notes", "staff_notes",
            "converted_sale", "converted_sale_number",
            "created_at", "confirmed_at", "ready_at", "delivered_at",
            "cancelled_at", "cancelled_by", "cancelled_by_name", "cancel_reason",
            "items",
        )

    def get_cancelled_by_name(self, obj):
        if not obj.cancelled_by:
            return None
        u = obj.cancelled_by
        return u.get_full_name() or u.username