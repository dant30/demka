from decimal import Decimal

from rest_framework import serializers

from ..models import SalesReturn, SalesReturnItem


class SalesReturnItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    sale_item_id = serializers.IntegerField(source="sale_item.pk", read_only=True)

    class Meta:
        model = SalesReturnItem
        fields = (
            "id", "sale_item_id",
            "product", "product_name", "product_sku",
            "quantity", "unit_price", "restock", "location",
        )
        read_only_fields = fields


class SalesReturnListSerializer(serializers.ModelSerializer):
    sale_number = serializers.CharField(source="original_sale.sale_number", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = SalesReturn
        fields = (
            "id", "return_number",
            "original_sale", "sale_number",
            "customer", "customer_name",
            "status", "status_display",
            "refund_amount", "item_count", "created_at",
        )


class SalesReturnDetailSerializer(serializers.ModelSerializer):
    sale_number = serializers.CharField(source="original_sale.sale_number", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    refund_method_code = serializers.CharField(source="refund_method.code", read_only=True, default=None)
    created_by_name = serializers.SerializerMethodField()
    items = SalesReturnItemSerializer(many=True, read_only=True)

    class Meta:
        model = SalesReturn
        fields = (
            "id", "return_number",
            "original_sale", "sale_number",
            "customer", "customer_name",
            "status", "status_display",
            "reason", "refund_amount",
            "refund_method", "refund_method_code",
            "created_by", "created_by_name",
            "created_at", "items",
        )

    def get_created_by_name(self, obj):
        u = obj.created_by
        return u.get_full_name() or u.username if u else None


class _ReturnLineWriteSerializer(serializers.Serializer):
    sale_item = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    restock = serializers.BooleanField(default=True, required=False)
    location = serializers.IntegerField(required=False, allow_null=True)


class SalesReturnCreateSerializer(serializers.Serializer):
    original_sale = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)
    refund_method = serializers.IntegerField(required=False, allow_null=True)
    items = _ReturnLineWriteSerializer(many=True, allow_empty=False)


class SalesReturnRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)