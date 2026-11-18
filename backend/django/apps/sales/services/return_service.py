"""
Sales returns — draft → approved/rejected → completed.

`complete()` is atomic and does:
    - restock items (restock=True only)
    - increment SaleItem.returned_quantity (prevents over-returning)
    - reverse credit via CREDIT_NOTE if the original was a credit sale
    - record refund_amount + refund_method
    - flip sale.status to RETURNED if fully returned
"""
from decimal import Decimal

from django.db import transaction

from core.exceptions.domain import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from core.utils.money import q

from ..models import Sale, SaleItem, SalesReturn, SalesReturnItem


class ReturnService:

    # ---- Create -------------------------------------------
    @staticmethod
    @transaction.atomic
    def create_return(data: dict, user) -> SalesReturn:
        from apps.inventory.models import Product, StockLocation

        try:
            sale = Sale.objects.select_related("customer").get(pk=data["original_sale"])
        except Sale.DoesNotExist:
            raise NotFoundError("Sale", data["original_sale"])

        if sale.status not in (
            Sale.Status.CONFIRMED, Sale.Status.PAID, Sale.Status.PARTIAL,
        ):
            raise ConflictError(
                f"Cannot return against a sale in status {sale.status}."
            )

        items_input = data.get("items") or []
        if not items_input:
            raise ValidationError("Return must contain at least one item.")

        sale_items = {
            si.pk: si
            for si in sale.items.select_related("product").all()
        }

        # Prevalidate
        for line in items_input:
            sale_item = sale_items.get(line["sale_item"])
            if not sale_item:
                raise ValidationError(
                    f"Sale item {line['sale_item']} does not belong to sale {sale.sale_number}."
                )
            qty = q(line["quantity"])
            if qty <= 0:
                raise ValidationError("Return quantity must be positive.")
            if qty > sale_item.returnable_quantity:
                raise ValidationError(
                    f"Cannot return {qty} of {sale_item.product.sku}; "
                    f"only {sale_item.returnable_quantity} remaining."
                )
            if line.get("location"):
                if not StockLocation.objects.filter(pk=line["location"]).exists():
                    raise NotFoundError("StockLocation", line["location"])

        ret = SalesReturn.objects.create(
            original_sale=sale,
            customer=sale.customer,
            reason=data.get("reason", ""),
            refund_method_id=data.get("refund_method"),
            created_by=user,
            status=SalesReturn.Status.DRAFT,
        )

        refund_total = Decimal("0")
        for line in items_input:
            sale_item = sale_items[line["sale_item"]]
            qty = q(line["quantity"])
            unit_price = q(sale_item.unit_price)
            line_refund = q(qty * unit_price)
            refund_total += line_refund

            SalesReturnItem.objects.create(
                sales_return=ret,
                sale_item=sale_item,
                product=sale_item.product,
                quantity=qty,
                unit_price=unit_price,
                restock=line.get("restock", True),
                location_id=line.get("location") or sale.location_id,
            )

        ret.refund_amount = q(refund_total)
        ret.save(update_fields=["refund_amount"])
        return ret

    # ---- Transitions --------------------------------------
    @staticmethod
    @transaction.atomic
    def approve(ret_id: int, user) -> SalesReturn:
        try:
            ret = SalesReturn.objects.select_for_update().get(pk=ret_id)
        except SalesReturn.DoesNotExist:
            raise NotFoundError("SalesReturn", ret_id)
        if ret.status != SalesReturn.Status.DRAFT:
            raise ConflictError(f"Cannot approve a return in status {ret.status}.")
        ret.status = SalesReturn.Status.APPROVED
        ret.save(update_fields=["status"])
        return ret

    @staticmethod
    @transaction.atomic
    def reject(ret_id: int, user, reason: str = "") -> SalesReturn:
        try:
            ret = SalesReturn.objects.select_for_update().get(pk=ret_id)
        except SalesReturn.DoesNotExist:
            raise NotFoundError("SalesReturn", ret_id)
        if ret.status not in (SalesReturn.Status.DRAFT, SalesReturn.Status.APPROVED):
            raise ConflictError(f"Cannot reject a return in status {ret.status}.")
        ret.status = SalesReturn.Status.REJECTED
        if reason:
            ret.reason = (ret.reason + f"\nRejected: {reason}").strip()
        ret.save(update_fields=["status", "reason"])
        return ret

    @staticmethod
    @transaction.atomic
    def complete(ret_id: int, user) -> SalesReturn:
        from apps.inventory.services import StockService
        from apps.customers.services import CustomerService

        try:
            ret = (
                SalesReturn.objects.select_for_update()
                .select_related("original_sale", "customer")
                .prefetch_related("items__sale_item__product")
                .get(pk=ret_id)
            )
        except SalesReturn.DoesNotExist:
            raise NotFoundError("SalesReturn", ret_id)

        if ret.status != SalesReturn.Status.APPROVED:
            raise ConflictError(
                f"Only APPROVED returns can be completed (current: {ret.status})."
            )

        sale = ret.original_sale

        # Restock + track returned quantity
        for item in ret.items.all():
            sale_item = item.sale_item
            sale_item.returned_quantity = q(sale_item.returned_quantity + item.quantity)
            sale_item.save(update_fields=["returned_quantity"])

            if item.restock and item.location_id:
                from apps.inventory.models import StockLocation
                location = StockLocation.objects.filter(pk=item.location_id).first()
                if location:
                    StockService.return_to_stock(
                        product=item.product,
                        location=location,
                        quantity=item.quantity,
                        return_reference=ret.return_number,
                        user=user,
                    )

        # Reverse credit
        if sale.is_credit_sale and sale.customer_id:
            # Cap the reduction to what the customer still owes from this sale.
            remaining_debt = max(
                Decimal("0"), Decimal(sale.balance_due)
            )
            if remaining_debt > 0:
                reduce_by = min(ret.refund_amount, remaining_debt)
                CustomerService.adjust_balance(
                    customer_id=sale.customer_id,
                    delta=-reduce_by,
                    entry_type="CREDIT_NOTE",
                    reference_type="SalesReturn",
                    reference_id=ret.return_number,
                )

        ret.status = SalesReturn.Status.COMPLETED
        ret.save(update_fields=["status"])

        # Update sale status if fully returned
        fully_returned = all(
            Decimal(si.returned_quantity) >= Decimal(si.quantity)
            for si in sale.items.all()
        )
        if fully_returned and sale.status != Sale.Status.RETURNED:
            sale.status = Sale.Status.RETURNED
            sale.save(update_fields=["status"])

        return ret