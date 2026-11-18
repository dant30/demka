from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=2, default_retry_delay=15)
def process_print_queue(self, limit: int = 20) -> dict:
    """
    Walk the queue and dispatch up to `limit` QUEUED jobs.
    Wire in Celery beat: every 30 seconds.
    """
    from .models import PrintJob
    from .services import PrintService

    qs = (
        PrintJob.objects
        .filter(status=PrintJob.Status.QUEUED)
        .select_related("printer")
        .order_by("created_at")[:limit]
    )
    printed, failed = 0, 0
    for job in qs:
        result = PrintService.dispatch(job.pk)
        if result.status == PrintJob.Status.PRINTED:
            printed += 1
        else:
            failed += 1
    return {"printed": printed, "failed": failed}


@shared_task
def cleanup_old_print_jobs(days: int = 30) -> dict:
    """Purge PRINTED jobs older than `days`. Keeps FAILED for 90 days for debugging."""
    from datetime import timedelta
    from .models import PrintJob

    cutoff_printed = timezone.now() - timedelta(days=days)
    cutoff_failed = timezone.now() - timedelta(days=90)

    deleted_printed, _ = PrintJob.objects.filter(
        status=PrintJob.Status.PRINTED, created_at__lt=cutoff_printed,
    ).delete()
    deleted_failed, _ = PrintJob.objects.filter(
        status=PrintJob.Status.FAILED, created_at__lt=cutoff_failed,
    ).delete()
    return {"deleted_printed": deleted_printed, "deleted_failed": deleted_failed}