from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, status, viewsets
from rest_framework.response import Response

from apps.common.pagination import StandardPagination
from apps.purchasing.models import GoodsReceivedNote
from apps.purchasing.permissions import CanManagePurchasing
from apps.purchasing.serializers import (
    GRNCreateSerializer,
    GRNDetailSerializer,
    GRNListSerializer,
)
from apps.purchasing.services import GRNService


class GRNFilterSet(django_filters.FilterSet):
    supplier = django_filters.NumberFilter()
    location = django_filters.NumberFilter()
    po = django_filters.NumberFilter()
    received_after = django_filters.DateTimeFilter(field_name="received_at", lookup_expr="gte")
    received_before = django_filters.DateTimeFilter(field_name="received_at", lookup_expr="lte")

    class Meta:
        model = GoodsReceivedNote
        fields = ("supplier", "location", "po")


class GoodsReceivedNoteViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """GRNs are immutable once posted — no update/delete endpoints."""

    queryset = (
        GoodsReceivedNote.objects
        .select_related("po", "supplier", "location", "received_by")
        .prefetch_related("items__product")
        .all()
    )
    permission_classes = [CanManagePurchasing]
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = GRNFilterSet
    search_fields = ("grn_number", "po__po_number", "supplier__name")
    ordering = ["-received_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return GRNListSerializer
        if self.action == "create":
            return GRNCreateSerializer
        return GRNDetailSerializer

    def create(self, request, *args, **kwargs):
        s = GRNCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        grn = GRNService.post(data=s.validated_data, user=request.user)
        return Response(
            GRNDetailSerializer(grn).data,
            status=status.HTTP_201_CREATED,
        )