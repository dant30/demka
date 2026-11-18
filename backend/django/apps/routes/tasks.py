from datetime import timedelta

from celery import shared_task
from django.utils import timezone


@shared_task
def materialize_upcoming_runs(days_ahead: int = 3) -> dict:
    """
    Scheduled task: materialize PLANNED runs for the next N days from active
    schedules. Run daily at ~6am. Skips days/agents that already have a run.
    """
    from .services import RouteRunService

    start = timezone.now().date()
    end = start + timedelta(days=days_ahead)
    created = RouteRunService.materialize_range(start, end)
    return {"created": len(created), "start": start.isoformat(), "end": end.isoformat()}


@shared_task
def flag_cash_variances(days_back: int = 7) -> dict:
    """
    Sweep recently completed runs and return any with non-zero cash or stock
    variance, so the boss can be notified / reconcile. Wire to daily cron.
    """
    from .services import RouteReportingService

    today = timezone.now().date()
    start = today - timedelta(days=days_back)
    rows = RouteReportingService.variance_report(start, today)
    return {"count": len(rows), "rows": rows}


@shared_task
def send_daily_run_digest() -> dict:
    """
    Morning SMS to each field agent listing today's planned runs.
    Sends at 6:30am via Celery beat.
    """
    from django.contrib.auth import get_user_model
    from core.services.sms import SmsError, SmsService

    from .models import RouteRun

    User = get_user_model()
    today = timezone.now().date()
    runs_today = (
        RouteRun.objects
        .filter(run_date=today, status=RouteRun.Status.PLANNED)
        .select_related("route", "agent")
    )
    per_agent: dict[int, list[str]] = {}
    for run in runs_today:
        per_agent.setdefault(run.agent_id, []).append(f"{run.route.code}:{run.route.name}")

    sent = 0
    for agent_id, route_names in per_agent.items():
        try:
            agent = User.objects.get(pk=agent_id)
        except User.DoesNotExist:
            continue
        if not agent.phone:
            continue
        body = f"DEMKA runs today: {', '.join(route_names)}. Have a good trip."
        try:
            SmsService.send(agent.phone, body)
            sent += 1
        except SmsError:
            pass
    return {"agents_notified": sent, "runs": runs_today.count()}