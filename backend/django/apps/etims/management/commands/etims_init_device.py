from django.core.management.base import BaseCommand, CommandError

from apps.etims.models import EtimsConfig
from apps.etims.services.client import EtimsClient, EtimsError


class Command(BaseCommand):
    help = "Initialise the eTIMS device with KRA and persist the cmcKey."

    def handle(self, *args, **options):
        cfg = EtimsConfig.get_solo()
        if not cfg.tin or not cfg.device_serial:
            raise CommandError("Set tin and device_serial on EtimsConfig first.")

        self.stdout.write(f"Initialising {cfg.tin}/{cfg.bhf_id} @ {cfg.environment} …")
        try:
            info = EtimsClient(cfg).initialize_device()
        except EtimsError as exc:
            raise CommandError(str(exc))

        from django.utils import timezone
        cfg.cmc_key = info.get("cmcKey", "")
        cfg.sdc_id = info.get("sdcId", "")
        cfg.mrc_no = info.get("mrcNo", "")
        cfg.trade_name = info.get("tradeNm", "")
        cfg.branch_name = info.get("bhfNm", "")
        cfg.initialized_at = timezone.now()
        cfg.save()

        self.stdout.write(self.style.SUCCESS(
            f"OK — trade_name={cfg.trade_name} sdcId={cfg.sdc_id}",
        ))