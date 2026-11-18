"""
Route run lifecycle — PLANNED → IN_PROGRESS → COMPLETED (or CANCELLED).

Snapshots at each transition:
    start()    → opening_stock_value, started_at, started_by
    complete() → closing_stock_value, cash_collected, cash_expected,
                 cash_variance (from cash_handed_in input), completed_at/by
"""
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from core.exceptions.domain import ConflictError, NotFoundError, ValidationError
from core.utils.money import q


class RouteRunService:

    # ---- Create -------------------------------------------
    @staticmethod
    @transaction.atomic
    def create(data: dict, user) -> "RouteRun":
        from apps.accounts.models import User
        from apps.inventory.models import StockLocation
        from ..models import Route, RouteRun

        route = Route.objects.filter(pk=data["route"], is_active=True).first()
        if not route:
            raise NotFoundError("Route", data["route"])

        agent_id = data.get("agent") or route.default_agent_id
        if not agent_id:
            raise ValidationError("Agent is required (route has no default).")
        if not User.objects.filter(pk=agent_id, role="FIELD_AGENT", is_active=True).exists() \
                and not User.objects.filter(pk=agent_id, role__in=("BOSS", "ADMIN"), is_active=True).exists():
            raise ValidationError("Agent must be an active field agent or boss.")

        location = StockLocation.objects.filter(
            pk=data["stock_location"], is_active=True, location_type="FIELD",
        ).first()
        if not location:
            raise ValidationError("stock_location must be an active FIELD location.")

        run_date = data["run_date"]
        if RouteRun.objects.filter(
            route=route, run_date=run_date, status__in=["PLANNED", "IN_PROGRESS"],
        ).exists():
            raise ConflictError(
                f"An open run already exists for {route.code} on {run_date}."
            )

        return RouteRun.objects.create(
            route=route,
            agent_id=agent_id,
            stock_location=location,
            run_date=run_date,
            status=RouteRun.Status.PLANNED,
            notes=(data.get("notes") or "").strip(),
        )

    # ---- Materialize (bulk plan) --------------------------
    @staticmethod
    @transaction.atomic
    def materialize_range(start_date, end_date) -> list:
        """
        For every active route scheduled on each day in the range, create a
        PLANNED run if one doesn't already exist. Assigns route.default_agent
        and a FIELD StockLocation whose assigned_agent matches (fallback to any
        active FIELD location).
        """
        from apps.inventory.models import StockLocation
        from ..models import Route, RouteRun

        created = []
        d = start_date
        while d <= end_date:
            for route in Route.objects.filter(
                is_active=True,
                schedules__day_of_week=d.weekday(),
                schedules__is_active=True,
            ).distinct():
                agent_id = route.default_agent_id
                if not agent_id:
                    continue
                if RouteRun.objects.filter(
                    route=route, run_date=d, status__in=["PLANNED", "IN_PROGRESS"],
                ).exists():
                    continue
                location = (
                    StockLocation.objects.filter(
                        location_type="FIELD", is_active=True,
                        assigned_agent_id=agent_id,
                    ).first()
                    or StockLocation.objects.filter(
                        location_type="FIELD", is_active=True,
                    ).first()
                )
                if not location:
                    continue
                created.append(RouteRun.objects.create(
                    route=route,
                    agent_id=agent_id,
                    stock_location=location,
                    run_date=d,
                    status=RouteRun.Status.PLANNED,
                    notes="Auto-materialized",
                ))
            d += timedelta(days=1)
        return created

    # ---- Start --------------------------------------------
    @staticmethod
    @transaction.atomic
    def start(run_id: int, user) -> "RouteRun":
        from apps.inventory.models import StockLevel
        from ..models import RouteRun

        try:
            run = RouteRun.objects.select_for_update().select_related(
                "stock_location",
            ).get(pk=run_id)
        except RouteRun.DoesNotExist:
            raise NotFoundError("RouteRun", run_id)

        if run.status != RouteRun.Status.PLANNED:
            raise ConflictError(f"Cannot start a run in status {run.status}.")

        opening_value = Decimal("0")
        levels = StockLevel.objects.filter(location=run.stock_location).select_related("product")
        for lvl in levels:
            opening_value += Decimal(lvl.quantity) * Decimal(lvl.product.cost_price or 0)

        run.status = RouteRun.Status.IN_PROGRESS
        run.started_at = timezone.now()
        run.started_by = user
        run.opening_stock_value = q(opening_value)
        run.save(update_fields=[
            "status", "started_at", "started_by", "opening_stock_value",
        ])
        return run

    # ---- Complete -----------------------------------------
    @staticmethod
    @transaction.atomic
    def complete(run_id: int, user, data: dict) -> "RouteRun":
        from apps.inventory.models import StockLevel
        from apps.payments.models import Payment
        from apps.expenses.models import Expense
        from ..models import RouteRun

        try:
            run = RouteRun.objects.select_for_update().select_related(
                "stock_location", "route",
            ).get(pk=run_id)
        except RouteRun.DoesNotExist:
            raise NotFoundError("RouteRun", run_id)

        if run.status != RouteRun.Status.IN_PROGRESS:
            raise ConflictError(f"Cannot complete a run in status {run.status}.")

        completed_at = timezone.now()

        # 1) Closing stock value
        closing_value = Decimal("0")
        for lvl in StockLevel.objects.filter(
            location=run.stock_location,
        ).select_related("product"):
            closing_value += Decimal(lvl.quantity) * Decimal(lvl.product.cost_price or 0)

        # 2) Cash collected — CASH payments received during the run window
        cash_payments = (
            Payment.objects
            .filter(
                received_by=run.agent,
                method__code="CASH",
                status="CONFIRMED",
                received_at__gte=run.started_at,
                received_at__lte=completed_at,
            )
            .aggregate(total=Sum("amount"))["total"] or Decimal("0")
        )
        cash_collected = q(cash_payments)

        # 3) Cash expenses on this run
        cash_expenses = (
            Expense.objects
            .filter(route_run=run, payment_method__code="CASH")
            .aggregate(total=Sum("amount"))["total"] or Decimal("0")
        )
        cash_expenses = q(cash_expenses)

        # 4) Expected cash in hand (collected − spent from cash)
        cash_expected = q(cash_collected - cash_expenses)

        # 5) Actual cash handed in (from input)
        cash_handed_in = q(data["cash_handed_in"])
        if cash_handed_in < 0:
            raise ValidationError("cash_handed_in cannot be negative.")

        # 6) Variance (positive = over, negative = short)
        cash_variance = q(cash_handed_in - cash_expected)

        run.status = RouteRun.Status.COMPLETED
        run.completed_at = completed_at
        run.completed_by = user
        run.closing_stock_value = q(closing_value)
        run.cash_collected = cash_collected
        run.cash_expected = cash_expected
        run.cash_handed_in = cash_handed_in
        run.cash_variance = cash_variance
        if data.get("notes"):
            run.notes = (run.notes + "\n" + data["notes"].strip()).strip()

        run.save(update_fields=[
            "status", "completed_at", "completed_by",
            "closing_stock_value", "cash_collected",
            "cash_expected", "cash_handed_in", "cash_variance", "notes",
        ])
        return run

    # ---- Cancel -------------------------------------------
    @staticmethod
    @transaction.atomic
    def cancel(run_id: int, user, reason: str = "") -> "RouteRun":
        from ..models import RouteRun

        try:
            run = RouteRun.objects.select_for_update().get(pk=run_id)
        except RouteRun.DoesNotExist:
            raise NotFoundError("RouteRun", run_id)

        if run.status == RouteRun.Status.COMPLETED:
            raise ConflictError("Cannot cancel a completed run.")
        if run.status == RouteRun.Status.CANCELLED:
            return run

        run.status = RouteRun.Status.CANCELLED
        if reason:
            run.notes = (run.notes + f"\nCancelled: {reason.strip()}").strip()
        run.save(update_fields=["status", "notes"])
        return run