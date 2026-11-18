from django.core.management.base import BaseCommand

from apps.etims.services import ETIMSService


class Command(BaseCommand):
    help = "Process queued and retryable eTIMS submissions once."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=25)

    def handle(self, *args, **options):
        result = ETIMSService.process_queued(limit=options["limit"])
        self.stdout.write(self.style.SUCCESS(
            f"processed={result['processed']} "
            f"submitted={result['submitted']} "
            f"failed={result['failed']}",
        ))