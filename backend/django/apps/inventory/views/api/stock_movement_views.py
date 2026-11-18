from django_filters import rest_framework as django_filters
from rest_framework import filters, viewsets

from apps.common.pagination import LargePagination
from apps.inventory.models import StockMovement
from apps.inventory.permissions import CanViewInventory
from apps.inventory.serializers import StockMovementSerializer


class StockMovementFilterSet(django_filters.FilterSet):
    product = django_filters.NumberFilter()
    location = django_filters.NumberFilter()
    movement_type = django_filters.CharFilter()
    reference_type = django_filters.CharFilter()
    reference_id = django_filters.CharFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = StockMovement
        fields = ("product", "location", "movement_type", "reference_type", "reference_id")


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        StockMovement.objects
        .select_related("product", "location", "created_by")
        .all()
    )
    serializer_class = StockMovementSerializer
    pagination_class = LargePagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_class = StockMovementFilterSet
    ordering = ["-created_at"]

    def get_permissions(self):
        return [CanViewInventory()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == "FIELD_AGENT":
            qs = qs.filter(location__assigned_agent=user)
        return qs