from django.core.management.base import BaseCommand

from apps.expenses.models import ExpenseCategory


SEEDS = [
    "Fuel",
    "Salary",
    "Rent",
    "Utilities",
    "Transport",
    "Maintenance",
    "Supplies",
    "Bank Charges",
    "Licenses & Fees",
    "Other",
]


class Command(BaseCommand):
    help = "Seed the standard DEMKA expense categories (idempotent)."

    def handle(self, *args, **options):
        created, existing = 0, 0
        for name in SEEDS:
            _, was_created = ExpenseCategory.objects.get_or_create(
                name=name, defaults={"is_active": True},
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  + {name}"))
            else:
                existing += 1
        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created}, already existed {existing}."
        ))