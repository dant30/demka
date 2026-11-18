"""Financial, cash, VAT, and eTIMS reports."""
from rest_framework.response import Response

from apps.reporting.services import (
    CashReportingService,
    EtimsReportingService,
    ProfitReportingService,
    TaxReportingService,
)
from .base import ReportingAPIView


class ProfitLossView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, ProfitReportingService.period_pnl, "profit_loss.csv",
        )


class ProfitByChannelView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, ProfitReportingService.by_channel, "profit_by_channel.csv",
        )


class ProfitByProductTypeView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, ProfitReportingService.by_product_type,
            "profit_by_product_type.csv",
        )


class CashReconciliationView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, CashReportingService.daily_reconciliation,
            "cash_reconciliation.csv",
        )


class PaymentMethodsView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, CashReportingService.payment_method_breakdown,
            "payment_methods.csv",
        )


class CashVarianceView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, CashReportingService.variance_report,
            "cash_variance.csv",
        )


class VatSummaryView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(request, start, end, TaxReportingService.vat_summary)


class EtimsHealthView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(request, start, end, EtimsReportingService.submission_rates)


class EtimsFailuresView(ReportingAPIView):
    def get(self, request):
        try:
            limit = self.integer_param(request, "limit", 50, maximum=500)
        except ValueError as exc:
            return self.bad_request(str(exc))
        rows = EtimsReportingService.recent_failures(limit)
        return self.csv_or_json(request, rows, "etims_failures.csv")
