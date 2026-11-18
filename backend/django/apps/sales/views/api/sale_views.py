from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.sales.models import Sale
from apps.sales.permissions import CanCancelSale, CanCreateSale, CanViewSales
from apps.sales.serializers import (
    SaleCancelSerializer,
    SaleCreateSerializer,
    SaleDetailSerializer,
    SaleListSerializer,
    SalePaymentSerializer,
    SalePreviewSerializer,
)
from apps.sales.services import SaleService


class SaleFilterSet(django_filters.FilterSet):
    channel = django_filters.CharFilter()
    status = django_filters.CharFilter()
    sale_type = django_filters.CharFilter()
    customer = django_filters.NumberFilter()
    agent = django_filters.NumberFilter()
    is_credit_sale = django_filters.BooleanFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = Sale
        fields = ("channel", "status", "sale_type", "customer", "agent", "is_credit_sale")


class SaleViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        Sale.objects
        .select_related("customer", "location", "agent", "route")
        .prefetch_related("items__product")
        .all()
    )
    permission_classes = [CanViewSales]
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SaleFilterSet
    search_fields = ("sale_number", "customer__name", "customer__phone")
    ordering_fields = ("created_at", "total", "sale_number")
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "patch", "head", "options"]  # no PUT, no DELETE

    def get_permissions(self):
        if self.action == "cancel":
            return [CanCancelSale()]
        if self.action in ("create", "preview", "confirm", "apply_payment"):
            return [CanCreateSale()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return SaleListSerializer
        if self.action == "create":
            return SaleCreateSerializer
        if self.action == "preview":
            return SalePreviewSerializer
        if self.action == "cancel":
            return SaleCancelSerializer
        if self.action == "apply_payment":
            return SalePaymentSerializer
        return SaleDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user, "role", None)
        if role == "FIELD_AGENT":
            qs = qs.filter(agent=user)
        elif role == "SALES_HELPER":
            qs = qs.filter(channel="SHOP")
        return qs

    # ---- Create / Preview --------------------------------
    def create(self, request, *args, **kwargs):
        s = SaleCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        confirm = s.validated_data.pop("confirm", True)
        sale = SaleService.create_sale(s.validated_data, request.user, confirm=confirm)
        return Response(
            SaleDetailSerializer(sale).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="preview")
    def preview(self, request):
        s = SalePreviewSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = SaleService.preview(s.validated_data, request.user)
        return Response(data)

    # ---- Lifecycle actions ------------------------------
    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        sale = SaleService.confirm(int(pk), request.user)
        return Response(SaleDetailSerializer(sale).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        s = SaleCancelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        sale = SaleService.cancel(int(pk), request.user, s.validated_data["reason"])
        return Response(SaleDetailSerializer(sale).data)

    @action(detail=True, methods=["post"], url_path="apply-payment")
    def apply_payment(self, request, pk=None):
        s = SalePaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payment = SaleService.apply_payment(int(pk), s.validated_data, request.user)
        # Re-fetch the sale for a fresh snapshot
        sale = Sale.objects.get(pk=pk)
        return Response({
            "payment": {
                "payment_number": payment.payment_number,
                "amount": str(payment.amount),
                "method": payment.method.code,
            },
            "sale": SaleDetailSerializer(sale).data,
        })

    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        return Response(SaleService.receipt_payload(int(pk)))

    @action(detail=True, methods=["get"], url_path="returns")
    def returns(self, request, pk=None):
        from apps.sales.serializers import SalesReturnListSerializer
        sale = self.get_object()
        qs = sale.returns.order_by("-created_at")
        return Response(SalesReturnListSerializer(qs, many=True).data)