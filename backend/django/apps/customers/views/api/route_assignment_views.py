from rest_framework import viewsets

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.customers.models import CustomerRouteAssignment
from apps.customers.permissions import CanViewCustomers
from apps.customers.serializers import CustomerRouteAssignmentSerializer


class CustomerRouteAssignmentViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        CustomerRouteAssignment.objects
        .select_related("customer", "route")
        .all()
    )
    serializer_class = CustomerRouteAssignmentSerializer
    permission_classes = [CanViewCustomers]
    pagination_class = StandardPagination
    http_method_names = ["get", "post", "head", "options"]  # no direct edit

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.request.query_params.get("customer")
        route_id = self.request.query_params.get("route")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if route_id:
            qs = qs.filter(route_id=route_id)
        return qs
        