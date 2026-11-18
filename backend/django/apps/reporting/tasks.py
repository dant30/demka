from celery import shared_task
from django.core.cache import cache


@shared_task
def warm_dashboard_cache() -> dict:
	from .services.dashboard_service import DashboardService

	payload = DashboardService.build()
	cache.set("reporting:dashboard:v1", payload, timeout=300)
	return {"warmed": True, "keys": list(payload.keys())}


@shared_task
def warm_monthly_cache() -> dict:
	from .services.date_utils import trailing_months
	from .services.profit_reporting import ProfitReportingService

	rows = []
	for start, end, label in trailing_months(12):
		row = ProfitReportingService.period_pnl(start, end)
		row["label"] = label
		rows.append(row)
	cache.set("reporting:monthly-pnl:v1", rows, timeout=3600)
	return {"months": len(rows)}