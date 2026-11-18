from rest_framework import serializers

from ..models import RouteChangeLog


class RouteChangeLogSerializer(serializers.ModelSerializer):
    route_code = serializers.CharField(source="route.code", read_only=True)
    change_type_display = serializers.CharField(
        source="get_change_type_display", read_only=True,
    )
    previous_agent_name = serializers.SerializerMethodField()
    new_agent_name = serializers.SerializerMethodField()
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RouteChangeLog
        fields = (
            "id", "route", "route_code",
            "change_type", "change_type_display",
            "affected_customers",
            "previous_agent", "previous_agent_name",
            "new_agent", "new_agent_name",
            "reason", "changed_by", "changed_by_name", "changed_at",
        )
        read_only_fields = fields

    def get_previous_agent_name(self, obj):
        u = obj.previous_agent
        return (u.get_full_name() or u.username) if u else None

    def get_new_agent_name(self, obj):
        u = obj.new_agent
        return (u.get_full_name() or u.username) if u else None

    def get_changed_by_name(self, obj):
        u = obj.changed_by
        return (u.get_full_name() or u.username) if u else None