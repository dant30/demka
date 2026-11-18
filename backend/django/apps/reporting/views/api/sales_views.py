"""Sales and product-performance reports."""
from apps.reporting.services import ProductReportingService, SalesReportingService
from .base import ReportingAPIView


class SalesSummaryView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(request, start, end, SalesReportingService.summary)


class SalesByDayView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(request, start, end, SalesReportingService.by_day, "sales_by_day.csv")


class SalesByCustomerTypeView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, SalesReportingService.by_customer_type,
            "sales_by_customer_type.csv",
        )


class TopProductsView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
            limit = self.integer_param(request, "limit", 20, maximum=500)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end,
            lambda first, last: ProductReportingService.best_sellers(first, last, limit),
            "top_products.csv",
        )


class WorstProductsView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
            limit = self.integer_param(request, "limit", 20, maximum=500)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end,
            lambda first, last: ProductReportingService.worst_sellers(first, last, limit),
            "worst_products.csv",
        )


class MarginAnalysisView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
            limit = self.integer_param(request, "limit", 50, maximum=500)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end,
            lambda first, last: ProductReportingService.margin_analysis(first, last, limit),
            "margin_analysis.csv",
        )
