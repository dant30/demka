from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.customers.models import Customer
from apps.inventory.models import Category, Product, StockLevel, StockLocation
from apps.inventory.services import StockService
from apps.payments.models import PaymentMethod
from apps.sales.models import SpecialOrder
from apps.sales.services import SaleService, SpecialOrderService
from apps.suppliers.models import Supplier


User = get_user_model()


class SpecialOrderTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
            credit_limit=Decimal("50000.00"),
        )
        self.shop = StockLocation.objects.create(name="Shop", location_type="SHOP")
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU-SO", name="Rare Part", category=cat,
            cost_price=1000, retail_price=1500, wholesale_price=1300,
            is_stocked=False,
        )
        self.supplier = Supplier.objects.create(
            code="SUP-0001", name="Importer", phone="0700000001",
        )
        PaymentMethod.objects.get_or_create(
            code="CASH", defaults={"name": "Cash", "requires_reference": False},
        )

    def _payload(self, **overrides):
        base = {
            "channel": "SHOP",
            "sale_type": "SPECIAL_ORDER",
            "customer": self.customer.pk,
            "location": self.shop.pk,
            "items": [
                {
                    "product": self.product.pk,
                    "quantity": "1",
                    "unit_price": "1300",
                    "supplier": self.supplier.pk,
                    "expected_arrival_date": "2026-12-01",
                    "customer_deposit": "500",
                },
            ],
            "amount_paid": "500",
            "payment_method": "CASH",
        }
        base.update(overrides)
        return base

    def test_special_order_created_no_stock_deduction(self):
        sale = SaleService.create_sale(self._payload(), self.boss)
        self.assertEqual(sale.status, "PARTIAL")  # deposit only
        self.assertEqual(sale.sale_type, "SPECIAL_ORDER")
        # No stock changes
        self.assertFalse(StockLevel.objects.filter(product=self.product).exists())
        so = SpecialOrder.objects.get(sale_item__sale=sale)
        self.assertEqual(so.status, "ORDERED")

    def test_mark_arrived_then_delivered(self):
        sale = SaleService.create_sale(self._payload(), self.boss)
        so = SpecialOrder.objects.get(sale_item__sale=sale)
        SpecialOrderService.mark_arrived(so.pk, self.boss)
        so.refresh_from_db()
        self.assertEqual(so.status, "ARRIVED")

        # Simulate GRN delivering stock
        StockService.adjust(
            self.product, self.shop, Decimal("1"),
            movement_type="PURCHASE", user=self.boss,
        )

        SpecialOrderService.mark_delivered(so.pk, self.boss)
        so.refresh_from_db()
        self.assertEqual(so.status, "DELIVERED")
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("0"))