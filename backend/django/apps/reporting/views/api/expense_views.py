"""Expense breakdowns and monthly trends."""
from apps.expenses.services import ExpenseService
from apps.reporting.services import ExpenseReportingService
from .base import ReportingAPIView


class ExpenseSummaryView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        current = ExpenseService.summary(start, end)
        if request.query_params.get("compare", "").lower() in ("1", "true", "yes"):
            current = ExpenseReportingService.summary_with_comparison(start, end)
        return self.csv_or_json(request, current)


class ExpenseByCategoryView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, ExpenseService.by_category, "expenses_by_category.csv",
        )


class ExpenseByLocationView(ReportingAPIView):
    def get(self, request):
        try:
            start, end = self.resolve_range(request)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.period_response(
            request, start, end, ExpenseService.by_location, "expenses_by_location.csv",
        )


class ExpenseTrendView(ReportingAPIView):
    def get(self, request):
        try:
            months = self.integer_param(request, "months", 6, maximum=60)
        except ValueError as exc:
            return self.bad_request(str(exc))
        return self.csv_or_json(request, ExpenseService.monthly_trend(months), "expense_trend.csv")
