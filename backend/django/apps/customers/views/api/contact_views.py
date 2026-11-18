from rest_framework import viewsets

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.customers.models import CustomerContact
from apps.customers.permissions import CanViewCustomers
from apps.customers.serializers import CustomerContactSerializer


class CustomerContactViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = CustomerContact.objects.select_related("customer").all()
    serializer_class = CustomerContactSerializer
    permission_classes = [CanViewCustomers]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.request.query_params.get("customer")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs