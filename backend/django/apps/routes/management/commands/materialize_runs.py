from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.routes.services import RouteRunService


class Command(BaseCommand):
    help = "Materialize PLANNED route runs from schedules for a date range."

    def add_arguments(self, parser):
        parser.add_argument("--start", required=True, help="YYYY-MM-DD")
        parser.add_argument("--end", required=True, help="YYYY-MM-DD")

    def handle(self, *args, **options):
        try:
            start = date.fromisoformat(options["start"])
            end = date.fromisoformat(options["end"])
        except ValueError as exc:
            raise CommandError(f"Invalid date: {exc}")

        if end < start:
            raise CommandError("--end must be on or after --start.")

        created = RouteRunService.materialize_range(start, end)
        if not created:
            self.stdout.write(self.style.SUCCESS("No new runs to create."))
            return
        self.stdout.write(self.style.SUCCESS(f"Created {len(created)} run(s):"))
        for r in created:
            self.stdout.write(
                f"  {r.run_date} — {r.route.code} ({r.agent.username}) @ {r.stock_location.name}"
            )