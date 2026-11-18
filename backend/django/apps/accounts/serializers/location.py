from rest_framework import serializers

from apps.accounts.models import UserLocationAssignment


class UserLocationAssignmentSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()
    location_display = serializers.CharField(source="location.name", read_only=True)

    class Meta:
        model = UserLocationAssignment
        fields = (
            "id", "user", "user_display",
            "location", "location_display",
            "is_primary", "assigned_at",
        )
        read_only_fields = ("id", "assigned_at")

    def get_user_display(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def validate(self, attrs):
        user = attrs.get("user") or (self.instance.user if self.instance else None)
        is_primary = attrs.get("is_primary", False)
        if is_primary and user:
            qs = UserLocationAssignment.objects.filter(user=user, is_primary=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"is_primary": "This user already has a primary location."}
                )
        return attrs