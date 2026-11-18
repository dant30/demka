"""Purchase order lifecycle — create, send, cancel, recompute totals."""
from decimal import Decimal

from django.db import transaction

from core.exceptions.domain import ConflictError, NotFoundError, ValidationError
from core.utils.money import q

from ..models import GoodsReceivedNote, PurchaseOrder, PurchaseOrderItem


DEFAULT_TAX_RATE = Decimal("16.00")


class PurchaseOrderService:

    # ---- Totals -------------------------------------------
    @staticmethod
    @transaction.atomic
    def recompute_totals(po: PurchaseOrder, tax_rate: Decimal = DEFAULT_TAX_RATE) -> PurchaseOrder:
        subtotal = Decimal("0")
        for item in po.items.all():
            line = q(Decimal(item.quantity_ordered) * Decimal(item.unit_cost))
            if item.line_total != line:
                item.line_total = line
                item.save(update_fields=["line_total"])
            subtotal += line
        tax = q(subtotal * Decimal(tax_rate) / Decimal("100"))
        po.subtotal = q(subtotal)
        po.tax = tax
        po.total = q(subtotal + tax)
        po.save(update_fields=["subtotal", "tax", "total"])
        return po

    # ---- Create -------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_po(data: dict, user) -> PurchaseOrder:
        from apps.common.services.numbering import next_number
        from apps.inventory.models import Product
        from apps.suppliers.models import Supplier

        supplier = Supplier.objects.filter(pk=data["supplier"], is_active=True).first()
        if not supplier:
            raise NotFoundError("Supplier", data["supplier"])

        if not data.get("items"):
            raise ValidationError("A purchase order must have at least one item.")

        seen_products = set()
        for item in data["items"]:
            if item["product"] in seen_products:
                raise ValidationError(
                    f"Duplicate product in PO items (product id {item['product']})."
                )
            seen_products.add(item["product"])
            if not Product.objects.filter(pk=item["product"]).exists():
                raise NotFoundError("Product", item["product"])
            if Decimal(item["quantity_ordered"]) <= 0:
                raise ValidationError("Ordered quantity must be positive.")
            if Decimal(item["unit_cost"]) < 0:
                raise ValidationError("Unit cost cannot be negative.")

        po = PurchaseOrder.objects.create(
            po_number=next_number("PURCHASE_ORDER", prefix="PO-", width=6),
            supplier=supplier,
            expected_date=data.get("expected_date"),
            notes=data.get("notes", ""),
            created_by=user,
            status=PurchaseOrder.Status.DRAFT,
        )
        for item in data["items"]:
            PurchaseOrderItem.objects.create(
                po=po,
                product_id=item["product"],
                quantity_ordered=q(item["quantity_ordered"]),
                unit_cost=q(item["unit_cost"]),
                line_total=q(
                    Decimal(item["quantity_ordered"]) * Decimal(item["unit_cost"])
                ),
            )

        PurchaseOrderService.recompute_totals(
            po, tax_rate=Decimal(str(data.get("tax_rate", DEFAULT_TAX_RATE))),
        )
        return po

    # ---- Transitions --------------------------------------
    @staticmethod
    @transaction.atomic
    def send(po_id: int, user) -> PurchaseOrder:
        try:
            po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
        except PurchaseOrder.DoesNotExist:
            raise NotFoundError("PurchaseOrder", po_id)

        if po.status != PurchaseOrder.Status.DRAFT:
            raise ConflictError(
                f"Cannot send a PO in status {po.status}."
            )
        if not po.items.exists():
            raise ValidationError("Cannot send an empty PO.")

        po.status = PurchaseOrder.Status.SENT
        po.save(update_fields=["status"])

        try:
            from .tasks import send_po_notification_sms
            send_po_notification_sms.delay(po.pk)
        except Exception:
            pass
        return po

    @staticmethod
    @transaction.atomic
    def cancel(po_id: int, user) -> PurchaseOrder:
        try:
            po = PurchaseOrder.objects.select_for_update().get(pk=po_id)
        except PurchaseOrder.DoesNotExist:
            raise NotFoundError("PurchaseOrder", po_id)

        if po.status not in (PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.SENT):
            raise ConflictError(
                f"Cannot cancel a PO in status {po.status}."
            )
        if GoodsReceivedNote.objects.filter(po=po).exists():
            raise ConflictError(
                "Cannot cancel a PO that already has a goods received note."
            )

        po.status = PurchaseOrder.Status.CANCELLED
        po.save(update_fields=["status"])
        return po

    # ---- Status refresh (called by GRN posting) -----------
    @staticmethod
    @transaction.atomic
    def refresh_status_from_receipts(po: PurchaseOrder) -> PurchaseOrder:
        items = list(po.items.all())
        if not items:
            return po
        all_complete = all(
            Decimal(i.quantity_received) >= Decimal(i.quantity_ordered)
            for i in items
        )
        any_received = any(Decimal(i.quantity_received) > 0 for i in items)

        if all_complete:
            new_status = PurchaseOrder.Status.RECEIVED
        elif any_received:
            new_status = PurchaseOrder.Status.PARTIAL
        else:
            return po

        if po.status != new_status:
            po.status = new_status
            po.save(update_fields=["status"])
        return po

    # ---- Queries ------------------------------------------
    @staticmethod
    def outstanding_items(po: PurchaseOrder) -> list[dict]:
        """Return PO items not yet fully received."""
        out = []
        for item in po.items.select_related("product"):
            remaining = Decimal(item.quantity_ordered) - Decimal(item.quantity_received)
            if remaining > 0:
                out.append({
                    "po_item": item.pk,
                    "product": item.product_id,
                    "sku": item.product.sku,
                    "name": item.product.name,
                    "quantity_ordered": str(item.quantity_ordered),
                    "quantity_received": str(item.quantity_received),
                    "remaining": str(remaining),
                    "unit_cost": str(item.unit_cost),
                })
        return out