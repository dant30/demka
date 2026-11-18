from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.purchasing.models import PurchaseOrder
from apps.purchasing.permissions import CanManagePurchasing
from apps.purchasing.serializers import (
    GRNDetailSerializer,
    PurchaseOrderCreateSerializer,
    PurchaseOrderDetailSerializer,
    PurchaseOrderListSerializer,
    PurchaseOrderUpdateSerializer,
)
from apps.purchasing.services import GRNService, PurchaseOrderService


class PurchaseOrderFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    supplier = django_filters.NumberFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = PurchaseOrder
        fields = ("status", "supplier")


class PurchaseOrderViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        PurchaseOrder.objects
        .select_related("supplier", "created_by")
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
    filterset_class = PurchaseOrderFilterSet
    search_fields = ("po_number", "supplier__name", "notes")
    ordering_fields = ("created_at", "expected_date", "total")
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return PurchaseOrderListSerializer
        if self.action == "create":
            return PurchaseOrderCreateSerializer
        if self.action in ("update", "partial_update"):
            return PurchaseOrderUpdateSerializer
        return PurchaseOrderDetailSerializer

    # ---- Override create to route through service -------
    def create(self, request, *args, **kwargs):
        s = PurchaseOrderCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        po = PurchaseOrderService.create_po(s.validated_data, request.user)
        return Response(
            PurchaseOrderDetailSerializer(po).data,
            status=status.HTTP_201_CREATED,
        )

    # ---- Lifecycle actions ------------------------------
    @action(detail=True, methods=["post"], url_path="send")
    def send_po(self, request, pk=None):
        po = PurchaseOrderService.send(int(pk), request.user)
        return Response(PurchaseOrderDetailSerializer(po).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_po(self, request, pk=None):
        po = PurchaseOrderService.cancel(int(pk), request.user)
        return Response(PurchaseOrderDetailSerializer(po).data)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive_po(self, request, pk=None):
        """
        Convenience: post a GRN that receives outstanding items (or a subset).
        Body: {location: <id>, items?: [{product, quantity_received, unit_cost?}]}
        If items omitted, receives everything still outstanding.
        """
        po = self.get_object()
        location_id = request.data.get("location")
        if not location_id:
            return Response(
                {"detail": "`location` is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        items = request.data.get("items")
        if not items:
            items = GRNService.default_receipt_items_for_po(po)
            if not items:
                return Response(
                    {"detail": "PO has no outstanding items."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        grn = GRNService.post(
            data={
                "supplier": po.supplier_id,
                "location": location_id,
                "po": po.pk,
                "items": items,
            },
            user=request.user,
        )
        return Response(
            GRNDetailSerializer(grn).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="outstanding")
    def outstanding(self, request, pk=None):
        po = self.get_object()
        return Response(PurchaseOrderService.outstanding_items(po))