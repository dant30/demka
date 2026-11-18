"""Base serializers for DEMKA."""
from rest_framework import serializers


class UserDisplaySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class BaseModelSerializer(serializers.ModelSerializer):
    """Common base — subclasses add Meta.model/fields."""

    created_by_display = serializers.SerializerMethodField()

    def get_created_by_display(self, obj):
        user = getattr(obj, "created_by", None)
        if not user:
            return None
        return user.get_full_name() or user.username


class MoneyField(serializers.DecimalField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 12)
        kwargs.setdefault("decimal_places", 2)
        kwargs.setdefault("coerce_to_string", False)
        super().__init__(**kwargs)