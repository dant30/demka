from django.core.management.base import BaseCommand

from apps.inventory.services import ReorderService


class Command(BaseCommand):
    help = "Print stock levels at or below reorder threshold. Exit code 1 if any found."

    def handle(self, *args, **options):
        low = list(ReorderService.low_stock_levels())
        if not low:
            self.stdout.write(self.style.SUCCESS("All stock levels above reorder thresholds."))
            return

        self.stdout.write(
            self.style.WARNING(f"{len(low)} stock level(s) need attention:\n")
        )
        for level in low:
            self.stdout.write(
                f"  {level.product.sku} {level.product.name} "
                f"@ {level.location.name}: "
                f"{level.quantity} (reorder at {level.effective_reorder_level()})"
            )
        # Non-zero exit for cron/monitoring pickup
        import sys
        sys.exit(1)