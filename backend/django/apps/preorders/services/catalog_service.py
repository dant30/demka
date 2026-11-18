"""Customer-facing catalog — wholesale pricing, aggregate stock, no cost leakage."""
from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from core.exceptions.domain import NotFoundError

from ..serializers.catalog import CatalogProductSerializer


class CatalogService:

    @staticmethod
    def _base_queryset():
        from apps.inventory.models import Product

        shop_q = Q(
            levels__location__location_type__in=["SHOP", "WAREHOUSE"],
            levels__location__is_active=True,
        )
        return (
            Product.objects
            .filter(is_active=True)
            .select_related("category")
            .annotate(
                available_qty=Coalesce(
                    Sum("levels__quantity", filter=shop_q),
                    Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2)),
                ),
            )
        )

    @classmethod
    def list_products(cls, *, search="", category_id=None, only_in_stock=False):
        qs = cls._base_queryset()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(sku__icontains=search) |
                Q(part_number__icontains=search) |
                Q(brand__icontains=search) |
                Q(compatibility_notes__icontains=search)
            )
        if category_id:
            qs = qs.filter(category_id=category_id)
        if only_in_stock:
            qs = qs.filter(available_qty__gt=0)
        return qs.order_by("category__name", "name")

    @classmethod
    def get_product(cls, product_id: int):
        product = cls._base_queryset().filter(pk=product_id).first()
        if not product:
            raise NotFoundError("Product", product_id)
        return product

    @staticmethod
    def serialize(product) -> dict:
        return CatalogProductSerializer(product).data