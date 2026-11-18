"""Product-level performance: best sellers, dead stock, and margins."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum

from core.utils.money import q


MONEY = DecimalField(max_digits=14, decimal_places=2)
QUALIFYING_STATUSES = ["CONFIRMED", "PAID", "PARTIAL", "INVOICED"]


def _sales(start, end):
    from apps.sales.models import SaleItem

    return SaleItem.objects.filter(
        sale__status__in=QUALIFYING_STATUSES,
        sale__confirmed_at__date__gte=start,
        sale__confirmed_at__date__lte=end,
    )


def _unit_cogs():
    return ExpressionWrapper(F("quantity") * F("unit_cost"), output_field=MONEY)


class ProductReportingService:
    @staticmethod
    def best_sellers(start: date, end: date, limit: int = 20) -> list[dict]:
        rows = (
            _sales(start, end)
            .values("product_id", "product__sku", "product__name", "product__product_type")
            .annotate(
                units_sold=Sum("quantity"), revenue=Sum("line_total"),
                cogs=Sum(_unit_cogs()), order_count=Count("sale_id", distinct=True),
            )
            .order_by("-revenue")[:limit]
        )
        result = []
        for row in rows:
            revenue = q(row["revenue"] or 0)
            cogs = q(row["cogs"] or 0)
            gross_profit = q(revenue - cogs)
            margin = q(gross_profit * 100 / revenue) if revenue else q(0)
            result.append({
                "product_id": row["product_id"], "sku": row["product__sku"],
                "name": row["product__name"], "product_type": row["product__product_type"],
                "units_sold": str(q(row["units_sold"] or 0)),
                "revenue": str(revenue), "cogs": str(cogs),
                "gross_profit": str(gross_profit), "margin_pct": str(margin),
                "order_count": row["order_count"],
            })
        return result

    @staticmethod
    def worst_sellers(start: date, end: date, limit: int = 20) -> list[dict]:
        rows = ProductReportingService.best_sellers(start, end, limit=10_000)
        return sorted(rows, key=lambda row: Decimal(row["revenue"]))[:limit]

    @staticmethod
    def dead_stock(days_since_last_sale: int = 90, limit: int = 100) -> list[dict]:
        from apps.inventory.models import Product
        from apps.sales.models import SaleItem

        cutoff = date.today() - timedelta(days=days_since_last_sale)
        recently_sold = SaleItem.objects.filter(
            sale__status__in=QUALIFYING_STATUSES,
            sale__confirmed_at__date__gte=cutoff,
        ).values_list("product_id", flat=True)
        value = ExpressionWrapper(F("levels__quantity") * F("cost_price"), output_field=MONEY)
        rows = (
            Product.objects.filter(is_active=True, is_stocked=True)
            .exclude(pk__in=recently_sold)
            .annotate(
                total_quantity=Sum("levels__quantity"),
                stock_value=Sum(value),
            )
            .filter(total_quantity__gt=0)
            .order_by("-stock_value")[:limit]
        )
        return [
            {
                "product_id": product.pk, "sku": product.sku,
                "name": product.name, "brand": product.brand,
                "total_quantity": str(q(product.total_quantity or 0)),
                "stock_value": str(q(product.stock_value or 0)),
                "cost_price": str(q(product.cost_price)),
            }
            for product in rows
        ]

    @staticmethod
    def margin_analysis(start: date, end: date, limit: int = 50) -> list[dict]:
        rows = [
            row for row in ProductReportingService.best_sellers(start, end, limit=10_000)
            if Decimal(row["revenue"]) >= Decimal("100")
        ]
        return sorted(rows, key=lambda row: Decimal(row["margin_pct"]), reverse=True)[:limit]
