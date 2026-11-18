from rest_framework import serializers

from core.utils.validators import validate_kenyan_phone

from ..models import CustomerContact


class CustomerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContact
        fields = ("id", "customer", "name", "phone", "role")
        read_only_fields = ("id",)
        extra_kwargs = {"customer": {"required": False}}

    def validate_phone(self, value):
        validate_kenyan_phone(value)
        return value