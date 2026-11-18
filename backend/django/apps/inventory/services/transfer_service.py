"""
Two-phase stock transfers between locations.

Lifecycle:
    create()   → PENDING     (no stock change)
    dispatch() → IN_TRANSIT  (deduct from source, create TRANSFER_OUT movements)
    receive()  → RECEIVED    (credit destination, create TRANSFER_IN movements)
    cancel()   → CANCELLED   (restore to source if IN_TRANSIT)
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

from ..models import (
    Product,
    StockLocation,
    StockMovement,
    StockTransfer,
    StockTransferItem,
)
from .stock_service import StockService


class TransferService:

    @staticmethod
    @transaction.atomic
    def create(
        from_location: StockLocation,
        to_location: StockLocation,
        items: list[dict],
        user,
        notes: str = "",
    ) -> StockTransfer:
        """
        items = [{"product_id": 1, "quantity": "3.00"}, ...]
        No stock is moved here — items are only reserved by intent.
        """
        if from_location.pk == to_location.pk:
            raise ValidationError("Source and destination must differ.")
        if not from_location.is_active or not to_location.is_active:
            raise ValidationError("Both locations must be active.")
        if not items:
            raise ValidationError("Transfer must contain at least one item.")

        transfer = StockTransfer.objects.create(
            from_location=from_location,
            to_location=to_location,
            initiated_by=user,
            status=StockTransfer.Status.PENDING,
            notes=notes,
        )

        for item in items:
            product = Product.objects.filter(pk=item["product_id"]).first()
            if not product:
                raise NotFoundError("Product", item["product_id"])
            qty = q(item["quantity"])
            if qty <= 0:
                raise ValidationError(f"Quantity for {product.sku} must be positive.")
            StockTransferItem.objects.create(
                transfer=transfer, product=product, quantity=qty,
            )

        return transfer

    @staticmethod
    @transaction.atomic
    def dispatch(transfer_id: int, user) -> StockTransfer:
        try:
            transfer = (
                StockTransfer.objects.select_for_update()
                .select_related("from_location", "to_location")
                .get(pk=transfer_id)
            )
        except StockTransfer.DoesNotExist:
            raise NotFoundError("StockTransfer", transfer_id)

        if transfer.status != StockTransfer.Status.PENDING:
            raise ConflictError(
                f"Cannot dispatch a transfer in status {transfer.status}."
            )

        # Pre-validate stock for every item, then deduct (all-or-nothing).
        for item in transfer.items.select_related("product"):
            StockService.require_stock(
                item.product, transfer.from_location, item.quantity,
            )

        for item in transfer.items.select_related("product"):
            StockService.adjust(
                product=item.product,
                location=transfer.from_location,
                delta=-item.quantity,
                movement_type=StockMovement.Type.TRANSFER_OUT,
                reference_type="StockTransfer",
                reference_id=str(transfer.pk),
                notes=f"Dispatched by {user.username}",
                user=user,
            )

        transfer.status = StockTransfer.Status.IN_TRANSIT
        transfer.save(update_fields=["status"])
        return transfer

    @staticmethod
    @transaction.atomic
    def receive(transfer_id: int, user) -> StockTransfer:
        try:
            transfer = (
                StockTransfer.objects.select_for_update()
                .select_related("to_location")
                .get(pk=transfer_id)
            )
        except StockTransfer.DoesNotExist:
            raise NotFoundError("StockTransfer", transfer_id)

        if transfer.status != StockTransfer.Status.IN_TRANSIT:
            raise ConflictError(
                f"Cannot receive a transfer in status {transfer.status}."
            )

        for item in transfer.items.select_related("product"):
            StockService.adjust(
                product=item.product,
                location=transfer.to_location,
                delta=item.quantity,
                movement_type=StockMovement.Type.TRANSFER_IN,
                reference_type="StockTransfer",
                reference_id=str(transfer.pk),
                notes=f"Received by {user.username}",
                user=user,
            )

        transfer.status = StockTransfer.Status.RECEIVED
        transfer.received_by = user
        transfer.received_at = timezone.now()
        transfer.save(update_fields=["status", "received_by", "received_at"])
        return transfer

    @staticmethod
    @transaction.atomic
    def cancel(transfer_id: int, user) -> StockTransfer:
        try:
            transfer = StockTransfer.objects.select_for_update().get(pk=transfer_id)
        except StockTransfer.DoesNotExist:
            raise NotFoundError("StockTransfer", transfer_id)

        if transfer.status not in (
            StockTransfer.Status.PENDING,
            StockTransfer.Status.IN_TRANSIT,
        ):
            raise ConflictError(
                f"Cannot cancel a transfer in status {transfer.status}."
            )

        # Restore source stock if we already deducted.
        if transfer.status == StockTransfer.Status.IN_TRANSIT:
            for item in transfer.items.select_related("product"):
                StockService.adjust(
                    product=item.product,
                    location=transfer.from_location,
                    delta=item.quantity,
                    movement_type=StockMovement.Type.TRANSFER_IN,
                    reference_type="StockTransfer",
                    reference_id=str(transfer.pk),
                    notes=f"Cancelled by {user.username} — restored to source",
                    user=user,
                )

        transfer.status = StockTransfer.Status.CANCELLED
        transfer.save(update_fields=["status"])
        return transfer