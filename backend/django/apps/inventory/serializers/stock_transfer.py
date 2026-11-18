from rest_framework import serializers

from ..models import StockTransfer, StockTransferItem


class StockTransferItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = StockTransferItem
        fields = ("id", "product", "product_name", "product_sku", "quantity")
        read_only_fields = ("id", "product_name", "product_sku")


class StockTransferListSerializer(serializers.ModelSerializer):
    from_location_name = serializers.CharField(source="from_location.name", read_only=True)
    to_location_name = serializers.CharField(source="to_location.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = StockTransfer
        fields = (
            "id", "from_location", "from_location_name",
            "to_location", "to_location_name",
            "status", "status_display", "item_count",
            "created_at", "received_at",
        )


class StockTransferDetailSerializer(serializers.ModelSerializer):
    from_location_name = serializers.CharField(source="from_location.name", read_only=True)
    to_location_name = serializers.CharField(source="to_location.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items = StockTransferItemSerializer(many=True, read_only=True)
    initiated_by_display = serializers.SerializerMethodField()
    received_by_display = serializers.SerializerMethodField()

    class Meta:
        model = StockTransfer
        fields = (
            "id", "from_location", "from_location_name",
            "to_location", "to_location_name",
            "status", "status_display",
            "initiated_by", "initiated_by_display",
            "received_by", "received_by_display",
            "created_at", "received_at",
            "notes", "items",
        )

    def get_initiated_by_display(self, obj):
        u = obj.initiated_by
        return u.get_full_name() or u.username if u else None

    def get_received_by_display(self, obj):
        u = obj.received_by
        return u.get_full_name() or u.username if u else None


class StockTransferCreateSerializer(serializers.Serializer):
    from_location = serializers.IntegerField()
    to_location = serializers.IntegerField()
    items = serializers.ListField(
        child=serializers.DictField(), allow_empty=False,
    )
    notes = serializers.CharField(required=False, allow_blank=True)