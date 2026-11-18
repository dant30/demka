"""Reporting wrappers for expense totals and comparison periods."""
from datetime import date

from .date_utils import previous_period


class ExpenseReportingService:
    @staticmethod
    def summary_with_comparison(start: date, end: date) -> dict:
        from apps.expenses.services import ExpenseService

        current = ExpenseService.summary(start, end)
        prev_start, prev_end = previous_period(start, end)
        prior = ExpenseService.summary(prev_start, prev_end)
        return {
            **current,
            "comparison": {
                "period": prior["period"],
                "total": prior["total"],
                "count": prior["count"],
            },
        }
