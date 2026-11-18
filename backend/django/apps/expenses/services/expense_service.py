"""Expense recording, validation, and reporting."""
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from core.exceptions.domain import NotFoundError, ValidationError
from core.utils.money import q

from ..models import Expense, ExpenseCategory


class ExpenseService:

    # ---- Create -------------------------------------------
    @classmethod
    @transaction.atomic
    def create(cls, data: dict, user) -> Expense:
        from apps.common.services.numbering import next_number
        from apps.inventory.models import StockLocation
        from apps.payments.models import PaymentMethod
        from apps.routes.models import RouteRun

        category = ExpenseCategory.objects.filter(
            pk=data["category"], is_active=True,
        ).first()
        if not category:
            raise NotFoundError("ExpenseCategory", data["category"])

        method = PaymentMethod.objects.filter(
            pk=data["payment_method"], is_active=True,
        ).first()
        if not method:
            raise NotFoundError("PaymentMethod", data["payment_method"])

        amount = q(data["amount"])
        if amount <= 0:
            raise ValidationError("Expense amount must be positive.")

        expense_date = data["expense_date"]
        if expense_date > timezone.now().date():
            raise ValidationError("Expense date cannot be in the future.")

        location = None
        if data.get("location"):
            location = StockLocation.objects.filter(
                pk=data["location"], is_active=True,
            ).first()
            if not location:
                raise NotFoundError("StockLocation", data["location"])

        route_run = None
        if data.get("route_run"):
            route_run = RouteRun.objects.filter(pk=data["route_run"]).first()
            if not route_run:
                raise NotFoundError("RouteRun", data["route_run"])
            # Field agents can only attach expenses to their own runs
            if (
                getattr(user, "role", None) == "FIELD_AGENT"
                and route_run.agent_id != user.id
            ):
                raise ValidationError(
                    "You can only record expenses against your own route runs."
                )
            if route_run.status == RouteRun.Status.CANCELLED:
                raise ValidationError("Cannot record an expense against a cancelled run.")

        return Expense.objects.create(
            expense_number=next_number("EXPENSE", prefix="EXP-", width=6),
            category=category,
            amount=amount,
            description=(data.get("description") or "").strip(),
            expense_date=expense_date,
            paid_by=user,
            payment_method=method,
            reference=(data.get("reference") or "").strip(),
            receipt_image=data.get("receipt_image"),
            location=location,
            route_run=route_run,
        )

    # ---- Update (boss only, enforced by permission) -------
    @classmethod
    @transaction.atomic
    def update(cls, expense_id: int, data: dict, user) -> Expense:
        from apps.inventory.models import StockLocation
        from apps.payments.models import PaymentMethod
        from apps.routes.models import RouteRun

        try:
            expense = Expense.objects.select_for_update().get(pk=expense_id)
        except Expense.DoesNotExist:
            raise NotFoundError("Expense", expense_id)

        if "category" in data:
            cat = ExpenseCategory.objects.filter(
                pk=data["category"], is_active=True,
            ).first()
            if not cat:
                raise NotFoundError("ExpenseCategory", data["category"])
            expense.category = cat

        if "payment_method" in data:
            method = PaymentMethod.objects.filter(
                pk=data["payment_method"], is_active=True,
            ).first()
            if not method:
                raise NotFoundError("PaymentMethod", data["payment_method"])
            expense.payment_method = method

        if "amount" in data:
            amount = q(data["amount"])
            if amount <= 0:
                raise ValidationError("Expense amount must be positive.")
            expense.amount = amount

        if "expense_date" in data:
            if data["expense_date"] > timezone.now().date():
                raise ValidationError("Expense date cannot be in the future.")
            expense.expense_date = data["expense_date"]

        if "location" in data:
            if data["location"] is None:
                expense.location = None
            else:
                loc = StockLocation.objects.filter(pk=data["location"]).first()
                if not loc:
                    raise NotFoundError("StockLocation", data["location"])
                expense.location = loc

        if "route_run" in data:
            if data["route_run"] is None:
                expense.route_run = None
            else:
                run = RouteRun.objects.filter(pk=data["route_run"]).first()
                if not run:
                    raise NotFoundError("RouteRun", data["route_run"])
                expense.route_run = run

        for field in ("description", "reference"):
            if field in data:
                setattr(expense, field, (data[field] or "").strip())

        if "receipt_image" in data:
            expense.receipt_image = data["receipt_image"]

        expense.save()
        return expense

    # ---- Delete (boss only) -------------------------------
    @classmethod
    @transaction.atomic
    def delete(cls, expense_id: int, user) -> None:
        try:
            expense = Expense.objects.select_for_update().get(pk=expense_id)
        except Expense.DoesNotExist:
            raise NotFoundError("Expense", expense_id)
        expense.delete()

    # ---- Reporting ----------------------------------------
    @classmethod
    def by_category(cls, start, end) -> list[dict]:
        """Total per category in [start, end] (inclusive)."""
        rows = (
            Expense.objects
            .filter(expense_date__gte=start, expense_date__lte=end)
            .values("category__id", "category__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        return [
            {
                "category_id": r["category__id"],
                "category": r["category__name"],
                "total": str(q(r["total"])),
                "count": r["count"],
            }
            for r in rows
        ]

    @classmethod
    def by_location(cls, start, end) -> list[dict]:
        rows = (
            Expense.objects
            .filter(expense_date__gte=start, expense_date__lte=end)
            .values("location__id", "location__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        return [
            {
                "location_id": r["location__id"],
                "location": r["location__name"] or "Unassigned",
                "total": str(q(r["total"])),
                "count": r["count"],
            }
            for r in rows
        ]

    @classmethod
    def by_route_run(cls, route_run_id: int) -> dict:
        """Aggregate expenses tied to a specific route run (trip profitability)."""
        from apps.routes.models import RouteRun

        run = RouteRun.objects.filter(pk=route_run_id).first()
        if not run:
            raise NotFoundError("RouteRun", route_run_id)

        rows = (
            Expense.objects
            .filter(route_run=run)
            .values("category__id", "category__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )
        total = sum(Decimal(r["total"]) for r in rows)

        return {
            "route_run_id": run.pk,
            "route": run.route.name if run.route_id else None,
            "run_date": run.run_date,
            "total_expenses": str(q(total)),
            "by_category": [
                {
                    "category_id": r["category__id"],
                    "category": r["category__name"],
                    "total": str(q(r["total"])),
                    "count": r["count"],
                }
                for r in rows
            ],
        }

    @classmethod
    def summary(cls, start, end) -> dict:
        """Single-call summary for a period — total + breakdowns."""
        qs = Expense.objects.filter(expense_date__gte=start, expense_date__lte=end)
        total = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "total": str(q(total)),
            "count": qs.count(),
            "by_category": cls.by_category(start, end),
            "by_location": cls.by_location(start, end),
        }

    @classmethod
    def monthly_trend(cls, months: int = 6) -> list[dict]:
        """Total expenses per month for the trailing N months."""
        today = timezone.now().date()
        out = []
        for i in range(months - 1, -1, -1):
            # Month i months ago
            anchor = today.replace(day=1)
            for _ in range(i):
                anchor = (anchor - timezone.timedelta(days=1)).replace(day=1)
            start = anchor
            if start.month == 12:
                nxt = start.replace(year=start.year + 1, month=1)
            else:
                nxt = start.replace(month=start.month + 1)
            end = nxt - timezone.timedelta(days=1)

            agg = Expense.objects.filter(
                expense_date__gte=start, expense_date__lte=end,
            ).aggregate(total=Sum("amount"))
            out.append({
                "month": start.strftime("%Y-%m"),
                "label": start.strftime("%b %Y"),
                "total": str(q(agg["total"] or Decimal("0"))),
            })
        return out