from rest_framework import serializers

from ..models import StockMovement


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    movement_type_display = serializers.CharField(
        source="get_movement_type_display", read_only=True,
    )
    created_by_display = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = (
            "id", "product", "product_name", "product_sku",
            "location", "location_name",
            "movement_type", "movement_type_display",
            "quantity", "unit_cost",
            "reference_type", "reference_id",
            "notes", "created_by", "created_by_display", "created_at",
        )
        read_only_fields = fields  # immutable ledger — no writes via API

    def get_created_by_display(self, obj):
        if not obj.created_by:
            return None
        u = obj.created_by
        return u.get_full_name() or u.username