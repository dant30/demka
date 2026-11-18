from decimal import Decimal

from rest_framework import serializers

from ..models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    remaining_quantity = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderItem
        fields = (
            "id", "product", "product_name", "product_sku",
            "quantity_ordered", "quantity_received", "remaining_quantity",
            "unit_cost", "line_total",
        )
        read_only_fields = fields

    def get_remaining_quantity(self, obj):
        remaining = Decimal(obj.quantity_ordered) - Decimal(obj.quantity_received)
        return str(remaining if remaining > 0 else Decimal("0"))


class _POItemWriteSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity_ordered = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0"))


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            "id", "po_number", "supplier", "supplier_name",
            "status", "status_display", "expected_date",
            "subtotal", "tax", "total",
            "item_count", "created_at",
        )


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_by_display = serializers.SerializerMethodField()
    grns = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = (
            "id", "po_number", "supplier", "supplier_name",
            "status", "status_display", "expected_date",
            "subtotal", "tax", "total",
            "notes", "created_by", "created_by_display",
            "created_at", "items", "grns",
        )

    def get_created_by_display(self, obj):
        u = obj.created_by
        return u.get_full_name() or u.username if u else None

    def get_grns(self, obj):
        from ..models import GoodsReceivedNote
        rows = GoodsReceivedNote.objects.filter(po=obj).values(
            "id", "grn_number", "received_at",
        )
        return list(rows)


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier = serializers.IntegerField()
    expected_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    tax_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=Decimal("16.00"),
    )
    items = _POItemWriteSerializer(many=True, allow_empty=False)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        product_ids = [i["product"] for i in value]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products in PO items.")
        return value


class PurchaseOrderUpdateSerializer(serializers.ModelSerializer):
    """Limited update — item changes require cancel + recreate."""

    class Meta:
        model = PurchaseOrder
        fields = ("expected_date", "notes")