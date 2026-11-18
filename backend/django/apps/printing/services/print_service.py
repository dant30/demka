"""
Print service — queue, render, dispatch.

`queue_*` methods create PrintJob rows with pre-rendered escpos_data.
`dispatch` hands a job to its printer via connector_for().
The Celery task `process_print_queue` walks the queue and dispatches.
"""
from __future__ import annotations

import base64
import logging

from django.db import transaction
from django.utils import timezone

from core.exceptions.domain import (
    ConflictError,
    NotFoundError,
    ValidationError,
)

from ..models import Printer, PrintJob
from .connectors import ConnectorError, connector_for
from .escpos_renderer import (
    render_credit_note,
    render_preorder_slip,
    render_route_sheet,
    render_sale_receipt,
    render_test_slip,
)

logger = logging.getLogger(__name__)


class PrintService:

    # ---- Queue builders -------------------------------------
    @classmethod
    @transaction.atomic
    def queue_receipt(cls, *, sale_id: int, user) -> PrintJob:
        from apps.sales.services import SaleService

        payload = SaleService.receipt_payload(sale_id)
        printer = cls._pick_printer(
            location_id=payload.get("sale", {}).get("location_id"),
            user=user,
            document_type=PrintJob.DocumentType.RECEIPT,
        )
        escpos = render_sale_receipt(
            payload, paper_width_mm=printer.paper_width_mm if printer else 58,
        )
        return cls._enqueue(
            printer=printer,
            document_type=PrintJob.DocumentType.RECEIPT,
            reference_type="Sale",
            reference_id=payload["sale"]["sale_number"],
            payload=payload,
            escpos=escpos,
            user=user,
        )

    @classmethod
    @transaction.atomic
    def queue_credit_note(cls, *, sales_return_id: int, user) -> PrintJob:
        from apps.sales.models import SalesReturn
        from apps.sales.services import SaleService
        from apps.common.models import BusinessConfiguration

        ret = (
            SalesReturn.objects
            .select_related("original_sale", "customer", "refund_method")
            .prefetch_related("items__product")
            .filter(pk=sales_return_id)
            .first()
        )
        if not ret:
            raise NotFoundError("SalesReturn", sales_return_id)

        cfg = BusinessConfiguration.get_solo()
        payload = {
            "business": {
                "name": cfg.business_name,
                "kra_pin": cfg.kra_pin,
                "address": cfg.address,
                "phone": cfg.phone,
                "receipt_footer": cfg.receipt_footer,
            },
            "sales_return": {
                "return_number": ret.return_number,
                "customer_name": ret.customer.name,
                "reason": ret.reason,
                "refund_amount": str(ret.refund_amount),
                "refund_method_code": ret.refund_method.code if ret.refund_method else "",
                "created_at": ret.created_at.isoformat(),
            },
            "original_sale": {
                "sale_number": ret.original_sale.sale_number,
            },
            "items": [
                {
                    "name": it.product.name,
                    "quantity": str(it.quantity),
                    "line_total": str((it.quantity * it.unit_price).quantize(
                        __import__("decimal").Decimal("0.01")
                    )),
                }
                for it in ret.items.all()
            ],
        }

        printer = cls._pick_printer(
            location_id=ret.original_sale.location_id,
            user=user,
            document_type=PrintJob.DocumentType.CREDIT_NOTE,
        )
        escpos = render_credit_note(
            payload, paper_width_mm=printer.paper_width_mm if printer else 58,
        )
        return cls._enqueue(
            printer=printer,
            document_type=PrintJob.DocumentType.CREDIT_NOTE,
            reference_type="SalesReturn",
            reference_id=ret.return_number,
            payload=payload,
            escpos=escpos,
            user=user,
        )

    @classmethod
    @transaction.atomic
    def queue_preorder_slip(cls, *, preorder_id: int, user) -> PrintJob:
        from apps.preorders.models import Preorder
        from apps.common.models import BusinessConfiguration

        pre = (
            Preorder.objects
            .select_related("customer")
            .prefetch_related("items__product")
            .filter(pk=preorder_id)
            .first()
        )
        if not pre:
            raise NotFoundError("Preorder", preorder_id)

        cfg = BusinessConfiguration.get_solo()
        payload = {
            "business": {
                "name": cfg.business_name,
                "address": cfg.address,
                "phone": cfg.phone,
            },
            "preorder": {
                "preorder_number": pre.preorder_number,
                "customer_name": pre.customer.name,
                "preferred_pickup_date": pre.preferred_pickup_date,
                "total_estimated": str(pre.total_estimated),
                "created_at": pre.created_at.isoformat(),
            },
            "items": [
                {
                    "product_name": it.product.name,
                    "quantity": str(it.quantity),
                    "line_total": str(it.line_total),
                }
                for it in pre.items.all()
            ],
        }
        printer = cls._pick_printer(
            location_id=None, user=user,
            document_type=PrintJob.DocumentType.PREORDER_SLIP,
        )
        escpos = render_preorder_slip(
            payload, paper_width_mm=printer.paper_width_mm if printer else 58,
        )
        return cls._enqueue(
            printer=printer,
            document_type=PrintJob.DocumentType.PREORDER_SLIP,
            reference_type="Preorder",
            reference_id=pre.preorder_number,
            payload=payload,
            escpos=escpos,
            user=user,
        )

    @classmethod
    @transaction.atomic
    def queue_route_sheet(cls, *, run_id: int, user) -> PrintJob:
        from apps.routes.models import RouteRun
        from apps.routes.services import RouteService
        from apps.common.models import BusinessConfiguration

        run = (
            RouteRun.objects
            .select_related("route", "agent", "stock_location")
            .filter(pk=run_id)
            .first()
        )
        if not run:
            raise NotFoundError("RouteRun", run_id)

        customers = RouteService.customers_with_debt()  # placeholder for "route customers"
        cfg = BusinessConfiguration.get_solo()
        payload = {
            "business": {"name": cfg.business_name},
            "run": {
                "route_name": run.route.name,
                "run_date": str(run.run_date),
                "agent_name": run.agent.get_full_name() or run.agent.username,
                "stock_location": run.stock_location.name,
            },
            "customers": [
                {"name": c.name, "phone": c.phone} for c in customers[:50]
            ],
        }
        printer = cls._pick_printer(
            location_id=run.stock_location_id, user=user,
            document_type=PrintJob.DocumentType.ROUTE_SHEET,
        )
        escpos = render_route_sheet(
            payload, paper_width_mm=printer.paper_width_mm if printer else 80,
        )
        return cls._enqueue(
            printer=printer,
            document_type=PrintJob.DocumentType.ROUTE_SHEET,
            reference_type="RouteRun",
            reference_id=str(run.pk),
            payload=payload,
            escpos=escpos,
            user=user,
        )

    @classmethod
    def queue_test_print(cls, *, printer_id: int, user) -> PrintJob:
        printer = Printer.objects.filter(pk=printer_id, is_active=True).first()
        if not printer:
            raise NotFoundError("Printer", printer_id)
        escpos = render_test_slip(printer.name, paper_width_mm=printer.paper_width_mm)
        return cls._enqueue(
            printer=printer,
            document_type=PrintJob.DocumentType.TEST,
            reference_type="Printer",
            reference_id=str(printer.pk),
            payload={"printer": printer.name, "transport": printer.transport_summary()},
            escpos=escpos,
            user=user,
        )

    # ---- Internal helpers -----------------------------------
    @staticmethod
    def _enqueue(*, printer, document_type, reference_type, reference_id,
                 payload, escpos, user) -> PrintJob:
        return PrintJob.objects.create(
            printer=printer,
            document_type=document_type,
            reference_type=reference_type,
            reference_id=reference_id,
            payload=payload,
            escpos_data=escpos,
            created_by=user if user and getattr(user, "is_authenticated", False) else None,
        )

    @staticmethod
    def _pick_printer(*, location_id, user, document_type) -> Printer | None:
        """
        Priority:
          1. Printer assigned to the given location (shop / van).
          2. Printer assigned to the requesting user.
          3. The default printer.
        """
        qs = Printer.objects.filter(is_active=True)

        if location_id:
            p = qs.filter(assigned_location_id=location_id).first()
            if p:
                return p

        if user and getattr(user, "is_authenticated", False):
            p = qs.filter(assigned_user_id=user.id).first()
            if p:
                return p

        return qs.filter(is_default=True).first()

    # ---- Dispatch -------------------------------------------
    @classmethod
    def dispatch(cls, job_id: int) -> PrintJob:
        """
        Send a single job to its printer. Marks PRINTED on success, FAILED on error.
        Thread-safe via select_for_update on the PrintJob row.
        """
        from django.db import transaction

        with transaction.atomic():
            job = (
                PrintJob.objects
                .select_for_update(of=("self",))
                .select_related("printer")
                .filter(pk=job_id)
                .first()
            )
            if not job:
                raise NotFoundError("PrintJob", job_id)
            if job.status not in (PrintJob.Status.QUEUED, PrintJob.Status.FAILED):
                return job  # already processed
            if not job.printer:
                job.status = PrintJob.Status.FAILED
                job.error_message = "No printer assigned to job."
                job.save(update_fields=["status", "error_message"])
                return job
            if not job.escpos_data:
                job.status = PrintJob.Status.FAILED
                job.error_message = "Job has no rendered ESC/POS payload."
                job.save(update_fields=["status", "error_message"])
                return job

            job.status = PrintJob.Status.PRINTING
            job.attempts += 1
            job.last_attempt_at = timezone.now()
            job.save(update_fields=["status", "attempts", "last_attempt_at"])

            try:
                with connector_for(job.printer) as conn:
                    conn.write(bytes(job.escpos_data))
            except ConnectorError as exc:
                job.status = PrintJob.Status.FAILED
                job.error_message = str(exc)[:2000]
                job.save(update_fields=["status", "error_message"])
                logger.warning("PrintJob #%s failed: %s", job.pk, exc)
                return job
            except Exception as exc:
                job.status = PrintJob.Status.FAILED
                job.error_message = f"Unexpected: {exc}"[:2000]
                job.save(update_fields=["status", "error_message"])
                logger.exception("PrintJob #%s unexpected failure", job.pk)
                return job

            job.status = PrintJob.Status.PRINTED
            job.printed_at = timezone.now()
            job.error_message = ""
            job.save(update_fields=["status", "printed_at", "error_message"])
            return job

    # ---- Client-side helpers (Web Bluetooth) ---------------
    @staticmethod
    def base64_payload(job_id: int) -> dict:
        """
        Return the rendered ESC/POS bytes as base64 so the React app can push
        them to a Bluetooth printer via the Web Bluetooth API.
        """
        job = PrintJob.objects.filter(pk=job_id).first()
        if not job:
            raise NotFoundError("PrintJob", job_id)
        if not job.escpos_data:
            raise ValidationError("Job has no rendered payload.")
        return {
            "job_id": job.pk,
            "document_type": job.document_type,
            "escpos_base64": base64.b64encode(bytes(job.escpos_data)).decode(),
            "bytes_length": len(bytes(job.escpos_data)),
        }

    @staticmethod
    def mark_printed_by_client(job_id: int, *, user) -> PrintJob:
        """Called by the frontend after Web Bluetooth printing succeeds."""
        job = PrintJob.objects.filter(pk=job_id).first()
        if not job:
            raise NotFoundError("PrintJob", job_id)
        if job.status == PrintJob.Status.PRINTED:
            return job
        job.status = PrintJob.Status.PRINTED
        job.printed_at = timezone.now()
        job.error_message = ""
        job.attempts += 1
        job.last_attempt_at = timezone.now()
        job.save(update_fields=[
            "status", "printed_at", "error_message", "attempts", "last_attempt_at",
        ])
        return job

    @staticmethod
    def mark_failed_by_client(job_id: int, *, user, error: str) -> PrintJob:
        job = PrintJob.objects.filter(pk=job_id).first()
        if not job:
            raise NotFoundError("PrintJob", job_id)
        job.status = PrintJob.Status.FAILED
        job.error_message = (error or "Client reported failure")[:2000]
        job.attempts += 1
        job.last_attempt_at = timezone.now()
        job.save(update_fields=[
            "status", "error_message", "attempts", "last_attempt_at",
        ])
        return job

    @staticmethod
    def retry(job_id: int, user) -> PrintJob:
        job = PrintJob.objects.filter(pk=job_id).first()
        if not job:
            raise NotFoundError("PrintJob", job_id)
        if job.status not in (PrintJob.Status.FAILED, PrintJob.Status.CANCELLED):
            raise ConflictError(
                f"Cannot retry a job in status {job.status}."
            )
        job.status = PrintJob.Status.QUEUED
        job.error_message = ""
        job.save(update_fields=["status", "error_message"])
        return job

    @staticmethod
    def cancel(job_id: int, user) -> PrintJob:
        job = PrintJob.objects.filter(pk=job_id).first()
        if not job:
            raise NotFoundError("PrintJob", job_id)
        if job.status == PrintJob.Status.PRINTED:
            raise ConflictError("Cannot cancel a printed job.")
        job.status = PrintJob.Status.CANCELLED
        job.save(update_fields=["status"])
        return job