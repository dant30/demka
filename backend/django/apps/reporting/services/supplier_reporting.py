"""Supplier spend and received-price trends."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth

from core.utils.money import q


MONEY = DecimalField(max_digits=14, decimal_places=2)


class SupplierReportingService:
    @staticmethod
    def purchases_by_supplier(start: date, end: date, limit: int = 50) -> list[dict]:
        from apps.purchasing.models import PurchaseOrder

        safe_limit = max(1, min(int(limit), 500))
        rows = (
            PurchaseOrder.objects.filter(
                status__in=["SENT", "PARTIAL", "RECEIVED"],
                created_at__date__gte=start, created_at__date__lte=end,
            )
            .values("supplier_id", "supplier__code", "supplier__name")
            .annotate(po_count=Count("id"), total=Sum("total"))
            .order_by("-total")[:safe_limit]
        )
        return [
            {
                "supplier_id": row["supplier_id"],
                "code": row["supplier__code"],
                "name": row["supplier__name"],
                "po_count": row["po_count"],
                "total_spent": str(q(row["total"] or 0)),
            }
            for row in rows
        ]

    @staticmethod
    def price_trend(product_id: int, months: int = 6) -> list[dict]:
        from apps.purchasing.models import GoodsReceivedItem

        months = max(1, min(int(months), 60))
        cutoff = date.today() - timedelta(days=30 * months)
        total_cost = ExpressionWrapper(
            F("quantity_received") * F("unit_cost"), output_field=MONEY,
        )
        rows = (
            GoodsReceivedItem.objects.filter(product_id=product_id, grn__received_at__date__gte=cutoff)
            .annotate(month=TruncMonth("grn__received_at"))
            .values("month")
            .annotate(total_cost=Sum(total_cost), total_qty=Sum("quantity_received"))
            .order_by("month")
        )
        return [
            {
                "month": row["month"].strftime("%Y-%m"),
                "total_qty": str(q(row["total_qty"] or 0)),
                "total_cost": str(q(row["total_cost"] or 0)),
                "avg_unit_cost": str(q(Decimal(row["total_cost"] or 0) / Decimal(row["total_qty"])))
                if row["total_qty"] else "0.00",
            }
            for row in rows
        ]
