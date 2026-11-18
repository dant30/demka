"""Route and run profitability reporting."""
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum

from core.exceptions.domain import NotFoundError
from core.utils.money import q


class RouteReportingService:

    # ---- Run reconciliation view --------------------------
    @classmethod
    def run_reconciliation(cls, run_id: int) -> dict:
        from apps.expenses.models import Expense
        from apps.sales.models import Sale, SaleItem
        from ..models import RouteRun

        run = (
            RouteRun.objects
            .select_related("route", "agent", "stock_location")
            .filter(pk=run_id)
            .first()
        )
        if not run:
            raise NotFoundError("RouteRun", run_id)

        # Sales during the run window by this agent
        sales_qs = Sale.objects.filter(
            agent=run.agent,
            channel="FIELD",
            status__in=["CONFIRMED", "PAID", "PARTIAL", "INVOICED"],
        )
        if run.started_at and run.completed_at:
            sales_qs = sales_qs.filter(
                confirmed_at__gte=run.started_at,
                confirmed_at__lte=run.completed_at,
            )
        elif run.started_at:
            sales_qs = sales_qs.filter(confirmed_at__gte=run.started_at)

        sales_total = q(sales_qs.aggregate(t=Sum("total"))["t"] or Decimal("0"))
        sales_count = sales_qs.count()

        # COGS from sale items
        items_qs = SaleItem.objects.filter(sale__in=sales_qs)
        cogs = Decimal("0")
        for it in items_qs.select_related("product"):
            cogs += q(Decimal(it.quantity) * Decimal(it.unit_cost))
        cogs = q(cogs)

        # Expenses on this run
        exp_rows = (
            Expense.objects
            .filter(route_run=run)
            .values("category__id", "category__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        expenses_total = sum((Decimal(r["total"]) for r in exp_rows), Decimal("0"))
        expenses_total = q(expenses_total)

        gross_profit = q(sales_total - cogs)
        net_profit = q(gross_profit - expenses_total)

        # Stock variance
        stock_used = cogs
        expected_closing = q(Decimal(run.opening_stock_value) - stock_used)
        stock_variance = q(Decimal(run.closing_stock_value) - expected_closing)

        return {
            "run_id": run.pk,
            "route": {"id": run.route_id, "code": run.route.code, "name": run.route.name},
            "agent": {
                "id": run.agent_id,
                "name": run.agent.get_full_name() or run.agent.username,
            },
            "stock_location": {"id": run.stock_location_id, "name": run.stock_location.name},
            "run_date": run.run_date,
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "sales": {
                "count": sales_count,
                "total": str(sales_total),
                "cogs": str(cogs),
                "gross_profit": str(gross_profit),
            },
            "expenses": {
                "total": str(expenses_total),
                "by_category": [
                    {
                        "category_id": r["category__id"],
                        "category": r["category__name"],
                        "total": str(q(r["total"])),
                        "count": r["count"],
                    }
                    for r in exp_rows
                ],
            },
            "profit": {
                "gross": str(gross_profit),
                "net": str(net_profit),
            },
            "stock": {
                "opening_value": str(run.opening_stock_value),
                "closing_value": str(run.closing_stock_value),
                "expected_closing": str(expected_closing),
                "variance": str(stock_variance),
            },
            "cash": {
                "collected": str(run.cash_collected),
                "expected": str(run.cash_expected) if run.cash_expected is not None else None,
                "handed_in": str(run.cash_handed_in) if run.cash_handed_in is not None else None,
                "variance": str(run.cash_variance) if run.cash_variance is not None else None,
            },
        }

    # ---- Route profitability over a period ----------------
    @classmethod
    def route_profitability(cls, route_id: int, start: date, end: date) -> dict:
        from apps.expenses.models import Expense
        from apps.sales.models import Sale, SaleItem
        from ..models import Route, RouteRun

        route = Route.objects.filter(pk=route_id).first()
        if not route:
            raise NotFoundError("Route", route_id)

        runs = RouteRun.objects.filter(
            route=route, run_date__gte=start, run_date__lte=end,
        )
        runs_completed = runs.filter(status="COMPLETED")

        sales_qs = Sale.objects.filter(
            route=route, channel="FIELD",
            status__in=["CONFIRMED", "PAID", "PARTIAL", "INVOICED"],
            confirmed_at__date__gte=start,
            confirmed_at__date__lte=end,
        )
        sales_total = q(sales_qs.aggregate(t=Sum("total"))["t"] or Decimal("0"))
        cogs = Decimal("0")
        for it in SaleItem.objects.filter(sale__in=sales_qs).select_related("product"):
            cogs += q(Decimal(it.quantity) * Decimal(it.unit_cost))
        cogs = q(cogs)

        expenses_total = q(
            Expense.objects
            .filter(route_run__in=runs)
            .aggregate(t=Sum("amount"))["t"] or Decimal("0")
        )
        gross = q(sales_total - cogs)
        net = q(gross - expenses_total)

        variance_sum = Decimal("0")
        for r in runs_completed:
            if r.cash_variance is not None:
                variance_sum += Decimal(r.cash_variance)

        return {
            "route": {"id": route.pk, "code": route.code, "name": route.name},
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "runs": {
                "total": runs.count(),
                "completed": runs_completed.count(),
            },
            "sales": {"total": str(sales_total), "cogs": str(cogs)},
            "expenses": str(expenses_total),
            "profit": {"gross": str(gross), "net": str(net)},
            "cash_variance_total": str(q(variance_sum)),
        }

    # ---- Agent performance --------------------------------
    @classmethod
    def agent_performance(cls, agent_id: int, start: date, end: date) -> dict:
        from apps.accounts.models import User
        from apps.sales.models import Sale
        from ..models import RouteRun

        agent = User.objects.filter(pk=agent_id).first()
        if not agent:
            raise NotFoundError("User", agent_id)

        runs = RouteRun.objects.filter(
            agent=agent, run_date__gte=start, run_date__lte=end,
        )
        completed = runs.filter(status="COMPLETED")

        sales_qs = Sale.objects.filter(
            agent=agent, channel="FIELD",
            status__in=["CONFIRMED", "PAID", "PARTIAL", "INVOICED"],
            confirmed_at__date__gte=start,
            confirmed_at__date__lte=end,
        )
        sales_total = q(sales_qs.aggregate(t=Sum("total"))["t"] or Decimal("0"))

        variance_sum = sum(
            (Decimal(r.cash_variance) for r in completed if r.cash_variance is not None),
            Decimal("0"),
        )
        variance_avg = q(variance_sum / completed.count()) if completed.count() else Decimal("0")

        return {
            "agent": {
                "id": agent.pk,
                "name": agent.get_full_name() or agent.username,
                "phone": agent.phone,
            },
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "runs": {
                "total": runs.count(),
                "completed": completed.count(),
            },
            "sales_total": str(sales_total),
            "cash_variance": {
                "total": str(q(variance_sum)),
                "average": str(variance_avg),
            },
        }

    # ---- Variance report (all runs in period) -------------
    @classmethod
    def variance_report(cls, start: date, end: date) -> list[dict]:
        from ..models import RouteRun

        qs = (
            RouteRun.objects
            .filter(run_date__gte=start, run_date__lte=end, status="COMPLETED")
            .select_related("route", "agent")
            .exclude(cash_variance=0)
            .exclude(cash_variance__isnull=True)
        )
        rows = []
        for run in qs.order_by("run_date", "route__code"):
            rows.append({
                "run_id": run.pk,
                "run_date": run.run_date.isoformat(),
                "route": {"id": run.route_id, "code": run.route.code, "name": run.route.name},
                "agent": {
                    "id": run.agent_id,
                    "name": run.agent.get_full_name() or run.agent.username,
                },
                "cash_expected": str(run.cash_expected),
                "cash_handed_in": str(run.cash_handed_in),
                "variance": str(run.cash_variance),
            })
        return rows