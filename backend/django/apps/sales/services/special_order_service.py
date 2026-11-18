"""Special order lifecycle — ordered → arrived → delivered → cancelled."""
from decimal import Decimal

from django.db import transaction

from core.exceptions.domain import ConflictError, NotFoundError, ValidationError
from core.utils.money import q

from ..models import Sale, SaleItem, SpecialOrder


class SpecialOrderService:

    # ---- Creation (called from SaleService.create_sale) ----
    @staticmethod
    @transaction.atomic
    def create_for_sale_item(
        sale_item: SaleItem,
        supplier_id=None,
        expected_arrival_date=None,
        customer_deposit=0,
    ) -> SpecialOrder:
        from apps.suppliers.models import Supplier

        supplier = None
        if supplier_id:
            supplier = Supplier.objects.filter(pk=supplier_id, is_active=True).first()
            if not supplier:
                raise NotFoundError("Supplier", supplier_id)

        return SpecialOrder.objects.create(
            sale_item=sale_item,
            supplier=supplier,
            expected_arrival_date=expected_arrival_date,
            customer_deposit=q(customer_deposit),
            status=SpecialOrder.Status.ORDERED,
        )

    # ---- Transitions --------------------------------------
    @staticmethod
    @transaction.atomic
    def mark_arrived(so_id: int, user) -> SpecialOrder:
        try:
            so = SpecialOrder.objects.select_for_update().select_related("sale_item").get(pk=so_id)
        except SpecialOrder.DoesNotExist:
            raise NotFoundError("SpecialOrder", so_id)

        if so.status != SpecialOrder.Status.ORDERED:
            raise ConflictError(f"Cannot mark arrived from status {so.status}.")

        so.status = SpecialOrder.Status.ARRIVED
        so.save(update_fields=["status"])
        return so

    @staticmethod
    @transaction.atomic
    def mark_delivered(so_id: int, user) -> SpecialOrder:
        """
        Deliver to the customer. This is when stock leaves inventory.
        The item should have been received earlier via a GRN against the
        linked purchase order; if not, we still deduct so long as stock
        exists at the sale's location.
        """
        from apps.inventory.services import StockService

        try:
            so = (
                SpecialOrder.objects.select_for_update()
                .select_related("sale_item__sale__location", "sale_item__product")
                .get(pk=so_id)
            )
        except SpecialOrder.DoesNotExist:
            raise NotFoundError("SpecialOrder", so_id)

        if so.status not in (SpecialOrder.Status.ORDERED, SpecialOrder.Status.ARRIVED):
            raise ConflictError(f"Cannot deliver from status {so.status}.")

        sale_item = so.sale_item
        sale = sale_item.sale

        # Deduct stock at the sale's location
        StockService.sell(
            product=sale_item.product,
            location=sale.location,
            quantity=sale_item.quantity,
            sale_reference=sale.sale_number,
            unit_cost=sale_item.unit_cost,
            user=user,
        )

        so.status = SpecialOrder.Status.DELIVERED
        so.save(update_fields=["status"])

        # If every special order on this sale is delivered, mark sale PAID/PARTIAL
        all_delivered = all(
            item.special_order.status == SpecialOrder.Status.DELIVERED
            for item in sale.items.select_related("special_order")
            if hasattr(item, "special_order")
        )
        if all_delivered and sale.status == Sale.Status.CONFIRMED:
            if sale.balance_due == 0:
                sale.status = Sale.Status.PAID
            else:
                sale.status = Sale.Status.PARTIAL
            sale.save(update_fields=["status"])

        return so

    @staticmethod
    @transaction.atomic
    def cancel(so_id: int, user, reason: str = "") -> SpecialOrder:
        try:
            so = SpecialOrder.objects.select_for_update().get(pk=so_id)
        except SpecialOrder.DoesNotExist:
            raise NotFoundError("SpecialOrder", so_id)

        if so.status == SpecialOrder.Status.DELIVERED:
            raise ConflictError("Cannot cancel a delivered special order.")
        if so.status == SpecialOrder.Status.CANCELLED:
            return so

        so.status = SpecialOrder.Status.CANCELLED
        if reason:
            so.notes = (so.notes + f"\nCancelled: {reason}").strip()
        so.save(update_fields=["status", "notes"])
        return so