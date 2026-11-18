from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_etims_outbox(self, limit: int = 25) -> dict:
    """
    Worker tick — process queued / retryable eTIMS submissions.
    Wire in Celery beat: every 2 minutes.
    """
    from apps.etims.services import ETIMSService

    try:
        return ETIMSService.process_queued(limit=limit)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def sync_etims_codes() -> dict:
    """Refresh KRA code lists + item classification cache."""
    from apps.etims.services.client import EtimsClient
    from apps.etims.models import EtimsConfig

    config = EtimsConfig.get_solo()
    if not config.cmc_key:
        return {"ok": False, "reason": "not initialised"}
    client = EtimsClient(config)
    codes = client.select_code_list()
    items = client.select_item_cls_list()
    from django.utils import timezone
    config.last_code_sync_at = timezone.now()
    config.save(update_fields=["last_code_sync_at"])
    return {"ok": True, "codes": len(codes or {}), "item_classes": len(items or {})}