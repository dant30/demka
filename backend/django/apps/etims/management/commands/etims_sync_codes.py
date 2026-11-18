from django.core.management.base import BaseCommand

from apps.etims.models import EtimsConfig
from apps.etims.services.client import EtimsClient, EtimsError


class Command(BaseCommand):
    help = "Fetch KRA code lists and item classifications."

    def handle(self, *args, **options):
        cfg = EtimsConfig.get_solo()
        if not cfg.cmc_key:
            raise SystemExit("Device not initialised. Run etims_init_device first.")
        try:
            client = EtimsClient(cfg)
            codes = client.select_code_list()
            items = client.select_item_cls_list()
        except EtimsError as exc:
            raise SystemExit(str(exc))

        from django.utils import timezone
        cfg.last_code_sync_at = timezone.now()
        cfg.save(update_fields=["last_code_sync_at"])
        self.stdout.write(self.style.SUCCESS(
            f"Codes synced. taxTypes={len(codes.get('taxTyList', []))} "
            f"itemClasses={len(items.get('itemClsList', []))}",
        ))