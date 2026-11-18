"""P&L aggregation: revenue, COGS, refunds, expenses, and margins."""
from datetime import date
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from core.utils.money import q
from .date_utils import previous_period


MONEY = DecimalField(max_digits=14, decimal_places=2)
QUALIFYING_STATUSES = ["CONFIRMED", "PAID", "PARTIAL", "INVOICED"]


def _sum(queryset, expression) -> Decimal:
    return q(queryset.aggregate(total=Sum(expression))["total"] or 0)


def _cogs_expression():
    return ExpressionWrapper(F("quantity") * F("unit_cost"), output_field=MONEY)


class ProfitReportingService:
    @staticmethod
    def period_pnl(start: date, end: date) -> dict:
        from apps.expenses.models import Expense
        from apps.sales.models import SaleItem, SalesReturnItem

        sales = SaleItem.objects.filter(
            sale__status__in=QUALIFYING_STATUSES,
            sale__confirmed_at__date__gte=start,
            sale__confirmed_at__date__lte=end,
        )
        gross_revenue = _sum(sales, "line_total")
        gross_cogs = _sum(sales, _cogs_expression())

        returns = SalesReturnItem.objects.filter(
            sales_return__status="COMPLETED",
            sales_return__created_at__date__gte=start,
            sales_return__created_at__date__lte=end,
        )
        refund_revenue = _sum(
            returns,
            ExpressionWrapper(F("quantity") * F("unit_price"), output_field=MONEY),
        )
        refund_cogs = _sum(
            returns,
            ExpressionWrapper(F("quantity") * F("sale_item__unit_cost"), output_field=MONEY),
        )
        expenses = q(Expense.objects.filter(
            expense_date__gte=start, expense_date__lte=end,
        ).aggregate(total=Sum("amount"))["total"] or 0)

        net_revenue = q(gross_revenue - refund_revenue)
        net_cogs = q(gross_cogs - refund_cogs)
        gross_profit = q(net_revenue - net_cogs)
        net_profit = q(gross_profit - expenses)

        def margin(amount, denominator):
            return str(q(amount * Decimal("100") / denominator)) if denominator else "0.00"

        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "revenue": {
                "gross": str(gross_revenue),
                "refunds": str(refund_revenue),
                "net": str(net_revenue),
            },
            "cogs": {
                "gross": str(gross_cogs),
                "returned": str(refund_cogs),
                "net": str(net_cogs),
            },
            "gross_profit": str(gross_profit),
            "gross_margin_pct": margin(gross_profit, net_revenue),
            "expenses": str(expenses),
            "net_profit": str(net_profit),
            "net_margin_pct": margin(net_profit, net_revenue),
        }

    @staticmethod
    def period_pnl_with_comparison(start: date, end: date) -> dict:
        prior_start, prior_end = previous_period(start, end)
        current = ProfitReportingService.period_pnl(start, end)
        prior = ProfitReportingService.period_pnl(prior_start, prior_end)

        def delta(current_value, previous_value):
            current_amount = Decimal(current_value)
            previous_amount = Decimal(previous_value)
            if previous_amount == 0:
                return "n/a"
            return str(q((current_amount - previous_amount) * 100 / previous_amount))

        current["comparison"] = {
            "period": prior["period"],
            "revenue_net": prior["revenue"]["net"],
            "gross_profit": prior["gross_profit"],
            "expenses": prior["expenses"],
            "net_profit": prior["net_profit"],
            "revenue_change_pct": delta(current["revenue"]["net"], prior["revenue"]["net"]),
            "gross_profit_change_pct": delta(current["gross_profit"], prior["gross_profit"]),
            "net_profit_change_pct": delta(current["net_profit"], prior["net_profit"]),
        }
        return current

    @staticmethod
    def by_channel(start: date, end: date) -> list[dict]:
        from apps.sales.models import SaleItem

        rows = []
        for channel in ("SHOP", "FIELD"):
            items = SaleItem.objects.filter(
                sale__status__in=QUALIFYING_STATUSES,
                sale__channel=channel,
                sale__confirmed_at__date__gte=start,
                sale__confirmed_at__date__lte=end,
            )
            revenue = _sum(items, "line_total")
            cogs = _sum(items, _cogs_expression())
            gross_profit = q(revenue - cogs)
            margin = q(gross_profit * 100 / revenue) if revenue else q(0)
            rows.append({
                "channel": channel,
                "revenue": str(revenue),
                "cogs": str(cogs),
                "gross_profit": str(gross_profit),
                "margin_pct": str(margin),
            })
        return rows

    @staticmethod
    def by_product_type(start: date, end: date) -> list[dict]:
        from apps.sales.models import SaleItem

        rows = []
        for product_type in ("MOTORBIKE_PART", "AUTO_PART", "ACCESSORY"):
            items = SaleItem.objects.filter(
                sale__status__in=QUALIFYING_STATUSES,
                product__product_type=product_type,
                sale__confirmed_at__date__gte=start,
                sale__confirmed_at__date__lte=end,
            )
            revenue = _sum(items, "line_total")
            cogs = _sum(items, _cogs_expression())
            gross_profit = q(revenue - cogs)
            margin = q(gross_profit * 100 / revenue) if revenue else q(0)
            rows.append({
                "product_type": product_type,
                "revenue": str(revenue),
                "cogs": str(cogs),
                "gross_profit": str(gross_profit),
                "margin_pct": str(margin),
            })
        return rows
