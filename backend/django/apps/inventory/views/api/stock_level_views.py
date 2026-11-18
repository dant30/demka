from django.db.models import F, Q
from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.inventory.models import Product, StockLevel, StockLocation
from apps.inventory.permissions import (
    CanAdjustStock,
    CanViewInventory,
)
from apps.inventory.serializers import StockAdjustSerializer, StockLevelSerializer
from apps.inventory.services import ReorderService, StockService


class StockLevelFilterSet(django_filters.FilterSet):
    product = django_filters.NumberFilter()
    location = django_filters.NumberFilter()
    needs_reorder = django_filters.BooleanFilter(method="filter_needs_reorder")

    class Meta:
        model = StockLevel
        fields = ("product", "location")

    def filter_needs_reorder(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(
                reorder_level__isnull=False,
                reorder_level__gt=0,
                quantity__lte=F("reorder_level"),
            )
            | Q(
                reorder_level__isnull=True,
                product__reorder_level__gt=0,
                quantity__lte=F("product__reorder_level"),
            )
        )


class StockLevelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        StockLevel.objects
        .select_related("product", "location")
        .all()
    )
    serializer_class = StockLevelSerializer
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_class = StockLevelFilterSet
    ordering_fields = ("quantity", "last_updated")
    ordering = ["location__name", "product__name"]

    def get_permissions(self):
        return [CanViewInventory()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == "FIELD_AGENT":
            qs = qs.filter(location__assigned_agent=user)
        return qs


class StockAdjustView(APIView):
    """Boss-only manual stock adjustment — writes ADJUSTMENT movement."""

    permission_classes = [CanAdjustStock]

    def post(self, request):
        serializer = StockAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = Product.objects.filter(
            pk=serializer.validated_data["product"]
        ).first()
        location = StockLocation.objects.filter(
            pk=serializer.validated_data["location"]
        ).first()

        if not product or not location:
            return Response(
                {"detail": "Product or location not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        level, movement = StockService.adjust(
            product=product,
            location=location,
            delta=serializer.validated_data["delta"],
            movement_type="ADJUSTMENT",
            reference_type="ManualAdjustment",
            notes=serializer.validated_data.get("notes", ""),
            user=request.user,
            allow_negative=False,
        )
        return Response(
            {
                "product": product.pk,
                "location": location.pk,
                "quantity": str(level.quantity),
                "movement_id": movement.pk,
            },
            status=status.HTTP_200_OK,
        )