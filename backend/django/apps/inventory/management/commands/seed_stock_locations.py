from django.core.management.base import BaseCommand

from apps.inventory.models import StockLocation


SEEDS = (
    ("Main Shop", "SHOP"),
    ("Main Warehouse", "WAREHOUSE"),
)


class Command(BaseCommand):
    help = "Seed standard stock locations (idempotent)."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for name, location_type in SEEDS:
            location, created = StockLocation.objects.update_or_create(
                name=name,
                defaults={
                    "location_type": location_type,
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created_count}, updated {updated_count}."
        ))
