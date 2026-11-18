"""Single-call dashboard aggregation for the boss's overview screen."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.utils import timezone

from core.utils.money import q


class DashboardService:
    @staticmethod
    def build() -> dict:
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
            "trends": {"last_7_days": SalesReportingService.last_7_days()},
            "position": {
                "ar_total": str(q(ar_total)),
                "cash_position_today": str(cash_position),
            },
        }
