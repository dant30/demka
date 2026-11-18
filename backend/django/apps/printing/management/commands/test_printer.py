from django.core.management.base import BaseCommand, CommandError

from apps.printing.models import Printer
from apps.printing.services import PrintService


class Command(BaseCommand):
    help = "Send a test print to a printer (by name or ID)."

    def add_arguments(self, parser):
        parser.add_argument("printer", help="Printer name or ID.")
        parser.add_argument("--no-dispatch", action="store_true",
                            help="Queue only; do not send immediately.")

    def handle(self, *args, **options):
        ident = options["printer"]
        if ident.isdigit():
            printer = Printer.objects.filter(pk=int(ident), is_active=True).first()
        else:
            printer = Printer.objects.filter(name=ident, is_active=True).first()
        if not printer:
            raise CommandError(f"Printer not found: {ident}")

        self.stdout.write(f"Queuing test print to '{printer.name}' ({printer.transport_summary()}) …")
        job = PrintService.queue_test_print(printer_id=printer.pk, user=None)

        if options["no_dispatch"]:
            self.stdout.write(self.style.SUCCESS(f"Job #{job.pk} queued."))
            return

        result = PrintService.dispatch(job.pk)
        if result.status == "PRINTED":
            self.stdout.write(self.style.SUCCESS("Printed successfully."))
        else:
            self.stdout.write(self.style.ERROR(f"Failed: {result.error_message}"))