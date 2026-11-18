from rest_framework import serializers

from ..models import CustomerRouteAssignment


class CustomerRouteAssignmentSerializer(serializers.ModelSerializer):
    route_display = serializers.CharField(source="route.name", read_only=True)
    customer_display = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = CustomerRouteAssignment
        fields = (
            "id", "customer", "customer_display",
            "route", "route_display",
            "assigned_from", "assigned_to", "reason",
        )
        read_only_fields = ("id", "assigned_from", "assigned_to")


class AssignRouteSerializer(serializers.Serializer):
    route = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)
    effective_date = serializers.DateField(required=False, allow_null=True)