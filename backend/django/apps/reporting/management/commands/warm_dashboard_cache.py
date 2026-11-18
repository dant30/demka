from django.core.cache import cache
from django.core.management.base import BaseCommand

from apps.reporting.services.dashboard_service import DashboardService


class Command(BaseCommand):
    help = "Pre-warm the reporting dashboard cache."

    def handle(self, *args, **options):
        payload = DashboardService.build()
        cache.set("reporting:dashboard:v1", payload, timeout=300)
        self.stdout.write(self.style.SUCCESS(
            f"Dashboard warmed: {len(payload)} sections cached for 5 minutes."
        ))
