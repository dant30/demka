from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, viewsets

from apps.common.pagination import LargePagination
from apps.routes.models import RouteChangeLog
from apps.routes.permissions import CanViewRoutes
from apps.routes.serializers import RouteChangeLogSerializer


class ChangeLogFilterSet(django_filters.FilterSet):
    route = django_filters.NumberFilter()
    change_type = django_filters.CharFilter()
    changed_after = django_filters.DateTimeFilter(field_name="changed_at", lookup_expr="gte")
    changed_before = django_filters.DateTimeFilter(field_name="changed_at", lookup_expr="lte")

    class Meta:
        model = RouteChangeLog
        fields = ("route", "change_type")


class RouteChangeLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        RouteChangeLog.objects
        .select_related("route", "previous_agent", "new_agent", "changed_by")
        .all()
    )
    serializer_class = RouteChangeLogSerializer
    permission_classes = [CanViewRoutes]
    pagination_class = LargePagination
    filter_backends = [django_filters.DjangoFilterBackend]
    filterset_class = ChangeLogFilterSet
    ordering = ["-changed_at"]