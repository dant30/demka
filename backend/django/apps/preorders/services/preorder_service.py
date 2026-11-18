"""
Preorder lifecycle.

    submit()      → SUBMITTED (snapshots wholesale price + stock flag)
    confirm()     → CONFIRMED (boss may adjust line prices here)
    prepare()     → IN_PREPARATION
    mark_ready()  → READY
    deliver()     → DELIVERED (atomically converts to a Sale + Payment)
    cancel()      → CANCELLED (customer while SUBMITTED; boss anytime pre-delivery)
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.exceptions.domain import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from core.utils.money import q


class PreorderService:

    # ---- Submit -------------------------------------------
    @classmethod
    @transaction.atomic
    def submit(cls, customer, data: dict) -> "Preorder":
        from apps.inventory.models import Product

        from ..models import Preorder, PreorderItem
        from .catalog_service import CatalogService

        items_input = data.get("items") or []
        if not items_input:
            raise ValidationError("At least one item is required.")

        if data.get("preferred_pickup_date") and data["preferred_pickup_date"] < timezone.now().date():
            raise ValidationError("Preferred pickup date cannot be in the past.")

        seen = set()
        for line in items_input:
            if line["product"] in seen:
                raise ValidationError(
                    f"Duplicate product in preorder items (id {line['product']})."
                )
            seen.add(line["product"])
            if Decimal(str(line["quantity"])) <= 0:
                raise ValidationError("Quantity must be positive.")

        preorder = Preorder.objects.create(
            customer=customer,
            preferred_pickup_date=data.get("preferred_pickup_date"),
            notes=(data.get("notes") or "").strip(),
            status=Preorder.Status.SUBMITTED,
        )

        total = Decimal("0")
        for line in items_input:
            product = (
                CatalogService._base_queryset()
                .filter(pk=line["product"])
                .first()
            )
            if not product:
                raise NotFoundError("Product", line["product"])

            qty = q(line["quantity"])
            unit_price = q(product.wholesale_price)
            available = q(getattr(product, "available_qty", Decimal("0")))

            PreorderItem.objects.create(
                preorder=preorder,
                product=product,
                quantity=qty,
                unit_price_estimated=unit_price,
                available_in_stock=available >= qty,
                available_quantity=available,
                notes=(line.get("notes") or "").strip()[:200],
            )
            total += q(qty * unit_price)

        preorder.total_estimated = q(total)
        preorder.save(update_fields=["total_estimated"])

        return preorder

    # ---- Staff transitions --------------------------------
    @staticmethod
    @transaction.atomic
    def confirm(preorder_id: int, user, price_adjustments=None) -> "Preorder":
        from ..models import Preorder

        try:
            preorder = (
                Preorder.objects.select_for_update()
                .prefetch_related("items")
                .get(pk=preorder_id)
            )
        except Preorder.DoesNotExist:
            raise NotFoundError("Preorder", preorder_id)

        if preorder.status != Preorder.Status.SUBMITTED:
            raise ConflictError(f"Cannot confirm a preorder in status {preorder.status}.")

        # Optional price adjustments: [{"item": <id>, "final_price": "130.00"}, ...]
        if price_adjustments:
            item_map = {it.pk: it for it in preorder.items.all()}
            for adj in price_adjustments:
                item = item_map.get(adj["item"])
                if not item:
                    raise ValidationError(f"Preorder item {adj['item']} not found.")
                new_price = q(adj["final_price"])
                if new_price < 0:
                    raise ValidationError("Price cannot be negative.")
                item.final_price = new_price
                item.save(update_fields=["final_price"])

            # Recompute total
            preorder.total_estimated = q(
                sum(
                    Decimal(it.quantity) * Decimal(it.effective_unit_price)
                    for it in preorder.items.all()
                )
            )
            preorder.save(update_fields=["total_estimated"])

        preorder.status = Preorder.Status.CONFIRMED
        preorder.confirmed_at = timezone.now()
        preorder.save(update_fields=["status", "confirmed_at"])
        return preorder

    @staticmethod
    @transaction.atomic
    def prepare(preorder_id: int, user) -> "Preorder":
        from ..models import Preorder

        try:
            preorder = Preorder.objects.select_for_update().get(pk=preorder_id)
        except Preorder.DoesNotExist:
            raise NotFoundError("Preorder", preorder_id)
        if preorder.status != Preorder.Status.CONFIRMED:
            raise ConflictError(f"Cannot prepare from status {preorder.status}.")
        preorder.status = Preorder.Status.IN_PREPARATION
        preorder.save(update_fields=["status"])
        return preorder

    @staticmethod
    @transaction.atomic
    def mark_ready(preorder_id: int, user) -> "Preorder":
        from ..models import Preorder

        try:
            preorder = Preorder.objects.select_for_update().get(pk=preorder_id)
        except Preorder.DoesNotExist:
            raise NotFoundError("Preorder", preorder_id)
        if preorder.status != Preorder.Status.IN_PREPARATION:
            raise ConflictError(f"Cannot mark ready from status {preorder.status}.")
        preorder.status = Preorder.Status.READY
        preorder.ready_at = timezone.now()
        preorder.save(update_fields=["status", "ready_at"])
        return preorder

    @classmethod
    @transaction.atomic
    def deliver(cls, preorder_id: int, data: dict, user) -> "Preorder":
        """Convert to a real Sale and mark DELIVERED."""
        from apps.sales.services import SaleService

        from ..models import Preorder

        try:
            preorder = (
                Preorder.objects.select_for_update()
                .select_related("customer")
                .prefetch_related("items__product")
                .get(pk=preorder_id)
            )
        except Preorder.DoesNotExist:
            raise NotFoundError("Preorder", preorder_id)

        if preorder.status != Preorder.Status.READY:
            raise ConflictError(f"Cannot deliver from status {preorder.status}.")
        if preorder.converted_sale_id:
            raise ConflictError("Preorder already converted to a sale.")

        location_id = data.get("location")
        payment_method = data.get("payment_method")
        amount_paid = q(data.get("amount_paid", 0))

        if not location_id:
            raise ValidationError("location is required.")
        if amount_paid < 0:
            raise ValidationError("amount_paid cannot be negative.")
        if amount_paid > 0 and not payment_method:
            raise ValidationError("payment_method is required when amount_paid > 0.")

        sale_items = [
            {
                "product": it.product_id,
                "quantity": str(it.quantity),
                "unit_price": str(it.effective_unit_price),
            }
            for it in preorder.items.all()
        ]

        sale = SaleService.create_sale(
            {
                "channel": "SHOP",
                "sale_type": "STANDARD",
                "customer": preorder.customer_id,
                "location": location_id,
                "items": sale_items,
                "amount_paid": str(amount_paid),
                "payment_method": payment_method,
                "discount_amount": str(data.get("discount_amount", "0")),
                "notes": f"Delivered from preorder {preorder.preorder_number}",
            },
            user,
            confirm=True,
        )

        preorder.converted_sale = sale
        preorder.status = Preorder.Status.DELIVERED
        preorder.delivered_at = timezone.now()
        preorder.save(update_fields=["converted_sale", "status", "delivered_at"])
        return preorder

    @staticmethod
    @transaction.atomic
    def cancel(preorder_id: int, user, reason: str = "", *, by_customer=False) -> "Preorder":
        from ..models import Preorder

        try:
            preorder = Preorder.objects.select_for_update().get(pk=preorder_id)
        except Preorder.DoesNotExist:
            raise NotFoundError("Preorder", preorder_id)

        if preorder.status in (Preorder.Status.DELIVERED, Preorder.Status.CANCELLED):
            raise ConflictError(f"Cannot cancel a preorder in status {preorder.status}.")
        if by_customer and preorder.status != Preorder.Status.SUBMITTED:
            raise ConflictError(
                "You can only cancel while the preorder is still SUBMITTED. "
                "Contact the shop if it has been confirmed.",
            )

        preorder.status = Preorder.Status.CANCELLED
        preorder.cancelled_at = timezone.now()
        preorder.cancelled_by = None if by_customer else user
        preorder.cancel_reason = (reason or "").strip()
        preorder.save(update_fields=[
            "status", "cancelled_at", "cancelled_by", "cancel_reason",
        ])
        return preorder