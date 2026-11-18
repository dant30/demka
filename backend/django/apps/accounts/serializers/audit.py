from rest_framework import serializers

from apps.accounts.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = (
            "id", "user", "user_display", "action",
            "model_name", "object_id", "changes",
            "ip_address", "created_at",
        )
        read_only_fields = fields

    def get_user_display(self, obj):
        if not obj.user:
            return None
        return obj.user.get_full_name() or obj.user.username