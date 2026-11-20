"""Single-call dashboard aggregation for the boss's overview screen."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.utils import timezone

from core.utils.money import q


class DashboardService:
    @staticmethod
    def build(start=None, end=None) -> dict:
        from apps.customers.models import Customer
        from apps.etims.models import EtimsInvoice
        from apps.expenses.models import Expense
        from apps.inventory.models import StockLevel
        from apps.payments.models import Payment
        from apps.preorders.models import Preorder
        from apps.sales.models import Sale

        from .profit_reporting import ProfitReportingService
        from .sales_reporting import SalesReportingService

        today = timezone.localdate()
        start = start or today
        end = end or today
        month_start = today.replace(day=1)
        sales_today = Sale.objects.filter(
            status__in=["CONFIRMED", "PAID", "PARTIAL", "INVOICED"],
            confirmed_at__date=today,
        )
        sales_agg = sales_today.aggregate(count=Count("id"), revenue=Sum("total"))
        cash_in = Payment.objects.filter(
            status="CONFIRMED", method__code="CASH", received_at__date=today,
        ).aggregate(total=Sum("amount"))["total"] or 0
        cash_out = Expense.objects.filter(
            payment_method__code="CASH", expense_date=today,
        ).aggregate(total=Sum("amount"))["total"] or 0

        today_pnl = ProfitReportingService.period_pnl(today, today)
        mtd_pnl = ProfitReportingService.period_pnl(month_start, today)
        period_pnl = ProfitReportingService.period_pnl(start, end)
        prior_start, prior_end = None, None
        span = (end - start).days + 1
        prior_end = start - timedelta(days=1)
        prior_start = prior_end - timedelta(days=span - 1)
        prior_pnl = ProfitReportingService.period_pnl(prior_start, prior_end)
        previous_month_end = month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)
        if previous_month_start.month == 12:
            next_month_start = previous_month_start.replace(year=previous_month_start.year + 1, month=1)
        else:
            next_month_start = previous_month_start.replace(month=previous_month_start.month + 1)
        comparable_day = min(today.day, (next_month_start - timedelta(days=1)).day)
        previous_mtd_end = previous_month_start.replace(day=comparable_day)
        previous_mtd_pnl = ProfitReportingService.period_pnl(previous_month_start, previous_mtd_end)

        low_stock_count = StockLevel.objects.filter(
            product__is_stocked=True,
            product__is_active=True,
            location__is_active=True,
        ).filter(
            Q(reorder_level__isnull=False, reorder_level__gt=0, quantity__lte=F("reorder_level"))
            | Q(reorder_level__isnull=True, product__reorder_level__gt=0,
                quantity__lte=F("product__reorder_level"))
        ).count()
        etims_failed_count = EtimsInvoice.objects.filter(status__in=["FAILED", "REJECTED"]).count()
        pending_preorders = Preorder.objects.filter(
            status__in=["SUBMITTED", "CONFIRMED", "IN_PREPARATION", "READY"],
        ).count()
        overdue_ar = Sale.objects.filter(
            balance_due__gt=0,
            status__in=["CONFIRMED", "PARTIAL"],
            confirmed_at__date__lt=today - timedelta(days=30),
        ).aggregate(total=Sum("balance_due"))["total"] or 0
        ar_total = Customer.objects.filter(is_active=True).aggregate(
            total=Sum("current_balance"),
        )["total"] or 0
        cash_position = q(Decimal(cash_in) - Decimal(cash_out))

        period_sales = Sale.objects.filter(
            status__in=["CONFIRMED", "PAID", "PARTIAL", "INVOICED"],
            confirmed_at__date__gte=start,
            confirmed_at__date__lte=end,
        )
        period_sales_agg = period_sales.aggregate(
            count=Count("id"),
            revenue=Sum("total"),
        )

        cash_in_period = Payment.objects.filter(
            status="CONFIRMED",
            received_at__date__gte=start,
            received_at__date__lte=end,
        ).aggregate(total=Sum("amount"))["total"] or 0
        expense_period = Expense.objects.filter(
            expense_date__gte=start,
            expense_date__lte=end,
        ).aggregate(total=Sum("amount"))["total"] or 0

        from apps.sales.models import SaleItem
        top_products = list(
            SaleItem.objects.filter(
                sale__status__in=["CONFIRMED", "PAID", "PARTIAL", "INVOICED"],
                sale__confirmed_at__date__gte=start,
                sale__confirmed_at__date__lte=end,
            )
            .values("product_id", "product__name", "product__sku")
            .annotate(
                units_sold=Sum("quantity"),
                revenue=Sum("line_total"),
                gross_profit=Sum(F("line_total") - F("quantity") * F("unit_cost")),
            )
            .order_by("-revenue")[:5]
        )

        branch_rows = list(
            period_sales.values("location_id", "location__name")
            .annotate(sales_count=Count("id"), revenue=Sum("total"))
            .order_by("-revenue")
        )

        from apps.inventory.models import StockLevel
        inventory = StockLevel.objects.filter(location__is_active=True)
        inventory_value = q(
            inventory.aggregate(
                total=Sum(F("quantity") * F("product__cost_price"))
            )["total"] or 0
        )
        inventory_units = q(inventory.aggregate(total=Sum("quantity"))["total"] or 0)
        cogs = period_pnl["cogs"]["net"]
        stock_turnover = "0.00"
        if inventory_value:
            stock_turnover = str(q(Decimal(cogs) / Decimal(inventory_value)))

        from apps.purchasing.models import PurchaseOrder
        outstanding_po = PurchaseOrder.objects.filter(status__in=["SENT", "PARTIAL"])
        supplier_payables = outstanding_po.aggregate(total=Sum("total"))["total"] or 0

        etims_pending = EtimsInvoice.objects.filter(status__in=["PENDING", "QUEUED"]).count()
        etims_submitted = EtimsInvoice.objects.filter(status="SUBMITTED").count()

        def compare_value(current_value, previous_value):
            current_amount = Decimal(str(current_value))
            previous_amount = Decimal(str(previous_value))
            if previous_amount == 0:
                return "n/a"
            return str(q((current_amount - previous_amount) * Decimal("100") / previous_amount))

        current_revenue = period_pnl["revenue"]["net"]
        previous_revenue = prior_pnl["revenue"]["net"]

        return {
            "generated_at": timezone.now().isoformat(),
            "today": {
                "date": today.isoformat(),
                "sales_count": sales_agg["count"] or 0,
                "sales_revenue": str(q(sales_agg["revenue"] or 0)),
                "cash_in": str(q(cash_in)),
                "cash_out": str(q(cash_out)),
                "cash_position": str(cash_position),
                "expenses": today_pnl["expenses"],
                "gross_profit": today_pnl["gross_profit"],
                "net_profit": today_pnl["net_profit"],
            },
            "mtd": {
                "period": mtd_pnl["period"],
                "net_revenue": mtd_pnl["revenue"]["net"],
                "gross_profit": mtd_pnl["gross_profit"],
                "expenses": mtd_pnl["expenses"],
                "net_profit": mtd_pnl["net_profit"],
                "prior_period": {
                    "period": previous_mtd_pnl["period"],
                    "net_profit": previous_mtd_pnl["net_profit"],
                },
            },
            "alerts": {
                "low_stock_count": low_stock_count,
                "etims_failed_count": etims_failed_count,
                "pending_preorders": pending_preorders,
                "overdue_ar_total": str(q(overdue_ar)),
            },
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "sales_count": period_sales_agg["count"] or 0,
                "sales_revenue": str(q(period_sales_agg["revenue"] or 0)),
                "gross_profit": period_pnl["gross_profit"],
                "net_profit": period_pnl["net_profit"],
                "expenses": period_pnl["expenses"],
                "cash_in": str(q(cash_in_period)),
                "cash_out": str(q(expense_period)),
                "comparison": {
                    "period": {"start": prior_start.isoformat(), "end": prior_end.isoformat()},
                    "revenue_change_pct": compare_value(current_revenue, previous_revenue),
                    "gross_profit_change_pct": compare_value(period_pnl["gross_profit"], prior_pnl["gross_profit"]),
                    "net_profit_change_pct": compare_value(period_pnl["net_profit"], prior_pnl["net_profit"]),
                },
            },
            "top_products": [
                {
                    "product_id": row["product_id"],
                    "name": row["product__name"],
                    "sku": row["product__sku"],
                    "units_sold": str(q(row["units_sold"])),
                    "revenue": str(q(row["revenue"])),
                    "gross_profit": str(q(row["gross_profit"])),
                }
                for row in top_products
            ],
            "branch_performance": [
                {
                    "location_id": row["location_id"],
                    "name": row["location__name"],
                    "sales_count": row["sales_count"] or 0,
                    "revenue": str(q(row["revenue"] or 0)),
                }
                for row in branch_rows
            ],
            "payables": {
                "supplier_outstanding": str(q(supplier_payables)),
            },
            "etims": {
                "pending_count": etims_pending,
                "submitted_count": etims_submitted,
                "failed_count": etims_failed_count,
            },
            "inventory": {
                "valuation": str(inventory_value),
                "units": str(inventory_units),
                "stock_turnover": stock_turnover,
            },
            "cash_reconciliation": {
                "cash_in": str(q(cash_in_period)),
                "cash_out": str(q(expense_period)),
                "net_cash": str(q(Decimal(cash_in_period) - Decimal(expense_period))),
            },
            "trends": {"last_7_days": SalesReportingService.last_7_days(), "period": SalesReportingService.by_day(start, end) if span <= 31 else SalesReportingService.last_7_days()},
            "position": {
                "ar_total": str(q(ar_total)),
                "cash_position_today": str(cash_position),
            },
        }
