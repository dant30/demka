from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import StandardPagination
from apps.sales.models import SpecialOrder
from apps.sales.permissions import CanCreateSale, CanViewSales
from apps.sales.serializers import (
    SpecialOrderCancelSerializer,
    SpecialOrderSerializer,
)
from apps.sales.services import SpecialOrderService


class SpecialOrderFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    supplier = django_filters.NumberFilter()

    class Meta:
        model = SpecialOrder
        fields = ("status", "supplier")


class SpecialOrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        SpecialOrder.objects
        .select_related("sale_item__sale", "sale_item__product", "supplier")
        .all()
    )
    serializer_class = SpecialOrderSerializer
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SpecialOrderFilterSet
    search_fields = ("sale_item__sale__sale_number", "sale_item__product__sku", "sale_item__product__name")
    ordering = ["-id"]

    def get_permissions(self):
        if self.action in ("mark_arrived", "mark_delivered", "cancel"):
            return [CanCreateSale()]
        return [CanViewSales()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, "role", None)
        if role == "FIELD_AGENT":
            qs = qs.filter(sale_item__sale__agent=user)
        return qs

    @action(detail=True, methods=["post"], url_path="mark-arrived")
    def mark_arrived(self, request, pk=None):
        so = SpecialOrderService.mark_arrived(int(pk), request.user)
        return Response(SpecialOrderSerializer(so).data)

    @action(detail=True, methods=["post"], url_path="mark-delivered")
    def mark_delivered(self, request, pk=None):
        so = SpecialOrderService.mark_delivered(int(pk), request.user)
        return Response(SpecialOrderSerializer(so).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        s = SpecialOrderCancelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        so = SpecialOrderService.cancel(
            int(pk), request.user, s.validated_data.get("reason", ""),
        )
        return Response(SpecialOrderSerializer(so).data)