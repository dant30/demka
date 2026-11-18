from django_filters import rest_framework as django_filters
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination
from apps.payments.models import MpesaTransaction
from apps.payments.permissions import CanReconcileMpesa, CanViewLedger
from apps.payments.serializers import (
    MpesaReconcileSerializer,
    MpesaSTKPushSerializer,
    MpesaTransactionSerializer,
    PaymentDetailSerializer,
)
from apps.payments.services import MpesaReconciliationService, PaymentService


class MpesaTransactionFilterSet(django_filters.FilterSet):
    reconciled = django_filters.BooleanFilter()

    class Meta:
        model = MpesaTransaction
        fields = ("reconciled",)


class MpesaTransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = MpesaTransaction.objects.select_related("matched_payment").all()
    serializer_class = MpesaTransactionSerializer
    pagination_class = StandardPagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = MpesaTransactionFilterSet
    search_fields = ("mpesa_receipt", "phone", "account_reference")
    ordering = ["-transaction_date"]

    def get_permissions(self):
        if self.action == "reconcile":
            return [CanReconcileMpesa()]
        return [CanViewLedger()]

    @action(detail=True, methods=["post"], url_path="reconcile")
    def reconcile(self, request, pk=None):
        s = MpesaReconcileSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payment = MpesaReconciliationService.manual_match(
            transaction_id=int(pk),
            payment_id=s.validated_data["payment"],
            user=request.user,
        )
        return Response(PaymentDetailSerializer(payment).data)


class MpesaSTKPushView(APIView):
    """Initiate an STK Push. Requires a PENDING payment to reconcile later."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = MpesaSTKPushSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payment, stk_response = PaymentService.initiate_stk_push(
            customer_id=s.validated_data["customer"],
            phone=s.validated_data["phone"],
            amount=s.validated_data["amount"],
            account_reference=s.validated_data["account_reference"],
            user=request.user,
            sale_id=s.validated_data.get("sale"),
        )
        return Response(
            {
                "payment": PaymentDetailSerializer(payment).data,
                "stk_response": stk_response,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class MpesaCallbackView(APIView):
    """
    Public Safaricom webhook — no auth, no throttling.
    Always returns 200 so Safaricom does not retry.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def post(self, request):
        from core.services.payment import MpesaCallbackProcessor

        try:
            result = MpesaCallbackProcessor.process(request.data)
            if result.get("matched"):
                checkout_id = result.get("transaction_id")
                if checkout_id:
                    MpesaReconciliationService.auto_match(checkout_id)
        except Exception:
            # Never raise to Safaricom — log in production
            pass

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})