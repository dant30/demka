"""Date period helpers for reporting."""
from datetime import date, timedelta


def today() -> date:
    return date.today()


def start_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def start_of_month(d: date) -> date:
    return d.replace(day=1)


def start_of_quarter(d: date) -> date:
    q = (d.month - 1) // 3
    return d.replace(month=q * 3 + 1, day=1)


def start_of_year(d: date) -> date:
    return d.replace(month=1, day=1)


def get_period_range(period: str, anchor: date | None = None) -> tuple[date, date]:
    """Return (start, end) inclusive for 'daily'|'weekly'|'monthly'|'quarterly'|'yearly'."""
    anchor = anchor or today()

    if period == "daily":
        return anchor, anchor

    if period == "weekly":
        start = start_of_week(anchor)
        return start, start + timedelta(days=6)

    if period == "monthly":
        start = start_of_month(anchor)
        nxt = start.replace(year=start.year + 1, month=1) if start.month == 12 \
            else start.replace(month=start.month + 1)
        return start, nxt - timedelta(days=1)

    if period == "quarterly":
        start = start_of_quarter(anchor)
        m = start.month + 3
        y = start.year + (m - 1) // 12
        m = (m - 1) % 12 + 1
        nxt = start.replace(year=y, month=m)
        return start, nxt - timedelta(days=1)

    if period == "yearly":
        start = start_of_year(anchor)
        return start, start.replace(month=12, day=31)

    raise ValueError(f"Unknown period: {period}")