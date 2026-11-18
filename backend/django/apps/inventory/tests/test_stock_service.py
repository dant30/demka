from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.inventory.models import (
    Category, Product, StockLevel, StockLocation, StockMovement,
)
from apps.inventory.services import StockService
from core.exceptions.domain import InsufficientStockError


class StockServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        self.shop = StockLocation.objects.create(name="Main Shop", location_type="SHOP")

    def test_adjust_creates_level_and_movement(self):
        level, movement = StockService.adjust(
            product=self.product, location=self.shop, delta=Decimal("10"),
            movement_type="PURCHASE", user=self.user,
        )
        self.assertEqual(level.quantity, Decimal("10"))
        self.assertEqual(movement.quantity, Decimal("10"))
        self.assertEqual(movement.movement_type, "PURCHASE")

    def test_sell_reduces_stock(self):
        StockService.adjust(
            self.product, self.shop, Decimal("10"),
            movement_type="PURCHASE", user=self.user,
        )
        StockService.sell(
            self.product, self.shop, Decimal("3"),
            sale_reference="SAL-001", user=self.user,
        )
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("7"))

    def test_sell_insufficient_raises(self):
        StockService.adjust(
            self.product, self.shop, Decimal("2"),
            movement_type="PURCHASE", user=self.user,
        )
        with self.assertRaises(InsufficientStockError):
            StockService.sell(
                self.product, self.shop, Decimal("5"),
                sale_reference="SAL-002", user=self.user,
            )
        # Quantity unchanged
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("2"))

    def test_return_increases_stock(self):
        StockService.adjust(
            self.product, self.shop, Decimal("5"),
            movement_type="PURCHASE", user=self.user,
        )
        StockService.return_to_stock(
            self.product, self.shop, Decimal("2"),
            return_reference="RET-001", user=self.user,
        )
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("7"))

    def test_available_returns_zero_when_no_level(self):
        self.assertEqual(
            StockService.available(self.product, self.shop), Decimal("0"),
        )

    def test_snapshot_total_value(self):
        StockService.adjust(
            self.product, self.shop, Decimal("10"),
            movement_type="PURCHASE", user=self.user,
        )
        snap = StockService.snapshot(self.shop)
        self.assertEqual(snap["total_units"], "10.00")
        self.assertEqual(snap["total_value"], "1000.00")