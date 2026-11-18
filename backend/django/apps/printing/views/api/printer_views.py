from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.mixins import AuditedViewSetMixin
from apps.common.pagination import StandardPagination
from apps.printing.models import Printer
from apps.printing.permissions import CanManagePrinters
from apps.printing.serializers import PrinterSerializer, PrinterWriteSerializer
from apps.printing.services import PrintService
from apps.printing.services.connectors import ConnectorError


class PrinterViewSet(AuditedViewSetMixin, viewsets.ModelViewSet):
    queryset = Printer.objects.select_related("assigned_location", "assigned_user").all()
    permission_classes = [CanManagePrinters]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ("name", "identifier", "ip_address", "bt_mac_address")
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PrinterWriteSerializer
        return PrinterSerializer

    @action(detail=True, methods=["post"], url_path="test-print")
    def test_print(self, request, pk=None):
        printer = self.get_object()
        if not printer.is_active:
            return Response(
                {"detail": "Printer is inactive."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            job = PrintService.queue_test_print(printer_id=printer.pk, user=request.user)
        except ConnectorError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Try inline for immediate feedback — otherwise the queue picks it up
        result = PrintService.dispatch(job.pk)
        return Response({
            "job_id": result.pk,
            "status": result.status,
            "error": result.error_message,
        })