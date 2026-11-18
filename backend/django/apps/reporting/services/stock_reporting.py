"""Stock valuation, movement summaries, and low-stock alerts."""
from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum

from core.utils.money import q


MONEY = DecimalField(max_digits=14, decimal_places=2)


class StockReportingService:
    @staticmethod
    def valuation(as_of: date | None = None) -> dict:
        from apps.inventory.models import StockLevel

        value_expr = ExpressionWrapper(F("quantity") * F("product__cost_price"), output_field=MONEY)
        rows = (
            StockLevel.objects.select_related("location", "product")
            .values("location_id", "location__name")
            .annotate(total_units=Sum("quantity"), total_value=Sum(value_expr))
            .order_by("location__name")
        )
        by_location = [
            {
                "location_id": row["location_id"],
                "location_name": row["location__name"],
                "total_units": str(q(row["total_units"] or 0)),
                "total_value": str(q(row["total_value"] or 0)),
            }
            for row in rows
        ]
        totals = StockLevel.objects.aggregate(total_units=Sum("quantity"), total_value=Sum(value_expr))
        return {
            "as_of": (as_of or date.today()).isoformat(),
            "total_units": str(q(totals["total_units"] or 0)),
            "total_value": str(q(totals["total_value"] or 0)),
            "by_location": by_location,
        }

    @staticmethod
    def low_stock() -> list[dict]:
        from apps.inventory.services import ReorderService

        return [
            {
                "product_id": level.product_id,
                "sku": level.product.sku,
                "name": level.product.name,
                "location_id": level.location_id,
                "location_name": level.location.name,
                "quantity": str(q(level.quantity)),
                "reorder_level": level.effective_reorder_level(),
                "suggested_qty": str(ReorderService.suggested_quantity(level)),
                "cost_price": str(q(level.product.cost_price)),
            }
            for level in ReorderService.low_stock_levels()
        ]

    @staticmethod
    def movement_summary(start: date, end: date) -> dict:
        from apps.inventory.models import StockMovement

        grouped = (
            StockMovement.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
            .values("movement_type")
            .annotate(count=Count("id"), net_units=Sum("quantity"))
        )
        by_type = {row["movement_type"]: row for row in grouped}
        movement_types = ["SALE", "PURCHASE", "TRANSFER_IN", "TRANSFER_OUT", "ADJUSTMENT", "RETURN", "SPECIAL_ORDER_OUT"]
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "by_type": [
                {
                    "movement_type": kind,
                    "count": by_type.get(kind, {}).get("count", 0),
                    "net_units": str(q(by_type.get(kind, {}).get("net_units") or 0)),
                }
                for kind in movement_types
            ],
        }
