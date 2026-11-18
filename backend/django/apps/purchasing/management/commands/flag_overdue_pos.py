from django.core.management.base import BaseCommand

from apps.purchasing.tasks import flag_overdue_pos


class Command(BaseCommand):
    help = "Print POs whose expected_date has passed and are still SENT/PARTIAL."

    def handle(self, *args, **options):
        result = flag_overdue_pos()
        if result["count"] == 0:
            self.stdout.write(self.style.SUCCESS("No overdue purchase orders."))
            return
        self.stdout.write(
            self.style.WARNING(f"{result['count']} overdue PO(s):")
        )
        for po in result["pos"]:
            self.stdout.write(
                f"  {po['po_number']} — {po['supplier__name']} "
                f"(expected {po['expected_date']})"
            )