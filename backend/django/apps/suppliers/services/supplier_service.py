"""Supplier domain services — linking, pricing, preferred-supplier logic."""
from decimal import Decimal

from django.db import transaction
from django.db.models import Min

from core.exceptions.domain import NotFoundError, ValidationError
from core.utils.money import q


class SupplierService:

    @staticmethod
    def record_purchase_price(
        supplier_id: int,
        product_id: int,
        unit_cost,
        lead_time_days: int | None = None,
    ):
        """
        Called from purchasing when a GRN is received.
        Updates `last_purchase_price` on the existing link or creates one.
        """
        from apps.inventory.models import Product
        from ..models import Supplier, SupplierProduct

        try:
            supplier = Supplier.objects.get(pk=supplier_id)
        except Supplier.DoesNotExist:
            raise NotFoundError("Supplier", supplier_id)
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFoundError("Product", product_id)

        defaults = {"last_purchase_price": q(unit_cost)}
        if lead_time_days is not None:
            defaults["lead_time_days"] = lead_time_days

        obj, _ = SupplierProduct.objects.update_or_create(
            supplier=supplier,
            product=product,
            defaults=defaults,
        )
        return obj

    @staticmethod
    def preferred_supplier_for(product_id: int, prefer_fast: bool = False):
        """
        Return the best SupplierProduct link for a product.
        - Default: cheapest last_purchase_price.
        - prefer_fast=True: shortest lead_time_days, then cheapest as tiebreaker.
        """
        from ..models import SupplierProduct

        qs = SupplierProduct.objects.filter(
            product_id=product_id,
            supplier__is_active=True,
        )
        if not qs.exists():
            return None
        if prefer_fast:
            return qs.order_by("lead_time_days", "last_purchase_price").first()
        return qs.order_by("last_purchase_price", "lead_time_days").first()

    @staticmethod
    def suppliers_for_product(product_id: int):
        from ..models import SupplierProduct

        return (
            SupplierProduct.objects
            .filter(product_id=product_id, supplier__is_active=True)
            .select_related("supplier")
            .order_by("last_purchase_price")
        )

    @staticmethod
    @transaction.atomic
    def deactivate(supplier_id: int) -> None:
        from ..models import Supplier

        try:
            supplier = Supplier.objects.select_for_update().get(pk=supplier_id)
        except Supplier.DoesNotExist:
            raise NotFoundError("Supplier", supplier_id)
        supplier.is_active = False
        supplier.save(update_fields=["is_active"])

    @staticmethod
    def summary_stats(supplier_id: int) -> dict:
        from ..models import Supplier

        try:
            supplier = Supplier.objects.get(pk=supplier_id)
        except Supplier.DoesNotExist:
            raise NotFoundError("Supplier", supplier_id)

        link_qs = supplier.products.all()
        cheapest = link_qs.aggregate(m=Min("last_purchase_price"))["m"]
        avg_lead = (
            link_qs.values_list("lead_time_days", flat=True)
        )
        lead_values = [v for v in avg_lead if v is not None]
        avg_lead_days = (
            round(sum(lead_values) / len(lead_values), 2)
            if lead_values else None
        )
        return {
            "product_count": link_qs.count(),
            "purchase_order_count": supplier.purchase_orders.count(),
            "cheapest_purchase_price": str(cheapest) if cheapest is not None else None,
            "average_lead_time_days": avg_lead_days,
        }