from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, viewsets

from apps.common.pagination import LargePagination
from apps.payments.models import CustomerLedgerEntry
from apps.payments.permissions import CanViewLedger
from apps.payments.serializers import CustomerLedgerEntrySerializer


class LedgerFilterSet(django_filters.FilterSet):
    customer = django_filters.NumberFilter()
    entry_type = django_filters.CharFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = CustomerLedgerEntry
        fields = ("customer", "entry_type")


class CustomerLedgerEntryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CustomerLedgerEntry.objects.select_related("customer").all()
    serializer_class = CustomerLedgerEntrySerializer
    permission_classes = [CanViewLedger]
    pagination_class = LargePagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_class = LedgerFilterSet
    ordering = ["-created_at"]