from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.payments.models import Payment
from apps.payments.permissions import (
    CanCreatePayment,
    CanReversePayment,
    CanViewLedger,
)
from apps.payments.serializers import (
    PaymentCreateSerializer,
    PaymentDetailSerializer,
    PaymentListSerializer,
    PaymentReverseSerializer,
)
from apps.payments.services import PaymentService


class PaymentFilterSet(django_filters.FilterSet):
    customer = django_filters.NumberFilter()
    sale = django_filters.NumberFilter()
    method = django_filters.NumberFilter(field_name="method_id")
    status = django_filters.CharFilter()
    received_after = django_filters.DateTimeFilter(field_name="received_at", lookup_expr="gte")
    received_before = django_filters.DateTimeFilter(field_name="received_at", lookup_expr="lte")

    class Meta:
        model = Payment
        fields = ("customer", "sale", "method", "status")


class PaymentViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = (
        Payment.objects
        .select_related("customer", "method", "sale", "received_by", "location")
        .all()
    )
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PaymentFilterSet
    search_fields = ("payment_number", "customer__name", "reference", "mpesa_receipt_number")
    ordering_fields = ("received_at", "amount")
    ordering = ["-received_at"]
    http_method_names = ["get", "post", "head", "options"]  # no PUT/PATCH/DELETE

    def get_permissions(self):
        if self.action == "create":
            return [CanCreatePayment()]
        if self.action == "reverse":
            return [CanReversePayment()]
        return [CanViewLedger()]

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        if self.action == "create":
            return PaymentCreateSerializer
        if self.action == "reverse":
            return PaymentReverseSerializer
        return PaymentDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "role", None) == "FIELD_AGENT":
            qs = qs.filter(received_by=user)
        return qs

    def create(self, request, *args, **kwargs):
        s = PaymentCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payment = PaymentService.create_standalone(s.validated_data, request.user)
        return Response(
            PaymentDetailSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="reverse")
    def reverse(self, request, pk=None):
        s = PaymentReverseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payment = PaymentService.reverse(
            int(pk), request.user, s.validated_data.get("reason", ""),
        )
        return Response(PaymentDetailSerializer(payment).data)