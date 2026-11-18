"""eTIMS submission health and recent failures."""
from datetime import date

from django.db.models import Count

from core.utils.money import q


class EtimsReportingService:
    @staticmethod
    def submission_rates(start: date, end: date) -> dict:
        from apps.etims.models import EtimsInvoice

        queryset = EtimsInvoice.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        total = queryset.count()
        by_status = {
            row["status"]: row["count"]
            for row in queryset.values("status").annotate(count=Count("id"))
        }
        submitted = by_status.get("SUBMITTED", 0)
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "total": total,
            "submitted": submitted,
            "failed": by_status.get("FAILED", 0),
            "rejected": by_status.get("REJECTED", 0),
            "pending": by_status.get("PENDING", 0) + by_status.get("QUEUED", 0),
            "success_rate_pct": str(q(submitted * 100 / total)) if total else "0.00",
            "by_status": by_status,
        }

    @staticmethod
    def recent_failures(limit: int = 50) -> list[dict]:
        from apps.etims.models import EtimsInvoice

        safe_limit = max(1, min(int(limit), 500))
        return [
            {
                "id": row.pk,
                "receipt_type": row.receipt_type,
                "invoice_number": row.invoice_number,
                "invc_no": row.invc_no,
                "status": row.status,
                "retry_count": row.retry_count,
                "error_message": row.error_message[:300],
                "created_at": row.created_at.isoformat(),
            }
            for row in EtimsInvoice.objects.filter(status__in=["FAILED", "REJECTED"])
            .order_by("-created_at")[:safe_limit]
        ]
