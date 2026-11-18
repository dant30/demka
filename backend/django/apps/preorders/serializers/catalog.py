from rest_framework import serializers

from apps.inventory.models import Category, Product


class CatalogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "applies_to")


class CatalogProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    product_type_display = serializers.CharField(
        source="get_product_type_display", read_only=True,
    )
    wholesale_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )
    available_qty = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )
    is_special_order = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "sku", "part_number", "name", "description",
            "category", "category_name",
            "product_type", "product_type_display",
            "brand", "unit",
            "image", "wholesale_price", "available_qty",
            "is_stocked", "is_special_order",
            "compatibility_notes",
        )
        read_only_fields = fields

    def get_is_special_order(self, obj):
        return not obj.is_stocked or (getattr(obj, "available_qty", 0) or 0) == 0