from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import LargePagination
from apps.etims.models import EtimsInvoice
from apps.etims.permissions import CanRetryEtims, CanViewEtims
from apps.etims.serializers import (
    EtimsInvoiceDetailSerializer,
    EtimsInvoiceListSerializer,
    EtimsResubmitSerializer,
)
from apps.etims.services import ETIMSService


class InvoiceFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    receipt_type = django_filters.CharFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = EtimsInvoice
        fields = ("status", "receipt_type")


class EtimsInvoiceViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet,
):
    queryset = (
        EtimsInvoice.objects
        .select_related("sale", "sales_return")
        .all()
    )
    pagination_class = LargePagination
    filter_backends = [django_filters.DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = InvoiceFilterSet
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action == "resubmit":
            return [CanRetryEtims()]
        return [CanViewEtims()]

    def get_serializer_class(self):
        if self.action == "list":
            return EtimsInvoiceListSerializer
        if self.action == "resubmit":
            return EtimsResubmitSerializer
        return EtimsInvoiceDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self.request.user, "role", None) not in ("BOSS", "ADMIN"):
            qs = qs.defer(
                "request_payload", "response_payload",
                "control_code", "receipt_signature",
            )
        return qs

    @action(detail=True, methods=["post"], url_path="resubmit")
    def resubmit(self, request, pk=None):
        inv = self.get_object()
        if inv.status == EtimsInvoice.Status.SUBMITTED:
            return Response(
                {"detail": "Already submitted."}, status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            if inv.receipt_type == EtimsInvoice.ReceiptType.SALE:
                ETIMSService.submit_sale(inv.sale_id)
            else:
                ETIMSService.submit_credit_note(inv.sales_return_id)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        inv.refresh_from_db()
        return Response(EtimsInvoiceDetailSerializer(inv).data)