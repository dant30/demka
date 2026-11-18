from rest_framework import serializers

from ..models import EtimsConfig


class EtimsConfigSerializer(serializers.ModelSerializer):
    cmc_key_set = serializers.SerializerMethodField()
    base_url = serializers.CharField(read_only=True)

    class Meta:
        model = EtimsConfig
        fields = (
            "environment", "tin", "bhf_id", "device_serial",
            "cmc_key_set", "sdc_id", "mrc_no",
            "trade_name", "branch_name",
            "initialized_at", "last_code_sync_at",
            "is_active", "base_url", "updated_at",
        )
        read_only_fields = fields

    def get_cmc_key_set(self, obj):
        return bool(obj.cmc_key)


class EtimsConfigWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtimsConfig
        fields = (
            "environment", "tin", "bhf_id", "device_serial",
            "cmc_key", "client_id", "client_secret",
            "is_active",
        )
        extra_kwargs = {
            "cmc_key":     {"write_only": True, "required": False, "allow_blank": True},
            "client_secret": {"write_only": True, "required": False, "allow_blank": True},
        }