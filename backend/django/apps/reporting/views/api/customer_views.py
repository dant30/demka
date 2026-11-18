"""Receivables and customer value reports."""
from datetime import date

from apps.reporting.services import CustomerReportingService
from .base import ReportingAPIView


def _parse_as_of(request):
    value = request.query_params.get("as_of")
    try:
        return date.fromisoformat(value) if value else None
    except ValueError as exc:
        raise ValueError("as_of must use YYYY-MM-DD format.") from exc


class AgingSummaryView(ReportingAPIView):
    def get(self, request):
        try:
            as_of = _parse_as_of(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.csv_or_json(request, CustomerReportingService.aging_summary(as_of))


class AgingDetailView(ReportingAPIView):
    def get(self, request):
        try:
            as_of = _parse_as_of(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        rows = CustomerReportingService.aging_detail(as_of)
        return self.csv_or_json(request, rows, "receivables_aging.csv")


class TopCustomersView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
            limit = self.integer_param(request, "limit", 20, maximum=500)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end,
            lambda first, last: CustomerReportingService.top_customers(first, last, limit),
            "top_customers.csv",
        )


class CreditUtilizationView(ReportingAPIView):
    def get(self, request):
        try:
            limit = self.integer_param(request, "limit", 50, maximum=500)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.csv_or_json(
            request, CustomerReportingService.credit_utilization(limit),
            "credit_utilization.csv",
        )
