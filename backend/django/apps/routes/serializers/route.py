from rest_framework import serializers

from ..models import Route


class RouteListSerializer(serializers.ModelSerializer):
    default_agent_name = serializers.SerializerMethodField()
    schedule_days = serializers.SerializerMethodField()
    open_runs = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = (
            "id", "code", "name", "is_active",
            "default_agent", "default_agent_name",
            "schedule_days", "open_runs",
        )

    def get_default_agent_name(self, obj):
        if not obj.default_agent:
            return None
        return obj.default_agent.get_full_name() or obj.default_agent.username

    def get_schedule_days(self, obj):
        return sorted(obj.schedules.filter(is_active=True).values_list("day_of_week", flat=True))

    def get_open_runs(self, obj):
        return obj.runs.filter(status__in=["PLANNED", "IN_PROGRESS"]).count()


class RouteDetailSerializer(RouteListSerializer):
    customer_count = serializers.SerializerMethodField()

    class Meta(RouteListSerializer.Meta):
        fields = RouteListSerializer.Meta.fields + (
            "description", "created_at", "customer_count",
        )

    def get_customer_count(self, obj):
        from apps.customers.models import CustomerRouteAssignment
        return CustomerRouteAssignment.objects.filter(
            route=obj, assigned_to__isnull=True,
        ).count()


class _DayOfWeekField(serializers.ListField):
    child = serializers.IntegerField(min_value=0, max_value=6)


class RouteWriteSerializer(serializers.ModelSerializer):
    schedule_days = _DayOfWeekField(required=False, write_only=True)

    class Meta:
        model = Route
        fields = (
            "code", "name", "description", "is_active",
            "default_agent", "schedule_days",
        )

    def validate_code(self, value):
        value = value.strip().upper()
        qs = Route.objects.filter(code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A route with this code already exists.")
        return value


class ChangeAgentSerializer(serializers.Serializer):
    new_agent = serializers.IntegerField(allow_null=True)
    reason = serializers.CharField()


class ReassignCustomersSerializer(serializers.Serializer):
    customer_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False,
    )
    target_route = serializers.IntegerField()
    reason = serializers.CharField()


class DeactivateRouteSerializer(serializers.Serializer):
    reason = serializers.CharField()