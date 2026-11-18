from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.pagination import LargePagination
from apps.printing.models import PrintJob
from apps.printing.permissions import CanCreatePrintJob, CanManagePrintJobs
from apps.printing.serializers import (
    PrintJobDetailSerializer,
    PrintJobListSerializer,
    PushResultSerializer,
    QueueCreditNoteSerializer,
    QueuePreorderSlipSerializer,
    QueueReceiptSerializer,
    QueueRouteSheetSerializer,
)
from apps.printing.services import PrintService
from apps.printing.services.connectors import ConnectorError


class JobFilterSet(django_filters.FilterSet):
    status = django_filters.CharFilter()
    document_type = django_filters.CharFilter()
    printer = django_filters.NumberFilter()
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = PrintJob
        fields = ("status", "document_type", "printer")


class PrintJobViewSet(viewsets.ModelViewSet):
    queryset = (
        PrintJob.objects
        .select_related("printer", "created_by")
        .all()
    )
    pagination_class = LargePagination
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = JobFilterSet
    search_fields = ("reference_type", "reference_id", "document_type")
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [CanManagePrintJobs()]
        if self.action in ("retry", "cancel", "dispatch"):
            return [CanManagePrintJobs()]
        return [CanCreatePrintJob()]

    def get_serializer_class(self):
        if self.action == "list":
            return PrintJobListSerializer
        if self.action == "queue_receipt":
            return QueueReceiptSerializer
        if self.action == "queue_credit_note":
            return QueueCreditNoteSerializer
        if self.action == "queue_preorder_slip":
            return QueuePreorderSlipSerializer
        if self.action == "queue_route_sheet":
            return QueueRouteSheetSerializer
        if self.action == "report_client_result":
            return PushResultSerializer
        return PrintJobDetailSerializer

    # ---- Queue actions -----------------------------------
    @action(detail=False, methods=["post"], url_path="queue/receipt")
    def queue_receipt(self, request):
        s = QueueReceiptSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        job = PrintService.queue_receipt(
            sale_id=s.validated_data["sale"], user=request.user,
        )
        return Response(PrintJobDetailSerializer(job).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="queue/credit-note")
    def queue_credit_note(self, request):
        s = QueueCreditNoteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        job = PrintService.queue_credit_note(
            sales_return_id=s.validated_data["sales_return"], user=request.user,
        )
        return Response(PrintJobDetailSerializer(job).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="queue/preorder-slip")
    def queue_preorder_slip(self, request):
        s = QueuePreorderSlipSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        job = PrintService.queue_preorder_slip(
            preorder_id=s.validated_data["preorder"], user=request.user,
        )
        return Response(PrintJobDetailSerializer(job).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="queue/route-sheet")
    def queue_route_sheet(self, request):
        s = QueueRouteSheetSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        job = PrintService.queue_route_sheet(
            run_id=s.validated_data["run"], user=request.user,
        )
        return Response(PrintJobDetailSerializer(job).data, status=status.HTTP_201_CREATED)

    # ---- Dispatch / control ------------------------------
    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch(self, request, pk=None):
        try:
            job = PrintService.dispatch(int(pk))
        except ConnectorError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PrintJobDetailSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        job = PrintService.retry(int(pk), request.user)
        return Response(PrintJobDetailSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        job = PrintService.cancel(int(pk), request.user)
        return Response(PrintJobDetailSerializer(job).data)

    # ---- Web Bluetooth (field agent) ---------------------
    @action(detail=True, methods=["get"], url_path="escpos")
    def escpos(self, request, pk=None):
        """Return base64-encoded ESC/POS bytes for the browser to push over Web Bluetooth."""
        return Response(PrintService.base64_payload(int(pk)))

    @action(detail=True, methods=["post"], url_path="report-result")
    def report_client_result(self, request, pk=None):
        """Frontend reports whether Web Bluetooth printing succeeded or failed."""
        s = PushResultSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if s.validated_data["success"]:
            job = PrintService.mark_printed_by_client(int(pk), user=request.user)
        else:
            job = PrintService.mark_failed_by_client(
                int(pk), user=request.user,
                error=s.validated_data.get("error", ""),
            )
        return Response(PrintJobDetailSerializer(job).data)