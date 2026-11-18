from rest_framework import serializers

from ..models import StockLevel


class StockLevelSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)
    effective_reorder_level = serializers.SerializerMethodField()
    needs_reorder = serializers.SerializerMethodField()

    class Meta:
        model = StockLevel
        fields = (
            "id", "product", "product_name", "product_sku",
            "location", "location_name", "quantity",
            "reorder_level", "effective_reorder_level",
            "needs_reorder", "last_updated",
        )
        read_only_fields = (
            "id", "quantity", "last_updated",
            "effective_reorder_level", "needs_reorder",
        )

    def get_effective_reorder_level(self, obj):
        return obj.effective_reorder_level()

    def get_needs_reorder(self, obj):
        from ..services.reorder_service import ReorderService
        return ReorderService.needs_reorder(obj)


class StockAdjustSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    location = serializers.IntegerField()
    delta = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)