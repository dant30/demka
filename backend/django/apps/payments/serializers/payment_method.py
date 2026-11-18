from rest_framework import serializers

from ..models import PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ("id", "code", "name", "requires_reference", "is_active")
        read_only_fields = ("id",)