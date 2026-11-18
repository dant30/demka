"""Receivables aging, top customers, and credit utilization."""
from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum

from core.utils.money import q


QUALIFYING_STATUSES = ["CONFIRMED", "PARTIAL"]
MONEY = DecimalField(max_digits=14, decimal_places=2)


def _outstanding(as_of):
    from apps.sales.models import Sale

    return Sale.objects.filter(
        balance_due__gt=0,
        status__in=QUALIFYING_STATUSES,
        confirmed_at__isnull=False,
    )


def _age_filter(lower_days, upper_days, as_of):
    """Build due-date/confirmation-date conditions for one aging bucket."""
    lower_date = as_of - __import__("datetime").timedelta(days=upper_days)
    upper_date = as_of - __import__("datetime").timedelta(days=lower_days)
    return (
        Q(due_date__isnull=False, due_date__gte=lower_date, due_date__lte=upper_date)
        | Q(
            due_date__isnull=True,
            confirmed_at__date__gte=lower_date,
            confirmed_at__date__lte=upper_date,
        )
    )


class CustomerReportingService:
    @staticmethod
    def aging_summary(as_of: date | None = None) -> dict:
        as_of = as_of or date.today()
        ranges = {
            "0-30": (0, 30),
            "31-60": (31, 60),
            "61-90": (61, 90),
        }
        buckets = {}
        queryset = _outstanding(as_of)
        future = (
            Q(due_date__gt=as_of)
            | Q(due_date__isnull=True, confirmed_at__date__gt=as_of)
        )
        buckets["0-30"] = q(queryset.filter(future | _age_filter(*ranges["0-30"], as_of)).aggregate(v=Sum("balance_due"))["v"] or 0)
        for name, (low, high) in list(ranges.items())[1:]:
            buckets[name] = q(queryset.filter(_age_filter(low, high, as_of)).aggregate(v=Sum("balance_due"))["v"] or 0)
        buckets["90+"] = q(queryset.filter(
            Q(due_date__lt=as_of - __import__("datetime").timedelta(days=90))
            | Q(due_date__isnull=True, confirmed_at__date__lt=as_of - __import__("datetime").timedelta(days=90))
        ).aggregate(v=Sum("balance_due"))["v"] or 0)
        total = q(sum(buckets.values(), Decimal("0")))
        return {
            "as_of": as_of.isoformat(),
            "total_outstanding": str(total),
            "buckets": {key: str(value) for key, value in buckets.items()},
        }

    @staticmethod
    def aging_detail(as_of: date | None = None) -> list[dict]:
        as_of = as_of or date.today()
        rows = _outstanding(as_of).select_related("customer").order_by("confirmed_at")
        result = []
        for sale in rows:
            anchor = sale.due_date or sale.confirmed_at.date()
            days = (as_of - anchor).days
            bucket = "0-30" if days <= 30 else "31-60" if days <= 60 else "61-90" if days <= 90 else "90+"
            result.append({
                "sale_number": sale.sale_number,
                "customer_code": sale.customer.code,
                "customer_name": sale.customer.name,
                "customer_phone": sale.customer.phone,
                "confirmed_at": sale.confirmed_at.date().isoformat(),
                "due_date": sale.due_date.isoformat() if sale.due_date else "",
                "balance_due": str(q(sale.balance_due)),
                "days_outstanding": days,
                "bucket": bucket,
            })
        return result

    @staticmethod
    def top_customers(start: date, end: date, limit: int = 20) -> list[dict]:
        from apps.sales.models import Sale, SaleItem

        sales = Sale.objects.filter(
            status__in=["CONFIRMED", "PAID", "PARTIAL", "INVOICED"],
            confirmed_at__date__gte=start,
            confirmed_at__date__lte=end,
        )
        revenue_rows = (
            sales.values("customer_id", "customer__code", "customer__name", "customer__customer_type")
            .annotate(sale_count=Count("id"), revenue=Sum("total"))
            .order_by("-revenue")[:limit]
        )
        customer_ids = [row["customer_id"] for row in revenue_rows]
        cogs_rows = (
            SaleItem.objects.filter(sale__in=sales, sale__customer_id__in=customer_ids)
            .values("sale__customer_id")
            .annotate(cogs=Sum(ExpressionWrapper(F("quantity") * F("unit_cost"), output_field=MONEY)))
        )
        cogs_by_customer = {row["sale__customer_id"]: row["cogs"] or 0 for row in cogs_rows}
        return [
            {
                "customer_id": row["customer_id"],
                "code": row["customer__code"],
                "name": row["customer__name"],
                "customer_type": row["customer__customer_type"],
                "sale_count": row["sale_count"],
                "revenue": str(q(row["revenue"] or 0)),
                "cogs": str(q(cogs_by_customer.get(row["customer_id"]) or 0)),
                "gross_profit": str(q((row["revenue"] or 0) - (cogs_by_customer.get(row["customer_id"]) or 0))),
            }
            for row in revenue_rows
        ]

    @staticmethod
    def credit_utilization(limit: int = 50) -> list[dict]:
        from apps.customers.models import Customer

        customers = Customer.objects.filter(is_active=True, credit_limit__gt=0).order_by("-current_balance")[:limit]
        rows = []
        for customer in customers:
            balance = Decimal(customer.current_balance)
            credit_limit = Decimal(customer.credit_limit)
            utilization = q(balance * 100 / credit_limit) if credit_limit else Decimal("0")
            rows.append({
                "customer_id": customer.pk,
                "code": customer.code,
                "name": customer.name,
                "credit_limit": str(credit_limit),
                "current_balance": str(balance),
                "available_credit": str(q(credit_limit - balance)),
                "utilization_pct": str(utilization),
                "at_limit": balance >= credit_limit,
            })
        return rows
