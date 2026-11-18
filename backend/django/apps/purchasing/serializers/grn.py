from decimal import Decimal

from rest_framework import serializers

from ..models import GoodsReceivedItem, GoodsReceivedNote


class GRNItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    po_item_id = serializers.IntegerField(source="po_item.pk", read_only=True, default=None)

    class Meta:
        model = GoodsReceivedItem
        fields = (
            "id", "product", "product_name", "product_sku",
            "po_item_id", "quantity_received", "unit_cost",
        )
        read_only_fields = fields


class GRNListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    po_number = serializers.CharField(source="po.po_number", read_only=True, default=None)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = GoodsReceivedNote
        fields = (
            "id", "grn_number", "po", "po_number",
            "supplier", "supplier_name",
            "location", "location_name",
            "item_count", "received_at",
        )


class GRNDetailSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    po_number = serializers.CharField(source="po.po_number", read_only=True, default=None)
    received_by_display = serializers.SerializerMethodField()
    items = GRNItemSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsReceivedNote
        fields = (
            "id", "grn_number", "po", "po_number",
            "supplier", "supplier_name",
            "location", "location_name",
            "received_by", "received_by_display",
            "received_at", "items",
        )

    def get_received_by_display(self, obj):
        u = obj.received_by
        return u.get_full_name() or u.username if u else None


class _GRNItemWriteSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity_received = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01"),
    )
    unit_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
    )


class GRNCreateSerializer(serializers.Serializer):
    supplier = serializers.IntegerField()
    location = serializers.IntegerField()
    po = serializers.IntegerField(required=False, allow_null=True)
    items = _GRNItemWriteSerializer(many=True, allow_empty=False)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        product_ids = [i["product"] for i in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products in GRN items.")
        return value