from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.preorders.models import Preorder
from apps.preorders.permissions import CanManagePreorders, IsStaffPreorderViewer
from apps.preorders.serializers import (
    CancelPreorderSerializer,
    ConfirmPreorderSerializer,
    DeliverPreorderSerializer,
    StaffPreorderDetailSerializer,
    PreorderListSerializer,
)
from apps.preorders.services import PreorderService


class StaffPreorderFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    customer = django_filters.NumberFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Preorder
        fields = ("status", "customer")


class StaffPreorderViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        Preorder.objects
        .select_related("customer", "converted_sale", "cancelled_by")
        .prefetch_related("items__product")
        .all()
    )
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = StaffPreorderFilterSet
    search_fields = ("preorder_number", "customer__name", "customer__phone")
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffPreorderViewer()]
        return [CanManagePreorders()]

    def get_serializer_class(self):
        if self.action == "list":
            return PreorderListSerializer
        if self.action == "confirm":
            return ConfirmPreorderSerializer
        if self.action == "deliver":
            return DeliverPreorderSerializer
        if self.action == "cancel":
            return CancelPreorderSerializer
        return StaffPreorderDetailSerializer

    # ---- Lifecycle actions -------------------------------
    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        s = ConfirmPreorderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        preorder = PreorderService.confirm(
            int(pk), request.user,
            price_adjustments=s.validated_data.get("price_adjustments"),
        )
        return Response(StaffPreorderDetailSerializer(preorder).data)

    @action(detail=True, methods=["post"], url_path="prepare")
    def prepare(self, request, pk=None):
        preorder = PreorderService.prepare(int(pk), request.user)
        return Response(StaffPreorderDetailSerializer(preorder).data)

    @action(detail=True, methods=["post"], url_path="ready")
    def mark_ready(self, request, pk=None):
        preorder = PreorderService.mark_ready(int(pk), request.user)
        return Response(StaffPreorderDetailSerializer(preorder).data)

    @action(detail=True, methods=["post"], url_path="deliver")
    def deliver(self, request, pk=None):
        s = DeliverPreorderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        preorder = PreorderService.deliver(int(pk), s.validated_data, request.user)
        return Response(StaffPreorderDetailSerializer(preorder).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        s = CancelPreorderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        preorder = PreorderService.cancel(
            int(pk), request.user, s.validated_data.get("reason", ""),
        )
        return Response(StaffPreorderDetailSerializer(preorder).data)