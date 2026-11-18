from rest_framework import serializers

from ..models import StockLocation


class StockLocationSerializer(serializers.ModelSerializer):
    assigned_agent_display = serializers.SerializerMethodField()
    location_type_display = serializers.CharField(
        source="get_location_type_display", read_only=True,
    )

    class Meta:
        model = StockLocation
        fields = (
            "id", "name", "location_type", "location_type_display",
            "assigned_agent", "assigned_agent_display", "is_active",
        )

    def get_assigned_agent_display(self, obj):
        if not obj.assigned_agent:
            return None
        u = obj.assigned_agent
        return u.get_full_name() or u.username