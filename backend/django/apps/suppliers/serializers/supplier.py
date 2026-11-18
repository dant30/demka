from rest_framework import serializers

from core.utils.validators import validate_kenyan_phone

from ..models import Supplier


def _code_taken(value: str, exclude_pk=None) -> bool:
    qs = Supplier.objects.filter(code=value)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


class SupplierListSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Supplier
        fields = (
            "id", "code", "name", "phone", "email",
            "payment_terms_days", "is_active", "product_count",
        )


class SupplierDetailSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)
    purchase_order_count = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = (
            "id", "code", "name", "phone", "email",
            "kra_pin", "address", "payment_terms_days",
            "is_active", "product_count", "purchase_order_count",
        )

    def get_purchase_order_count(self, obj):
        return obj.purchase_orders.count()


class SupplierCreateSerializer(serializers.ModelSerializer):
    code = serializers.CharField(
        max_length=20, required=False, allow_blank=True,
        help_text="Leave blank to auto-generate (SUP-0001, ...).",
    )

    class Meta:
        model = Supplier
        fields = (
            "code", "name", "phone", "email",
            "kra_pin", "address", "payment_terms_days", "is_active",
        )

    def validate_phone(self, value):
        if value:
            validate_kenyan_phone(value)
        return value

    def validate_code(self, value):
        if value and _code_taken(value):
            raise serializers.ValidationError("A supplier with this code already exists.")
        return value

    def create(self, validated_data):
        if not validated_data.get("code"):
            from apps.common.services.numbering import next_number
            validated_data["code"] = next_number("SUPPLIER", prefix="SUP-", width=4)
        return super().create(validated_data)


class SupplierUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = (
            "name", "phone", "email", "kra_pin", "address",
            "payment_terms_days", "is_active",
        )

    def validate_phone(self, value):
        if value:
            validate_kenyan_phone(value)
        return value