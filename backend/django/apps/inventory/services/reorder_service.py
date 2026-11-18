"""Reorder-level detection and purchase-order suggestion."""
from decimal import Decimal

from django.db.models import F, Q

from ..models import StockLevel


class ReorderService:

    @staticmethod
    def _low_stock_queryset():
        return (
            StockLevel.objects
            .filter(
                product__is_stocked=True,
                product__is_active=True,
                location__is_active=True,
            )
            .filter(
                Q(
                    reorder_level__isnull=False,
                    reorder_level__gt=0,
                    quantity__lte=F("reorder_level"),
                )
                | Q(
                    reorder_level__isnull=True,
                    product__reorder_level__gt=0,
                    quantity__lte=F("product__reorder_level"),
                )
            )
            .select_related("product", "location")
            .order_by("location__name", "product__name")
        )

    @staticmethod
    def low_stock_levels():
        return ReorderService._low_stock_queryset()

    @staticmethod
    def needs_reorder(level: StockLevel) -> bool:
        threshold = level.effective_reorder_level()
        return threshold > 0 and Decimal(level.quantity) <= threshold

    @staticmethod
    def suggested_quantity(level: StockLevel) -> Decimal:
        """If reorder_qty is set on the product, use it; else 2x reorder-level minus current."""
        product = level.product
        if product.reorder_qty and product.reorder_qty > 0:
            return Decimal(product.reorder_qty)
        threshold = Decimal(level.effective_reorder_level() or 0)
        suggested = (threshold * 2) - Decimal(level.quantity)
        return suggested if suggested > 0 else Decimal("1")

    @staticmethod
    def suggest_purchase_order() -> list[dict]:
        """
        Group low-stock items by preferred supplier and propose a PO per supplier.
        Never creates POs — the boss reviews and confirms.
        """
        from apps.suppliers.services import SupplierService

        grouped: dict[int | None, dict] = {}

        for level in ReorderService.low_stock_levels():
            product = level.product
            link = SupplierService.preferred_supplier_for(product.pk)
            supplier = link.supplier if link else None
            key = supplier.pk if supplier else None

            bucket = grouped.setdefault(
                key,
                {
                    "supplier_id": supplier.pk if supplier else None,
                    "supplier_name": supplier.name if supplier else "No preferred supplier",
                    "items": [],
                    "estimated_total": Decimal("0"),
                },
            )

            qty = ReorderService.suggested_quantity(level)
            unit_cost = (
                Decimal(link.last_purchase_price) if link and link.last_purchase_price
                else Decimal(product.cost_price or 0)
            )
            line_total = (qty * unit_cost).quantize(Decimal("0.01"))
            bucket["estimated_total"] += line_total

            bucket["items"].append({
                "product_id": product.pk,
                "sku": product.sku,
                "name": product.name,
                "location": level.location.name,
                "current_quantity": str(level.quantity),
                "reorder_level": level.effective_reorder_level(),
                "suggested_quantity": str(qty),
                "unit_cost_estimate": str(unit_cost),
                "line_total_estimate": str(line_total),
            })

        result = list(grouped.values())
        for bucket in result:
            bucket["estimated_total"] = str(bucket["estimated_total"])
        return result