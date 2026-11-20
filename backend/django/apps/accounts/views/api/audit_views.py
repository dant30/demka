from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, viewsets

from apps.accounts.models import AuditLog
from apps.accounts.permissions import IsBossOnly
from apps.accounts.serializers.audit import AuditLogSerializer
from apps.common.pagination import StandardPagination


class AuditLogFilterSet(django_filters.FilterSet):
    action = django_filters.CharFilter()
    model_name = django_filters.CharFilter()
    user = django_filters.NumberFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AuditLog
        fields = ("action", "model_name", "user")


class AuditLogViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    queryset = AuditLog.objects.select_related("user").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsBossOnly]
    pagination_class = StandardPagination
    filterset_class = AuditLogFilterSet
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter]
    search_fields = (
        "action", "model_name", "object_id",
        "user__username", "user__first_name", "user__last_name", "user__phone",
    )