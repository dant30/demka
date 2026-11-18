"""
eTIMS submission orchestration — the single public entry point used by the
sales and returns apps.

submit_sale(sale_id)        → idempotent, safe to retry
submit_credit_note(ret_id)  → idempotent, safe to retry
process_queued(limit=25)    → worker tick

The `EtimsInvoice` row IS the outbox. Once queued, the Celery task drives it.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.exceptions.domain import NotFoundError, ValidationError
from core.utils.money import q

from ..models import EtimsConfig, EtimsInvoice, EtimsItem
from .client import EtimsClient, EtimsRejection, EtimsTransientError
from .mapping import PaymentMapper, TaxMapper, UnitMapper
from .qr import build_qr_url
from .sequence import SequenceService

logger = logging.getLogger(__name__)

MAX_RETRIES = 8
BASE_BACKOFF = 30  # seconds


def _dt_kra(dt) -> str:
    return dt.strftime("%Y%m%d%H%M%S")


def _date_kra(d) -> str:
    return d.strftime("%Y%m%d")


def _backoff_seconds(attempt: int) -> int:
    return min(BASE_BACKOFF * (2 ** attempt), 3600)


class ETIMSService:

    # ============================================================
    # Public entry points
    # ============================================================
    @classmethod
    def submit_sale(cls, sale_id: int) -> EtimsInvoice:
        """Called from sales confirmation. Idempotent — returns existing row if submitted."""
        from apps.sales.models import Sale

        sale = (
            Sale.objects
            .select_related("customer", "agent")
            .prefetch_related("items__product", "items__tax_rate_ref", "payments__method")
            .filter(pk=sale_id)
            .first()
        )
        if not sale:
            raise NotFoundError("Sale", sale_id)
        if sale.status not in ("CONFIRMED", "PAID", "PARTIAL", "INVOICED"):
            raise ValidationError(
                f"Cannot submit sale {sale.sale_number} in status {sale.status}.",
            )

        existing = sale.etims_invoices.filter(
            receipt_type=EtimsInvoice.ReceiptType.SALE,
        ).first()
        if existing and existing.status == EtimsInvoice.Status.SUBMITTED:
            return existing

        config = EtimsConfig.get_solo()
        cls._assert_ready(config, sale)

        invoice = existing or EtimsInvoice(
            sale=sale,
            receipt_type=EtimsInvoice.ReceiptType.SALE,
            invoice_number=sale.sale_number,
        )

        with transaction.atomic():
            if invoice.invc_no is None:
                invoice.invc_no = SequenceService.allocate(config.tin, config.bhf_id)
            invoice.status = EtimsInvoice.Status.QUEUED
            invoice.save()

        cls._transmit(invoice)
        return invoice

    @classmethod
    def submit_credit_note(cls, sales_return_id: int) -> EtimsInvoice:
        from apps.sales.models import SalesReturn

        ret = (
            SalesReturn.objects
            .select_related("original_sale", "customer")
            .prefetch_related("items__product", "items__sale_item")
            .filter(pk=sales_return_id)
            .first()
        )
        if not ret:
            raise NotFoundError("SalesReturn", sales_return_id)
        if ret.status != "COMPLETED":
            raise ValidationError(
                f"Cannot submit credit note for return in status {ret.status}.",
            )

        original = (
            ret.original_sale.etims_invoices
            .filter(receipt_type=EtimsInvoice.ReceiptType.SALE,
                    status=EtimsInvoice.Status.SUBMITTED)
            .first()
        )
        if not original or not original.invc_no:
            raise ValidationError(
                "Original sale has no signed eTIMS invoice; a credit note "
                "cannot be raised for it.",
            )

        existing = ret.etims_invoices.filter(
            receipt_type=EtimsInvoice.ReceiptType.CREDIT_NOTE,
        ).first()
        if existing and existing.status == EtimsInvoice.Status.SUBMITTED:
            return existing

        config = EtimsConfig.get_solo()
        cls._assert_ready(config, ret)

        invoice = existing or EtimsInvoice(
            sales_return=ret,
            receipt_type=EtimsInvoice.ReceiptType.CREDIT_NOTE,
            invoice_number=ret.return_number,
            org_invc_no=original.invc_no,
        )

        with transaction.atomic():
            if invoice.invc_no is None:
                invoice.invc_no = SequenceService.allocate(config.tin, config.bhf_id)
            invoice.status = EtimsInvoice.Status.QUEUED
            invoice.save()

        cls._transmit(invoice)
        return invoice

    @classmethod
    def process_queued(cls, limit: int = 25) -> dict:
        """Worker tick — pull QUEUED/FAILED rows due for retry."""
        now = timezone.now()
        candidates = (
            EtimsInvoice.objects
            .filter(status__in=[EtimsInvoice.Status.QUEUED, EtimsInvoice.Status.FAILED])
            .filter(next_retry_at__lte=now)
            .order_by("next_retry_at", "id")[:limit]
        )
        processed, submitted, failed = 0, 0, 0
        for inv in candidates:
            processed += 1
            try:
                cls._transmit(inv)
                inv.refresh_from_db()
                if inv.status == EtimsInvoice.Status.SUBMITTED:
                    submitted += 1
            except Exception:
                failed += 1
        return {"processed": processed, "submitted": submitted, "failed": failed}

    # ============================================================
    # Transmission
    # ============================================================
    @classmethod
    def _transmit(cls, invoice: EtimsInvoice) -> None:
        config = EtimsConfig.get_solo()
        client = EtimsClient(config)

        try:
            payload = (
                cls._build_sale_payload(invoice, config)
                if invoice.receipt_type == EtimsInvoice.ReceiptType.SALE
                else cls._build_credit_note_payload(invoice, config)
            )
        except Exception as exc:
            cls._mark_failed(invoice, str(exc), retryable=False)
            return

        invoice.request_payload = payload
        invoice.last_attempt_at = timezone.now()

        try:
            body = client.save_sale(payload)
        except EtimsRejection as exc:
            invoice.response_payload = exc.raw
            cls._mark_failed(invoice, str(exc), retryable=False)
            return
        except EtimsTransientError as exc:
            cls._mark_failed(invoice, str(exc), retryable=True)
            return

        cls._mark_submitted(invoice, body, config)

    @classmethod
    def _mark_submitted(cls, invoice: EtimsInvoice, body: dict, config: EtimsConfig) -> None:
        data = body.get("data", {}) or {}
        cur = data.get("curRcptNo")
        tot = data.get("totRcptNo")
        signature = data.get("rcptSign", "")
        invoice.cur_rcpt_no = cur
        invoice.tot_rcpt_no = tot
        invoice.cu_invc_no = f"{cur}/{tot}" if cur is not None else ""
        invoice.control_code = data.get("intrlData", "")
        invoice.receipt_signature = signature
        invoice.sdc_date_time = data.get("sdcDateTime", "")
        invoice.qr_code_data = build_qr_url(
            tin=config.tin, bhf_id=config.bhf_id, rcpt_sign=signature,
            sandbox=(config.environment == EtimsConfig.Environment.SANDBOX),
        )
        invoice.response_payload = body
        invoice.status = EtimsInvoice.Status.SUBMITTED
        invoice.submitted_at = timezone.now()
        invoice.next_retry_at = None
        invoice.error_message = ""
        invoice.save()

        # Reflect onto the source
        source = invoice.sale or invoice.sales_return
        if invoice.sale_id:
            invoice.sale.etims_invoice_number = invoice.cu_invc_no
            invoice.sale.etims_status = "SENT"
            invoice.sale.save(update_fields=["etims_invoice_number", "etims_status"])

    @classmethod
    def _mark_failed(cls, invoice: EtimsInvoice, message: str, *, retryable: bool) -> None:
        invoice.retry_count += 1
        invoice.error_message = message[:2000]
        if retryable and invoice.retry_count < MAX_RETRIES:
            invoice.status = EtimsInvoice.Status.FAILED
            invoice.next_retry_at = timezone.now() + timedelta(
                seconds=_backoff_seconds(invoice.retry_count),
            )
        elif retryable:
            invoice.status = EtimsInvoice.Status.FAILED
            invoice.next_retry_at = None
        else:
            invoice.status = EtimsInvoice.Status.REJECTED
            invoice.next_retry_at = None
        invoice.save()

        if invoice.sale_id:
            invoice.sale.etims_status = "FAILED"
            invoice.sale.save(update_fields=["etims_status"])

    @classmethod
    def _assert_ready(cls, config: EtimsConfig, source) -> None:
        if not config.is_active:
            raise ValidationError("eTIMS is not active. Configure and initialise a device first.")
        if not config.cmc_key:
            raise ValidationError(
                "eTIMS device not initialised. Run `etims_init_device` first.",
            )
        if not config.tin or not config.bhf_id:
            raise ValidationError("eTIMS tin/bhfId missing.")

        if hasattr(source, "items"):
            for item in source.items.all():
                product = item.product
                if not product.etims_item_cls_cd:
                    raise ValidationError(
                        f"Product '{product.sku}' has no eTIMS classification code. "
                        f"Set `Product.etims_item_cls_cd` before selling.",
                    )
                if not EtimsItem.objects.filter(
                    product=product, status=EtimsItem.Status.REGISTERED,
                ).exists():
                    raise ValidationError(
                        f"Product '{product.sku}' is not registered with eTIMS. "
                        f"Run `etims_register_items`.",
                    )

    # ============================================================
    # Payload builders
    # ============================================================
    @classmethod
    def _build_common_items(cls, lines, *, start_seq: int = 1) -> tuple[list, dict]:
        """
        lines: iterable of (product, quantity, unit_price, discount, tax_rate_pct, tax_rate_ref)
        Returns (itemList, tax_buckets).
        """
        buckets = {k: {"taxbl": Decimal("0"), "tax": Decimal("0"), "rate": Decimal("0")}
                   for k in ("A", "B", "C", "D", "E")}
        items = []

        for seq, line in enumerate(lines, start=start_seq):
            product, qty, price, discount, tax_rate_pct, tax_ref = line
            tax_code = TaxMapper.code_for_sale_item(
                type("Tmp", (), {"tax_rate_ref": tax_ref, "tax_rate": tax_rate_pct, "pk": product.pk}),
            )
            qty_d = Decimal(str(qty))
            price_d = Decimal(str(price))
            disc_d = Decimal(str(discount or 0))

            sply_amt = (qty_d * price_d).quantize(Decimal("0.01"), ROUND_HALF_UP)
            line_after_disc = (sply_amt - disc_d).quantize(Decimal("0.01"), ROUND_HALF_UP)

            # Inclusive-to-taxable conversion (KRA standard)
            rate_pct = Decimal(str(tax_rate_pct))
            if rate_pct > 0:
                divisor = Decimal("1") + rate_pct / Decimal("100")
                taxbl = (line_after_disc / divisor).quantize(Decimal("0.01"), ROUND_HALF_UP)
                tax_amt = (line_after_disc - taxbl).quantize(Decimal("0.01"), ROUND_HALF_UP)
            else:
                taxbl = line_after_disc
                tax_amt = Decimal("0.00")

            tot = (taxbl + tax_amt).quantize(Decimal("0.01"), ROUND_HALF_UP)

            buckets[tax_code]["taxbl"] += taxbl
            buckets[tax_code]["tax"] += tax_amt
            buckets[tax_code]["rate"] = rate_pct

            items.append({
                "itemSeq": seq,
                "itemCd": product.sku,
                "itemClsCd": product.etims_item_cls_cd,
                "itemNm": product.name[:200],
                "bcd": product.barcode or None,
                "pkgUnitCd": "NT",
                "pkg": 1,
                "qtyUnitCd": UnitMapper.qty_unit_for(product),
                "qty": float(qty_d),
                "prc": float(price_d),
                "splyAmt": float(sply_amt),
                "dcRt": float(Decimal("0")),
                "dcAmt": float(disc_d),
                "taxTyCd": tax_code,
                "taxblAmt": float(taxbl),
                "taxAmt": float(tax_amt),
                "totAmt": float(tot),
            })

        return items, buckets

    @classmethod
    def _build_header(cls, *, invoice, config, sale, items, buckets, payment_code, receipt_type_code) -> dict:
        now = timezone.localtime()
        cfm_dt = _dt_kra(now)
        sales_dt = _date_kra(now.date())

        cust = sale.customer
        cust_tin = (cust.kra_pin or "").strip() or "N/A"
        cust_name = (cust.business_name or cust.name or "Walk-in")[:100]
        address = (cust.physical_address or "")[:200]

        taxbl = {k: float(buckets[k]["taxbl"].quantize(Decimal("0.01"))) for k in "ABCDE"}
        tax_amt = {k: float(buckets[k]["tax"].quantize(Decimal("0.01"))) for k in "ABCDE"}
        tax_rt = {k: float(buckets[k]["rate"]) for k in "ABCDE"}

        tot_taxbl = round(sum(taxbl.values()), 2)
        tot_tax = round(sum(tax_amt.values()), 2)
        tot_amt = round(tot_taxbl + tot_tax, 2)

        agent = sale.agent
        regr_id = (agent.username or "system")[:20]
        regr_nm = (agent.get_full_name() or agent.username or "System")[:60]

        return {
            "tin": config.tin,
            "bhfId": config.bhf_id,
            "invcNo": invoice.invc_no,
            "orgInvcNo": invoice.org_invc_no or 0,
            "trdInvcNo": invoice.invoice_number,
            "custTin": cust_tin,
            "custNm": cust_name,
            "salesTyCd": "N",
            "rcptTyCd": receipt_type_code,
            "pmtTyCd": payment_code,
            "salesSttsCd": "02",
            "cfmDt": cfm_dt,
            "salesDt": sales_dt,
            "totItemCnt": len(items),
            "taxblAmtA": taxbl["A"], "taxblAmtB": taxbl["B"], "taxblAmtC": taxbl["C"],
            "taxblAmtD": taxbl["D"], "taxblAmtE": taxbl["E"],
            "taxRtA": tax_rt["A"], "taxRtB": tax_rt["B"], "taxRtC": tax_rt["C"],
            "taxRtD": tax_rt["D"], "taxRtE": tax_rt["E"],
            "taxAmtA": tax_amt["A"], "taxAmtB": tax_amt["B"], "taxAmtC": tax_amt["C"],
            "taxAmtD": tax_amt["D"], "taxAmtE": tax_amt["E"],
            "totTaxblAmt": tot_taxbl,
            "totTaxAmt": tot_tax,
            "totAmt": tot_amt,
            "prchrAcptcYn": "N",
            "regrId": regr_id,
            "regrNm": regr_nm,
            "modrId": regr_id,
            "modrNm": regr_nm,
            "receipt": {
                "custTin": cust_tin,
                "rcptPbctDt": cfm_dt,
                "trdeNm": "",
                "adrs": address,
                "topMsg": "Thank you for your business",
                "btmMsg": "",
                "prchrAcptcYn": "N",
            },
            "itemList": items,
        }

    @classmethod
    def _build_sale_payload(cls, invoice: EtimsInvoice, config: EtimsConfig) -> dict:
        sale = invoice.sale
        lines = []
        for it in sale.items.select_related("product", "tax_rate_ref").all():
            lines.append((
                it.product, it.quantity, it.unit_price, it.discount,
                it.tax_rate, it.tax_rate_ref,
            ))
        items, buckets = cls._build_common_items(lines)
        return cls._build_header(
            invoice=invoice, config=config, sale=sale, items=items, buckets=buckets,
            payment_code=PaymentMapper.code_for_sale(sale),
            receipt_type_code="S",
        )

    @classmethod
    def _build_credit_note_payload(cls, invoice: EtimsInvoice, config: EtimsConfig) -> dict:
        ret = invoice.sales_return
        sale = ret.original_sale

        lines = []
        for rit in ret.items.select_related(
            "product", "sale_item__tax_rate_ref",
        ).all():
            orig_item = rit.sale_item
            lines.append((
                rit.product, rit.quantity, rit.unit_price, Decimal("0"),
                orig_item.tax_rate, orig_item.tax_rate_ref,
            ))
        items, buckets = cls._build_common_items(lines)

        return cls._build_header(
            invoice=invoice, config=config, sale=sale, items=items, buckets=buckets,
            payment_code=PaymentMapper.code_for_method("CASH"),
            receipt_type_code="R",
        )