"""Cash reconciliation and payment-method reporting."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from core.utils.money import q


class CashReportingService:
    @staticmethod
    def daily_reconciliation(start: date, end: date) -> list[dict]:
        from apps.expenses.models import Expense
        from apps.payments.models import Payment

        collected_rows = (
            Payment.objects.filter(
                status="CONFIRMED", method__code="CASH",
                received_at__date__gte=start, received_at__date__lte=end,
            )
            .annotate(day=TruncDate("received_at"))
            .values("day", "location_id", "location__name")
            .annotate(total=Sum("amount"))
        )
        spent_rows = (
            Expense.objects.filter(
                payment_method__code="CASH", expense_date__gte=start, expense_date__lte=end,
            )
            .values("expense_date", "location_id", "location__name")
            .annotate(total=Sum("amount"))
        )

        per_day = {}
        for rows, key, date_key in (
            (collected_rows, "collected", "day"),
            (spent_rows, "spent", "expense_date"),
        ):
            for row in rows:
                day = row[date_key]
                location_id = row["location_id"]
                entry = per_day.setdefault(day, {}).setdefault(location_id, {
                    "location_id": location_id,
                    "location_name": row["location__name"] or "Unassigned",
                    "collected": Decimal("0"),
                    "spent": Decimal("0"),
                })
                entry[key] += Decimal(row["total"] or 0)

        result = []
        current_day = start
        while current_day <= end:
            locations = list(per_day.get(current_day, {}).values())
            collected = sum((row["collected"] for row in locations), Decimal("0"))
            spent = sum((row["spent"] for row in locations), Decimal("0"))
            result.append({
                "date": current_day.isoformat(),
                "collected": str(q(collected)),
                "spent": str(q(spent)),
                "expected": str(q(collected - spent)),
                "by_location": [
                    {
                        **row,
                        "collected": str(q(row["collected"])),
                        "spent": str(q(row["spent"])),
                        "expected": str(q(row["collected"] - row["spent"])),
                    }
                    for row in locations
                ],
            })
            current_day += timedelta(days=1)
        return result

    @staticmethod
    def variance_report(start: date, end: date) -> list[dict]:
        from apps.routes.services import RouteReportingService

        return RouteReportingService.variance_report(start, end)

    @staticmethod
    def payment_method_breakdown(start: date, end: date) -> list[dict]:
        from apps.payments.models import Payment

        rows = (
            Payment.objects.filter(
                status="CONFIRMED", received_at__date__gte=start, received_at__date__lte=end,
            )
            .values("method__code", "method__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        return [
            {
                "method_code": row["method__code"],
                "method_name": row["method__name"],
                "count": row["count"],
                "total": str(q(row["total"] or 0)),
            }
            for row in rows
        ]
