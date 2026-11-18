from rest_framework import serializers

from ..models import ExpenseCategory


class ExpenseCategorySerializer(serializers.ModelSerializer):
    expense_count = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseCategory
        fields = ("id", "name", "is_active", "expense_count")
        read_only_fields = ("id", "expense_count")

    def get_expense_count(self, obj):
        return obj.expense_set.count()

    def validate_name(self, value):
        qs = ExpenseCategory.objects.filter(name__iexact=value.strip())
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A category with this name already exists."
            )
        return value.strip()