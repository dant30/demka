from django.db.models import Count
from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.suppliers.models import Supplier
from apps.suppliers.permissions import CanManageSuppliers, CanViewSuppliers
from apps.suppliers.serializers import (
    SupplierCreateSerializer,
    SupplierDetailSerializer,
    SupplierListSerializer,
    SupplierUpdateSerializer,
)
from apps.suppliers.serializers.supplier_product import SupplierProductListSerializer
from apps.suppliers.services import SupplierService


class SupplierFilterSet(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Supplier
        fields = ("is_active",)


class SupplierViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        Supplier.objects
        .annotate(product_count=Count("products"))
        .all()
        .order_by("name")
    )
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SupplierFilterSet
    search_fields = ("code", "name", "phone", "email", "kra_pin")
    ordering_fields = ("name", "code", "created_at" if False else "name")
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [CanManageSuppliers()]
        return [CanViewSuppliers()]

    def get_serializer_class(self):
        if self.action == "list":
            return SupplierListSerializer
        if self.action == "create":
            return SupplierCreateSerializer
        if self.action in ("update", "partial_update"):
            return SupplierUpdateSerializer
        return SupplierDetailSerializer

    # ---- Custom actions -----------------------------------
    @action(detail=True, methods=["get"], url_path="products")
    def products(self, request, pk=None):
        supplier = self.get_object()
        qs = supplier.products.select_related("product").all()
        return Response(SupplierProductListSerializer(
            qs, many=True, context={"request": request},
        ).data)

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        return Response(SupplierService.summary_stats(int(pk)))

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        SupplierService.deactivate(int(pk))
        return Response({"detail": "Supplier deactivated."}, status=status.HTTP_200_OK)