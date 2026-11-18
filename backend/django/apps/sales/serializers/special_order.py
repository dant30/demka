from rest_framework import serializers

from ..models import SpecialOrder


class SpecialOrderSerializer(serializers.ModelSerializer):
    sale_number = serializers.CharField(source="sale_item.sale.sale_number", read_only=True)
    product_sku = serializers.CharField(source="sale_item.product.sku", read_only=True)
    product_name = serializers.CharField(source="sale_item.product.name", read_only=True)
    quantity = serializers.DecimalField(
        source="sale_item.quantity", max_digits=12, decimal_places=2, read_only=True,
    )
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SpecialOrder
        fields = (
            "id", "sale_item", "sale_number",
            "product_sku", "product_name", "quantity",
            "supplier", "supplier_name",
            "purchase_order_item",
            "customer_deposit", "expected_arrival_date",
            "status", "status_display", "notes",
        )
        read_only_fields = fields


class SpecialOrderCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)