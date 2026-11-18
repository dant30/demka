from decimal import Decimal

from rest_framework import serializers

from ..models import RouteRun


class RouteRunListSerializer(serializers.ModelSerializer):
    route_code = serializers.CharField(source="route.code", read_only=True)
    route_name = serializers.CharField(source="route.name", read_only=True)
    agent_name = serializers.SerializerMethodField()
    stock_location_name = serializers.CharField(source="stock_location.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RouteRun
        fields = (
            "id", "route", "route_code", "route_name",
            "agent", "agent_name",
            "stock_location", "stock_location_name",
            "run_date", "status", "status_display",
            "started_at", "completed_at",
            "cash_collected", "cash_variance",
        )

    def get_agent_name(self, obj):
        u = obj.agent
        return u.get_full_name() or u.username if u else None


class RouteRunDetailSerializer(RouteRunListSerializer):
    started_by_name = serializers.SerializerMethodField()
    completed_by_name = serializers.SerializerMethodField()

    class Meta(RouteRunListSerializer.Meta):
        fields = RouteRunListSerializer.Meta.fields + (
            "opening_stock_value", "closing_stock_value",
            "cash_expected", "cash_handed_in",
            "started_by", "started_by_name",
            "completed_by", "completed_by_name",
            "notes",
        )

    def get_started_by_name(self, obj):
        if not obj.started_by:
            return None
        return obj.started_by.get_full_name() or obj.started_by.username

    def get_completed_by_name(self, obj):
        if not obj.completed_by:
            return None
        return obj.completed_by.get_full_name() or obj.completed_by.username


class RouteRunCreateSerializer(serializers.Serializer):
    route = serializers.IntegerField()
    agent = serializers.IntegerField(required=False, allow_null=True)
    stock_location = serializers.IntegerField()
    run_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True)


class RouteRunCompleteSerializer(serializers.Serializer):
    cash_handed_in = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"),
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class RouteRunCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class MaterializeSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError(
                {"end_date": "end_date must be on or after start_date."}
            )
        # Guard against runaway planning
        delta = (attrs["end_date"] - attrs["start_date"]).days
        if delta > 60:
            raise serializers.ValidationError(
                {"end_date": "Range cannot exceed 60 days in one call."}
            )
        return attrs