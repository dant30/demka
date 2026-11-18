"""Sales volume, revenue, and channel breakdowns."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate

from core.utils.money import q
from .date_utils import trailing_days


QUALIFYING_STATUSES = ["CONFIRMED", "PAID", "PARTIAL", "INVOICED"]


def _sales(start, end):
    from apps.sales.models import Sale

    return Sale.objects.filter(
        status__in=QUALIFYING_STATUSES,
        confirmed_at__date__gte=start,
        confirmed_at__date__lte=end,
    )


class SalesReportingService:
    @staticmethod
    def summary(start: date, end: date) -> dict:
        sales = _sales(start, end)
        totals = sales.aggregate(
            count=Count("id"),
            revenue=Sum("total"),
            credit_revenue=Sum("total", filter=Q(is_credit_sale=True)),
        )
        revenue = q(totals["revenue"] or 0)
        credit = q(totals["credit_revenue"] or 0)
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "sale_count": totals["count"] or 0,
            "total_revenue": str(revenue),
            "credit_revenue": str(credit),
            "cash_revenue": str(q(revenue - credit)),
        }

    @staticmethod
    def by_day(start: date, end: date) -> list[dict]:
        grouped = (
            _sales(start, end)
            .annotate(day=TruncDate("confirmed_at"))
            .values("day")
            .annotate(count=Count("id"), revenue=Sum("total"))
        )
        by_date = {row["day"]: row for row in grouped}
        rows = []
        day = start
        while day <= end:
            row = by_date.get(day)
            rows.append({
                "date": day.isoformat(),
                "count": row["count"] if row else 0,
                "revenue": str(q(row["revenue"] or 0)) if row else "0.00",
            })
            day += timedelta(days=1)
        return rows

    @staticmethod
    def last_7_days() -> list[dict]:
        days = [day for day, _ in trailing_days(7)]
        grouped = (
            _sales(days[0], days[-1])
            .annotate(day=TruncDate("confirmed_at"))
            .values("day")
            .annotate(revenue=Sum("total"))
        )
        totals = {row["day"]: row["revenue"] for row in grouped}
        return [
            {"date": day.isoformat(), "revenue": str(q(totals.get(day) or 0))}
            for day in days
        ]

    @staticmethod
    def by_customer_type(start: date, end: date) -> list[dict]:
        grouped = (
            _sales(start, end)
            .values("customer__customer_type")
            .annotate(count=Count("id"), revenue=Sum("total"))
        )
        indexed = {row["customer__customer_type"]: row for row in grouped}
        return [
            {
                "customer_type": kind,
                "count": indexed.get(kind, {}).get("count", 0),
                "revenue": str(q(indexed.get(kind, {}).get("revenue") or 0)),
            }
            for kind in ("RETAIL", "RESELLER", "WALK_IN")
        ]
