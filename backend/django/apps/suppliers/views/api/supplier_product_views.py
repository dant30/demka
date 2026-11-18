from django_filters import rest_framework as django_filters
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.suppliers.models import SupplierProduct
from apps.suppliers.permissions import CanManageSuppliers, CanViewSuppliers
from apps.suppliers.serializers import (
    SupplierProductListSerializer,
    SupplierProductWriteSerializer,
)


class SupplierProductFilterSet(django_filters.FilterSet):
    supplier = django_filters.NumberFilter()
    product = django_filters.NumberFilter()

    class Meta:
        model = SupplierProduct
        fields = ("supplier", "product")


class SupplierProductViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        SupplierProduct.objects
        .select_related("supplier", "product")
        .all()
    )
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SupplierProductFilterSet
    search_fields = ("supplier__name", "product__name", "product__sku", "supplier_part_number")
    ordering_fields = ("last_purchase_price", "lead_time_days")
    ordering = ["supplier__name"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [CanManageSuppliers()]
        return [CanViewSuppliers()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SupplierProductWriteSerializer
        return SupplierProductListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=False, methods=["get"], url_path="for-product/(?P<product_id>[^/.]+)")
    def for_product(self, request, product_id=None):
        qs = SupplierProduct.objects.filter(
            product_id=product_id, supplier__is_active=True,
        ).select_related("supplier", "product").order_by("last_purchase_price")
        return Response(SupplierProductListSerializer(
            qs, many=True, context={"request": request},
        ).data)

    @action(detail=False, methods=["get"], url_path="preferred/(?P<product_id>[^/.]+)")
    def preferred(self, request, product_id=None):
        prefer_fast = request.query_params.get("prefer_fast") == "true"
        obj = SupplierProduct.objects.filter(
            product_id=product_id, supplier__is_active=True,
        )
        obj = (
            obj.order_by("lead_time_days", "last_purchase_price")
            if prefer_fast
            else obj.order_by("last_purchase_price", "lead_time_days")
        ).first()
        if not obj:
            return Response({"detail": "No supplier available for this product."}, status=404)
        return Response(
            SupplierProductListSerializer(obj, context={"request": request}).data
        )