from rest_framework import serializers

from ..models import SupplierProduct


class SupplierProductListSerializer(serializers.ModelSerializer):
    supplier_display = serializers.CharField(source="supplier.name", read_only=True)
    product_display = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = SupplierProduct
        fields = (
            "id", "supplier", "supplier_display",
            "product", "product_display", "product_sku",
            "supplier_part_number",
            "last_purchase_price", "lead_time_days",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or getattr(user, "role", None) not in ("BOSS", "ADMIN"):
            data.pop("last_purchase_price", None)
        return data


class SupplierProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProduct
        fields = (
            "supplier", "product", "supplier_part_number",
            "last_purchase_price", "lead_time_days",
        )

    def validate_last_purchase_price(self, value):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if getattr(user, "role", None) not in ("BOSS", "ADMIN") and value is not None:
            raise serializers.ValidationError(
                "Only a boss can set purchase prices."
            )
        return value

    def validate(self, attrs):
        supplier = attrs.get("supplier") or getattr(self.instance, "supplier", None)
        product = attrs.get("product") or getattr(self.instance, "product", None)
        if supplier and product:
            qs = SupplierProduct.objects.filter(supplier=supplier, product=product)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"product": "This product is already linked to this supplier."}
                )
        return attrs