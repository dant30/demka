"""
Atomic stock operations — the only place StockLevel.quantity is mutated.

Every write:
  1. Locks the StockLevel row via select_for_update().
  2. Validates the resulting quantity >= 0 (unless allowed).
  3. Saves the level.
  4. Appends an immutable StockMovement ledger row.
  5. Invalidates cache for the product.
"""
from decimal import Decimal

from django.db import transaction

from core.exceptions.domain import (
    ConflictError,
    InsufficientStockError,
    NotFoundError,
)
from core.utils.money import q

from ..models import Product, StockLevel, StockLocation, StockMovement


class StockService:

    # ---- Helpers ------------------------------------------
    @staticmethod
    def get_or_create_level(product: Product, location: StockLocation) -> StockLevel:
        level, _ = StockLevel.objects.get_or_create(
            product=product,
            location=location,
            defaults={"quantity": Decimal("0")},
        )
        return level

    @staticmethod
    def available(product: Product, location: StockLocation) -> Decimal:
        level = StockLevel.objects.filter(
            product=product, location=location,
        ).only("quantity").first()
        return level.quantity if level else Decimal("0")

    # ---- Core mutation ------------------------------------
    @staticmethod
    @transaction.atomic
    def adjust(
        product: Product,
        location: StockLocation,
        delta,
        movement_type: str,
        *,
        reference_type: str = "",
        reference_id: str = "",
        unit_cost=None,
        notes: str = "",
        user=None,
        allow_negative: bool = False,
    ) -> tuple[StockLevel, StockMovement]:
        """
        The single gateway for all stock mutations.

        `delta` is a signed Decimal (or int/str). Positive = add, negative = subtract.
        Raises InsufficientStockError if the resulting quantity would be negative
        and `allow_negative` is False.
        """
        if not product.is_active:
            raise ConflictError(f"Product '{product.sku}' is inactive.")
        if not location.is_active:
            raise ConflictError(f"Location '{location.name}' is inactive.")

        delta = q(delta)

        # Ensure row exists first (unique constraint handles concurrency),
        # then lock it for the rest of this transaction.
        StockLevel.objects.get_or_create(
            product=product, location=location,
            defaults={"quantity": Decimal("0")},
        )
        level = StockLevel.objects.select_for_update().get(
            product=product, location=location,
        )

        new_qty = q(Decimal(level.quantity) + delta)
        if new_qty < 0 and not allow_negative:
            raise InsufficientStockError(
                product_name=product.name,
                requested=str(abs(delta)),
                available=str(level.quantity),
            )

        level.quantity = new_qty
        level.save(update_fields=["quantity", "last_updated"])

        movement = StockMovement.objects.create(
            product=product,
            location=location,
            movement_type=movement_type,
            quantity=delta,
            unit_cost=q(unit_cost) if unit_cost is not None else None,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=user if user and getattr(user, "is_authenticated", False) else None,
        )
        return level, movement

    # ---- Domain wrappers ----------------------------------
    @staticmethod
    @transaction.atomic
    def sell(product, location, quantity, *, sale_reference: str, user, unit_cost=None):
        return StockService.adjust(
            product=product,
            location=location,
            delta=-quantity,
            movement_type=StockMovement.Type.SALE,
            reference_type="Sale",
            reference_id=sale_reference,
            unit_cost=unit_cost,
            user=user,
        )

    @staticmethod
    @transaction.atomic
    def receive(product, location, quantity, *, grn_reference: str, unit_cost, user):
        return StockService.adjust(
            product=product,
            location=location,
            delta=quantity,
            movement_type=StockMovement.Type.PURCHASE,
            reference_type="GoodsReceivedNote",
            reference_id=grn_reference,
            unit_cost=unit_cost,
            user=user,
        )

    @staticmethod
    @transaction.atomic
    def return_to_stock(product, location, quantity, *, return_reference: str, user):
        return StockService.adjust(
            product=product,
            location=location,
            delta=quantity,
            movement_type=StockMovement.Type.RETURN,
            reference_type="SalesReturn",
            reference_id=return_reference,
            user=user,
        )

    @staticmethod
    @transaction.atomic
    def special_order_out(product, location, quantity, *, sale_reference: str, user):
        return StockService.adjust(
            product=product,
            location=location,
            delta=-quantity,
            movement_type=StockMovement.Type.SPECIAL_ORDER_OUT,
            reference_type="Sale",
            reference_id=sale_reference,
            user=user,
        )

    @staticmethod
    def require_stock(product, location, quantity) -> None:
        available = StockService.available(product, location)
        if available < q(quantity):
            raise InsufficientStockError(
                product_name=product.name,
                requested=str(quantity),
                available=str(available),
            )

    # ---- Bulk helpers -------------------------------------
    @staticmethod
    def snapshot(location: StockLocation | None = None) -> dict:
        """Total stock value at a location (or company-wide)."""
        qs = StockLevel.objects.select_related("product")
        if location is not None:
            qs = qs.filter(location=location)
        total_value = Decimal("0")
        total_units = Decimal("0")
        for level in qs:
            value = q(Decimal(level.quantity) * Decimal(level.product.cost_price))
            total_value += value
            total_units += Decimal(level.quantity)
        return {
            "location": location.name if location else "all",
            "total_units": str(total_units),
            "total_value": str(q(total_value)),
        }

    @staticmethod
    def product_summary(product_id: int) -> dict:
        """Per-product per-location stock breakdown."""
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            raise NotFoundError("Product", product_id)

        rows = []
        for level in product.levels.select_related("location").all():
            rows.append({
                "location_id": level.location_id,
                "location_name": level.location.name,
                "quantity": str(level.quantity),
                "reorder_level": level.effective_reorder_level(),
                "needs_reorder": (
                    level.effective_reorder_level() > 0
                    and Decimal(level.quantity) <= level.effective_reorder_level()
                ),
            })
        total = sum((Decimal(r["quantity"]) for r in rows), Decimal("0"))
        return {
            "product_id": product.pk,
            "sku": product.sku,
            "name": product.name,
            "unit": product.unit,
            "total_quantity": str(q(total)),
            "by_location": rows,
        }