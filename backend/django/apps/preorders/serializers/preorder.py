from decimal import Decimal

from rest_framework import serializers

from ..models import Preorder, PreorderItem


class PreorderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )
    effective_unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = PreorderItem
        fields = (
            "id", "product", "product_name", "product_sku",
            "quantity", "unit_price_estimated", "final_price",
            "effective_unit_price", "line_total",
            "available_in_stock", "available_quantity",
            "notes",
        )
        read_only_fields = fields


class PreorderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Preorder
        fields = (
            "id", "preorder_number", "status", "status_display",
            "total_estimated", "preferred_pickup_date",
            "item_count", "created_at", "confirmed_at", "ready_at", "delivered_at",
        )


class PreorderDetailSerializer(PreorderListSerializer):
    items = PreorderItemSerializer(many=True, read_only=True)
    converted_sale_number = serializers.CharField(
        source="converted_sale.sale_number", read_only=True, default=None,
    )

    class Meta(PreorderListSerializer.Meta):
        fields = PreorderListSerializer.Meta.fields + (
            "notes", "items", "converted_sale", "converted_sale_number",
        )


class PreorderItemWriteSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"),
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=200)


class PreorderSubmitSerializer(serializers.Serializer):
    preferred_pickup_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = PreorderItemWriteSerializer(many=True, allow_empty=False)