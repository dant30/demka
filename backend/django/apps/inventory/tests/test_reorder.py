from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.inventory.models import (
    Category, Product, StockLevel, StockLocation,
)
from apps.inventory.services import ReorderService, StockService
from apps.inventory.views.api.product_views import ProductFilterSet


class ReorderTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
            reorder_level=5, reorder_qty=20,
        )
        self.shop = StockLocation.objects.create(name="Shop")

    def test_product_at_reorder_flagged(self):
        StockService.adjust(
            self.product, self.shop, Decimal("5"),
            movement_type="PURCHASE", user=self.user,
        )
        lows = list(ReorderService.low_stock_levels())
        self.assertEqual(len(lows), 1)
        self.assertEqual(lows[0].product, self.product)

    def test_product_above_reorder_not_flagged(self):
        StockService.adjust(
            self.product, self.shop, Decimal("10"),
            movement_type="PURCHASE", user=self.user,
        )
        self.assertEqual(len(list(ReorderService.low_stock_levels())), 0)

    def test_per_location_override(self):
        StockService.adjust(
            self.product, self.shop, Decimal("3"),
            movement_type="PURCHASE", user=self.user,
        )
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        level.reorder_level = 2  # override — 3 > 2, not flagged
        level.save()
        self.assertEqual(len(list(ReorderService.low_stock_levels())), 0)

    def test_product_filter_returns_low_stock_products(self):
        StockService.adjust(
            self.product, self.shop, Decimal("5"),
            movement_type="PURCHASE", user=self.user,
        )
        queryset = ProductFilterSet(
            {"needs_reorder": "true"}, queryset=Product.objects.all(),
        ).qs
        self.assertEqual(list(queryset), [self.product])

    def test_product_filter_respects_location_reorder_override(self):
        StockService.adjust(
            self.product, self.shop, Decimal("3"),
            movement_type="PURCHASE", user=self.user,
        )
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        level.reorder_level = 2
        level.save()
        queryset = ProductFilterSet(
            {"needs_reorder": "true"}, queryset=Product.objects.all(),
        ).qs
        self.assertFalse(queryset.exists())

    def test_unstocked_product_excluded(self):
        self.product.is_stocked = False
        self.product.save()
        StockService.adjust(
            self.product, self.shop, Decimal("1"),
            movement_type="ADJUSTMENT", user=self.user,
        )
        self.assertEqual(len(list(ReorderService.low_stock_levels())), 0)

    def test_suggested_quantity_uses_product_reorder_qty(self):
        StockService.adjust(
            self.product, self.shop, Decimal("2"),
            movement_type="PURCHASE", user=self.user,
        )
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(ReorderService.suggested_quantity(level), Decimal("20"))