"""
Goods Received Note posting.

`post()` is the single entry point — atomic across:
  - GRN header + items
  - StockService.receive() per line (increments stock, logs movement)
  - PurchaseOrderItem.quantity_received increment (if PO-linked)
  - PurchaseOrder status refresh (PARTIAL / RECEIVED)
  - SupplierProduct.last_purchase_price sync
"""
from decimal import Decimal

from django.db import transaction

from core.exceptions.domain import NotFoundError, ValidationError
from core.utils.money import q

from ..models import (
    GoodsReceivedItem,
    GoodsReceivedNote,
    PurchaseOrder,
    PurchaseOrderItem,
)


class GRNService:

    # ---- Post ---------------------------------------------
    @staticmethod
    @transaction.atomic
    def post(data: dict, user) -> GoodsReceivedNote:
        from apps.common.services.numbering import next_number
        from apps.inventory.models import Product, StockLocation
        from apps.inventory.services import StockService
        from apps.suppliers.models import Supplier
        from apps.suppliers.services import SupplierService

        supplier = Supplier.objects.filter(pk=data["supplier"], is_active=True).first()
        if not supplier:
            raise NotFoundError("Supplier", data["supplier"])

        location = StockLocation.objects.filter(pk=data["location"], is_active=True).first()
        if not location:
            raise NotFoundError("StockLocation", data["location"])

        po = None
        if data.get("po"):
            po = PurchaseOrder.objects.select_for_update().filter(pk=data["po"]).first()
            if not po:
                raise NotFoundError("PurchaseOrder", data["po"])
            if po.status not in (
                PurchaseOrder.Status.SENT, PurchaseOrder.Status.PARTIAL,
            ):
                raise ValidationError(
                    f"Cannot receive against a PO in status {po.status}."
                )
            if po.supplier_id != supplier.pk:
                raise ValidationError("PO supplier does not match GRN supplier.")

        items = data.get("items") or []
        if not items:
            raise ValidationError("GRN must contain at least one item.")

        # Prevalidate and gather products.
        product_map: dict[int, Product] = {}
        po_item_map: dict[int, PurchaseOrderItem] = {}
        if po:
            for poi in po.items.all():
                po_item_map[poi.product_id] = poi

        for item in items:
            product = Product.objects.filter(pk=item["product"]).first()
            if not product:
                raise NotFoundError("Product", item["product"])
            if Decimal(item["quantity_received"]) <= 0:
                raise ValidationError(
                    f"Quantity received must be positive for {product.sku}."
                )
            if Decimal(item["unit_cost"]) < 0:
                raise ValidationError(
                    f"Unit cost cannot be negative for {product.sku}."
                )
            product_map[item["product"]] = product

            if po and item["product"] in po_item_map:
                poi = po_item_map[item["product"]]
                remaining = Decimal(poi.quantity_ordered) - Decimal(poi.quantity_received)
                if Decimal(item["quantity_received"]) > remaining:
                    raise ValidationError(
                        f"Cannot receive {item['quantity_received']} of "
                        f"{product.sku}; only {remaining} remaining on PO."
                    )

        grn = GoodsReceivedNote.objects.create(
            grn_number=next_number("GRN", prefix="GRN-", width=6),
            po=po,
            supplier=supplier,
            received_by=user,
            location=location,
        )

        for item in items:
            product = product_map[item["product"]]
            qty = q(item["quantity_received"])
            unit_cost = q(item["unit_cost"])

            po_item = po_item_map.get(product.pk) if po else None

            GoodsReceivedItem.objects.create(
                grn=grn,
                po_item=po_item,
                product=product,
                quantity_received=qty,
                unit_cost=unit_cost,
            )

            # 1) Stock in
            StockService.receive(
                product=product,
                location=location,
                quantity=qty,
                grn_reference=grn.grn_number,
                unit_cost=unit_cost,
                user=user,
            )

            # 2) Update PO line
            if po_item:
                po_item.quantity_received = q(
                    Decimal(po_item.quantity_received) + qty
                )
                po_item.save(update_fields=["quantity_received"])

            # 3) Supplier price sync
            SupplierService.record_purchase_price(
                supplier_id=supplier.pk,
                product_id=product.pk,
                unit_cost=unit_cost,
            )

        # 4) PO status refresh
        if po:
            from .purchase_order_service import PurchaseOrderService
            PurchaseOrderService.refresh_status_from_receipts(po)

        return grn

    # ---- Helpers ------------------------------------------
    @staticmethod
    def default_receipt_items_for_po(po: PurchaseOrder) -> list[dict]:
        """Build the payload that receives all outstanding PO lines."""
        out = []
        for poi in po.items.all():
            remaining = Decimal(poi.quantity_ordered) - Decimal(poi.quantity_received)
            if remaining > 0:
                out.append({
                    "product": poi.product_id,
                    "quantity_received": str(remaining),
                    "unit_cost": str(poi.unit_cost),
                })
        return out