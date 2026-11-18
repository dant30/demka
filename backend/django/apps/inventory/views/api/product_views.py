from django.db.models import F, Prefetch, Q
from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.inventory.models import Product, StockLevel
from apps.inventory.permissions import CanManageProducts, CanViewInventory
from apps.inventory.serializers import (
    ProductDetailSerializer,
    ProductListSerializer,
    ProductWriteSerializer,
)
from apps.inventory.services import StockService


class ProductFilterSet(django_filters.FilterSet):
    category = django_filters.NumberFilter()
    product_type = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()
    is_stocked = django_filters.BooleanFilter()
    brand = django_filters.CharFilter(lookup_expr="iexact")
    needs_reorder = django_filters.BooleanFilter(method="filter_needs_reorder")

    class Meta:
        model = Product
        fields = ("category", "product_type", "is_active", "is_stocked", "brand")

    def filter_needs_reorder(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(is_stocked=True, is_active=True).filter(
            Q(levels__location__is_active=True)
            & (
                Q(
                    levels__reorder_level__isnull=False,
                    levels__reorder_level__gt=0,
                    levels__quantity__lte=F("levels__reorder_level"),
                )
                | Q(
                    levels__reorder_level__isnull=True,
                    reorder_level__gt=0,
                    levels__quantity__lte=F("reorder_level"),
                )
            )
        ).distinct()


class ProductViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        Product.objects
        .select_related("category")
        .prefetch_related("levels__location")
        .all()
    )
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilterSet
    search_fields = ("sku", "part_number", "name", "barcode", "brand", "compatibility_notes")
    ordering_fields = ("name", "sku", "retail_price", "created_at")
    ordering = ["name"]

    def get_permissions(self):
        return [CanManageProducts()]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action in ("create", "update", "partial_update"):
            return ProductWriteSerializer
        return ProductDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    # ---- Custom actions -----------------------------------
    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        return Response(StockService.product_summary(int(pk)))

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        """Fast SKU/barcode lookup — used by POS and field sales."""
        sku = request.query_params.get("sku", "").strip()
        part_number = request.query_params.get("part_number", "").strip()
        barcode = request.query_params.get("barcode", "").strip()
        qs = Product.objects.filter(is_active=True).select_related("category")
        if sku:
            qs = qs.filter(Q(sku__iexact=sku) | Q(part_number__iexact=sku))
        elif barcode:
            qs = qs.filter(barcode=barcode)
        elif part_number:
            qs = qs.filter(part_number__iexact=part_number)
        else:
            return Response({"detail": "Provide sku=, part_number=, or barcode=."}, status=status.HTTP_400_BAD_REQUEST)
        product = qs.first()
        if not product:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductListSerializer(product).data)