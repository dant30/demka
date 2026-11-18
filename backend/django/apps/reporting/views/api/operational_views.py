"""Inventory and supplier reports."""
from datetime import date

from apps.reporting.services import ProductReportingService, StockReportingService, SupplierReportingService
from .base import ReportingAPIView


class StockValuationView(ReportingAPIView):
    def get(self, request):
        as_of_param = request.query_params.get("as_of")
        try:
            as_of = date.fromisoformat(as_of_param) if as_of_param else None
        except ValueError:
            return self.bad_request("as_of must use YYYY-MM-DD format.")
        return self.csv_or_json(request, StockReportingService.valuation(as_of))


class LowStockView(ReportingAPIView):
    def get(self, request):
        return self.csv_or_json(request, StockReportingService.low_stock(), "low_stock.csv")


class StockMovementSummaryView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, StockReportingService.movement_summary,
            "stock_movements.csv",
        )


class DeadStockView(ReportingAPIView):
    def get(self, request):
        try:
            days = self.integer_param(request, "days", 90, maximum=3650)
            limit = self.integer_param(request, "limit", 100, maximum=1000)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.csv_or_json(
            request, ProductReportingService.dead_stock(days_since_last_sale=days, limit=limit),
            "dead_stock.csv",
        )


class PurchasesBySupplierView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
            limit = self.integer_param(request, "limit", 50, maximum=500)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end,
            lambda first, last: SupplierReportingService.purchases_by_supplier(first, last, limit),
            "purchases_by_supplier.csv",
        )


class SupplierPriceTrendView(ReportingAPIView):
    def get(self, request):
        try:
            product_id = self.integer_param(request, "product", None, maximum=2**31 - 1)
            months = self.integer_param(request, "months", 6, maximum=60)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.csv_or_json(
            request, SupplierReportingService.price_trend(product_id, months),
            "supplier_price_trend.csv",
        )
