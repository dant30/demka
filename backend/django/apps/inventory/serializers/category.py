from rest_framework import serializers

from ..models import Category


class CategorySerializer(serializers.ModelSerializer):
    parent_display = serializers.CharField(source="parent.name", read_only=True, default=None)
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = Category
        fields = (
            "id", "name", "parent", "parent_display",
            "applies_to", "product_count",
        )
        read_only_fields = ("id", "product_count")

    def validate_parent(self, value):
        if value is None:
            return value
        if self.instance and value.pk == self.instance.pk:
            raise serializers.ValidationError("A category cannot be its own parent.")
        if self.instance and self._is_descendant(value):
            raise serializers.ValidationError(
                "Cannot set a descendant as the parent."
            )
        return value

    def _is_descendant(self, candidate) -> bool:
        node = candidate
        seen = set()
        while node is not None and node.pk not in seen:
            seen.add(node.pk)
            if node.pk == self.instance.pk:
                return True
            node = node.parent
        return False