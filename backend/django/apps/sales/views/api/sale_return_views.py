from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import StandardPagination
from apps.sales.models import SalesReturn
from apps.sales.permissions import CanApproveReturn, CanCreateSale, CanViewSales
from apps.sales.serializers import (
    SalesReturnCreateSerializer,
    SalesReturnDetailSerializer,
    SalesReturnListSerializer,
    SalesReturnRejectSerializer,
)
from apps.sales.services import ReturnService


class SalesReturnFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    customer = django_filters.NumberFilter()
    original_sale = django_filters.NumberFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = SalesReturn
        fields = ("status", "customer", "original_sale")


class SalesReturnViewSet(viewsets.ModelViewSet):
    queryset = (
        SalesReturn.objects
        .select_related("original_sale", "customer", "refund_method", "created_by")
        .prefetch_related("items__product", "items__sale_item")
        .all()
    )
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SalesReturnFilterSet
    search_fields = ("return_number", "original_sale__sale_number", "customer__name")
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options"]  # transitions via actions

    def get_permissions(self):
        if self.action in ("approve", "reject", "complete"):
            return [CanApproveReturn()]
        if self.action == "create":
            return [CanCreateSale()]
        return [CanViewSales()]

    def get_serializer_class(self):
        if self.action == "list":
            return SalesReturnListSerializer
        if self.action == "create":
            return SalesReturnCreateSerializer
        if self.action == "reject":
            return SalesReturnRejectSerializer
        return SalesReturnDetailSerializer

    def create(self, request, *args, **kwargs):
        s = SalesReturnCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        ret = ReturnService.create_return(s.validated_data, request.user)
        return Response(
            SalesReturnDetailSerializer(ret).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        ret = ReturnService.approve(int(pk), request.user)
        return Response(SalesReturnDetailSerializer(ret).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        s = SalesReturnRejectSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        ret = ReturnService.reject(
            int(pk), request.user, s.validated_data.get("reason", ""),
        )
        return Response(SalesReturnDetailSerializer(ret).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        ret = ReturnService.complete(int(pk), request.user)
        return Response(SalesReturnDetailSerializer(ret).data)