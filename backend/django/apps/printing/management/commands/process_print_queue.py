from django.core.management.base import BaseCommand

from apps.printing.tasks import process_print_queue


class Command(BaseCommand):
    help = "Process queued print jobs once."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        result = process_print_queue(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(
            f"printed={result['printed']} failed={result['failed']}",
        ))