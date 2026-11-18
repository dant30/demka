"""Route configuration — CRUD, agent changes, deactivation, schedule management."""
from django.db import transaction
from django.utils import timezone

from core.exceptions.domain import ConflictError, NotFoundError, ValidationError


class RouteService:

    # ---- Create / update ----------------------------------
    @staticmethod
    @transaction.atomic
    def create(data: dict, user) -> "Route":
        from ..models import Route, RouteChangeLog

        route = Route.objects.create(
            name=data["name"].strip(),
            code=data["code"].strip().upper(),
            description=data.get("description", "").strip(),
            is_active=data.get("is_active", True),
            default_agent=data.get("default_agent"),
        )

        # Seed schedule if provided
        days = data.get("schedule_days") or []
        if days:
            RouteService.set_schedule(route, days)

        return route

    @staticmethod
    @transaction.atomic
    def update(route_id: int, data: dict, user) -> "Route":
        from ..models import Route

        try:
            route = Route.objects.select_for_update().get(pk=route_id)
        except Route.DoesNotExist:
            raise NotFoundError("Route", route_id)

        for field in ("name", "description"):
            if field in data:
                setattr(route, field, (data[field] or "").strip())

        if "code" in data and data["code"].strip().upper() != route.code:
            new_code = data["code"].strip().upper()
            if Route.objects.filter(code=new_code).exclude(pk=route.pk).exists():
                raise ValidationError("A route with this code already exists.")
            route.code = new_code

        if "is_active" in data:
            route.is_active = bool(data["is_active"])

        if "schedule_days" in data:
            RouteService.set_schedule(route, data["schedule_days"] or [])

        route.save()
        return route

    # ---- Agent change (audited) ---------------------------
    @staticmethod
    @transaction.atomic
    def change_default_agent(route_id: int, new_agent_id: int | None, user, reason: str) -> "Route":
        from apps.accounts.models import User
        from ..models import Route, RouteChangeLog

        if not reason or not reason.strip():
            raise ValidationError("A change reason is required.")

        try:
            route = Route.objects.select_for_update().get(pk=route_id)
        except Route.DoesNotExist:
            raise NotFoundError("Route", route_id)

        if new_agent_id is not None:
            if not User.objects.filter(pk=new_agent_id, is_active=True).exists():
                raise NotFoundError("User", new_agent_id)

        if route.default_agent_id == new_agent_id:
            return route

        previous_agent_id = route.default_agent_id
        route.default_agent_id = new_agent_id
        route.save(update_fields=["default_agent"])

        RouteChangeLog.objects.create(
            route=route,
            change_type=RouteChangeLog.ChangeType.REASSIGN_AGENT,
            previous_agent_id=previous_agent_id,
            new_agent_id=new_agent_id,
            reason=reason.strip(),
            changed_by=user,
        )
        return route

    # ---- Reassign customers (audited) ---------------------
    @staticmethod
    @transaction.atomic
    def reassign_customers(
        route_id: int,
        customer_ids: list[int],
        target_route_id: int,
        user,
        reason: str,
    ) -> dict:
        """
        Move customers from `route_id` to `target_route_id`. Closes the current
        CustomerRouteAssignment row and creates a new one. Logs to RouteChangeLog.
        """
        from apps.customers.models import CustomerRouteAssignment
        from ..models import Route, RouteChangeLog

        if not reason or not reason.strip():
            raise ValidationError("A reassignment reason is required.")
        if not customer_ids:
            raise ValidationError("At least one customer must be provided.")

        try:
            source = Route.objects.select_for_update().get(pk=route_id)
            target = Route.objects.select_for_update().get(pk=target_route_id)
        except Route.DoesNotExist as exc:
            raise NotFoundError("Route", str(exc))
        if source.pk == target.pk:
            raise ValidationError("Source and target routes must differ.")
        if not target.is_active:
            raise ValidationError("Target route is inactive.")

        today = timezone.now().date()
        moved = 0
        for cid in customer_ids:
            assignments = CustomerRouteAssignment.objects.filter(
                customer_id=cid,
                route=source,
                assigned_to__isnull=True,
            )
            if not assignments.exists():
                continue
            assignments.update(assigned_to=today, reason=reason.strip())
            CustomerRouteAssignment.objects.create(
                customer_id=cid,
                route=target,
                assigned_from=today,
                reason=reason.strip(),
            )
            moved += 1

        RouteChangeLog.objects.create(
            route=source,
            change_type=RouteChangeLog.ChangeType.REASSIGN_CUSTOMER,
            affected_customers=customer_ids,
            reason=reason.strip(),
            changed_by=user,
        )
        return {"moved": moved, "from_route": source.pk, "to_route": target.pk}

    # ---- Deactivate (audited) -----------------------------
    @staticmethod
    @transaction.atomic
    def deactivate(route_id: int, user, reason: str) -> "Route":
        from ..models import Route, RouteChangeLog

        if not reason or not reason.strip():
            raise ValidationError("A deactivation reason is required.")

        try:
            route = Route.objects.select_for_update().get(pk=route_id)
        except Route.DoesNotExist:
            raise NotFoundError("Route", route_id)

        if not route.is_active:
            return route

        # Refuse if there are open runs
        open_runs = route.runs.filter(
            status__in=["PLANNED", "IN_PROGRESS"],
        ).count()
        if open_runs:
            raise ConflictError(
                f"Route has {open_runs} open run(s). Cancel or complete them first."
            )

        route.is_active = False
        route.save(update_fields=["is_active"])

        RouteChangeLog.objects.create(
            route=route,
            change_type=RouteChangeLog.ChangeType.DEACTIVATE,
            reason=reason.strip(),
            changed_by=user,
        )
        return route

    # ---- Schedule -----------------------------------------
    @staticmethod
    @transaction.atomic
    def set_schedule(route, days: list[int]) -> None:
        """Replace the route's schedule with the given day-of-week set (0=Mon..6=Sun)."""
        from ..models import RouteSchedule

        days = sorted(set(int(d) for d in days))
        for d in days:
            if d < 0 or d > 6:
                raise ValidationError(f"Invalid day_of_week: {d}")
        RouteSchedule.objects.filter(route=route).delete()
        RouteSchedule.objects.bulk_create([
            RouteSchedule(route=route, day_of_week=d, is_active=True) for d in days
        ])

    @staticmethod
    def today_routes(today=None) -> list:
        """Active routes scheduled for the given date (defaults to today)."""
        from ..models import Route

        today = today or timezone.now().date()
        dow = today.weekday()
        return list(
            Route.objects
            .filter(
                is_active=True,
                schedules__day_of_week=dow,
                schedules__is_active=True,
            )
            .distinct()
        )