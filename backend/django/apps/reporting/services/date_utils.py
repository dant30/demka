"""Date-range parsing and comparison-period helpers for reports."""
from datetime import date, timedelta

from django.utils import timezone

from core.utils.dates import get_period_range


PERIODS = {"daily", "weekly", "monthly", "quarterly", "yearly"}


def parse_range(request) -> tuple[date, date]:
    """Resolve explicit start/end dates or a named period anchored to today."""
    start_param = request.query_params.get("start")
    end_param = request.query_params.get("end")
    if bool(start_param) != bool(end_param):
        raise ValueError("Both start and end must be provided together.")
    if start_param and end_param:
        try:
            start = date.fromisoformat(start_param)
            end = date.fromisoformat(end_param)
        except ValueError as exc:
            raise ValueError("start and end must use YYYY-MM-DD format.") from exc
        if end < start:
            raise ValueError("end must be on or after start.")
        return start, end

    period = request.query_params.get("period", "monthly")
    if period not in PERIODS:
        raise ValueError(f"period must be one of: {', '.join(sorted(PERIODS))}.")
    return get_period_range(period, timezone.localdate())


def previous_period(start: date, end: date) -> tuple[date, date]:
    """Return the immediately preceding inclusive period of equal duration."""
    span = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    return previous_end - timedelta(days=span - 1), previous_end


def trailing_days(n: int, *, anchor: date | None = None) -> list[tuple[date, str]]:
    anchor = anchor or timezone.localdate()
    return [
        (anchor - timedelta(days=i), (anchor - timedelta(days=i)).strftime("%a %d %b"))
        for i in range(n - 1, -1, -1)
    ]


def trailing_months(n: int, *, anchor: date | None = None) -> list[tuple[date, date, str]]:
    """Return inclusive month boundaries and labels, oldest month first."""
    anchor = anchor or timezone.localdate()
    current = anchor.replace(day=1)
    months = []
    for offset in range(n - 1, -1, -1):
        year = current.year
        month = current.month - offset
        while month <= 0:
            year -= 1
            month += 12
        first = date(year, month, 1)
        if month == 12:
            next_first = date(year + 1, 1, 1)
        else:
            next_first = date(year, month + 1, 1)
        months.append((first, next_first - timedelta(days=1), first.strftime("%b %Y")))
    return months
