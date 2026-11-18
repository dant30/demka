from rest_framework import serializers

from ..models import EtimsItem


class EtimsItemSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EtimsItem
        fields = (
            "id", "product", "product_sku", "product_name",
            "item_cd", "item_cls_cd", "status", "status_display",
            "error_message", "registered_at", "updated_at",
        )
        read_only_fields = fields