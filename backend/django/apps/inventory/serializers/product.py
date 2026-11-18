from decimal import Decimal

from rest_framework import serializers

from ..models import Category, Product


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    product_type_display = serializers.CharField(
        source="get_product_type_display", read_only=True,
    )
    total_quantity = serializers.SerializerMethodField()
    needs_reorder = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "sku", "part_number", "barcode", "name", "category", "category_name",
            "product_type", "product_type_display", "brand", "unit",
            "retail_price", "wholesale_price", "is_stocked", "is_active",
            "image", "total_quantity", "needs_reorder",
        )

    def get_total_quantity(self, obj):
        total = sum(
            (Decimal(level.quantity) for level in obj.levels.all()),
            Decimal("0"),
        )
        return str(total)

    def get_needs_reorder(self, obj):
        from ..services.reorder_service import ReorderService
        return any(ReorderService.needs_reorder(level) for level in obj.levels.all())


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    product_type_display = serializers.CharField(
        source="get_product_type_display", read_only=True,
    )
    stock_by_location = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "sku", "part_number", "barcode", "name", "description",
            "category", "category_name",
            "product_type", "product_type_display", "brand", "unit",
            "image", "cost_price", "retail_price", "wholesale_price",
            "is_stocked", "reorder_level", "reorder_qty",
            "is_active", "compatibility_notes",
            "created_at", "updated_at",
            "stock_by_location",
        )

    def get_stock_by_location(self, obj):
        return [
            {
                "location_id": level.location_id,
                "location_name": level.location.name,
                "quantity": str(level.quantity),
                "reorder_level": level.effective_reorder_level(),
            }
            for level in obj.levels.select_related("location").all()
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or getattr(user, "role", None) not in ("BOSS", "ADMIN"):
            data.pop("cost_price", None)
        return data


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "sku", "part_number", "barcode", "name", "description", "category",
            "product_type", "brand", "unit", "image",
            "cost_price", "retail_price", "wholesale_price",
            "is_stocked", "reorder_level", "reorder_qty",
            "is_active", "compatibility_notes",
        )

    def validate_sku(self, value):
        qs = Product.objects.filter(sku=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value

    def validate_barcode(self, value):
        if not value:
            return value
        qs = Product.objects.filter(barcode=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A product with this barcode already exists.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if getattr(user, "role", None) not in ("BOSS", "ADMIN"):
            # Helpers/agents cannot touch financials.
            for f in ("cost_price", "retail_price", "wholesale_price"):
                if f in attrs:
                    raise serializers.ValidationError(
                        {f: "Only a boss can set prices."}
                    )
        retail = attrs.get("retail_price") or getattr(self.instance, "retail_price", 0)
        wholesale = attrs.get("wholesale_price") or getattr(self.instance, "wholesale_price", 0)
        cost = attrs.get("cost_price") or getattr(self.instance, "cost_price", 0)
        if retail and cost and retail < cost:
            raise serializers.ValidationError(
                {"retail_price": "Retail price is below cost price."}
            )
        if wholesale and cost and wholesale < cost:
            raise serializers.ValidationError(
                {"wholesale_price": "Wholesale price is below cost price."}
            )
        return attrs