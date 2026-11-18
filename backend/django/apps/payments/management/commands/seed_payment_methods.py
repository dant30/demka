from django.core.management.base import BaseCommand

from apps.payments.models import PaymentMethod


SEEDS = [
    ("CASH", "Cash", False),
    ("MPESA", "M-Pesa", True),
    ("CREDIT", "Credit", False),
    ("CHEQUE", "Cheque", True),
    ("BANK_TRANSFER", "Bank Transfer", True),
]


class Command(BaseCommand):
    help = "Seed the standard DEMKA payment methods (idempotent)."

    def handle(self, *args, **options):
        for code, name, needs_ref in SEEDS:
            pm, created = PaymentMethod.objects.update_or_create(
                code=code,
                defaults={"name": name, "requires_reference": needs_ref, "is_active": True},
            )
            action = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"  {pm.code} — {pm.name} ({action})"))
        self.stdout.write(self.style.SUCCESS("Done."))