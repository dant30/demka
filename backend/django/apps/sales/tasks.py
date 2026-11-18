from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=120)
def submit_sale_to_etims(self, sale_id: int):
    """
    Submit a sale to KRA eTIMS. Delegates to the etims app.
    The etims app is responsible for idempotency, retries, and status updates.
    """
    from apps.etims.services import ETIMSService

    try:
        ETIMSService.submit_sale(sale_id)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def queue_sale_receipt(sale_id: int, user_id: int | None = None) -> dict:
    """
    Create a PrintJob for a sale receipt. Consumed by the printing app
    which renders ESC/POS and serves it to the client's Bluetooth printer.
    """
    from apps.printing.services import PrintService

    return PrintService.queue_receipt(sale_id=sale_id, user_id=user_id)