from rest_framework import serializers

from ..models import RouteSchedule


class RouteScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = RouteSchedule
        fields = ("id", "route", "day_of_week", "day_name", "is_active")
        read_only_fields = ("id",)

    def get_day_name(self, obj):
        return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][obj.day_of_week]