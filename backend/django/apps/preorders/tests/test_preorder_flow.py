from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.customers.models import Customer
from apps.inventory.models import Category, Product, StockLocation
from apps.inventory.services import StockService
from apps.payments.models import PaymentMethod
from apps.preorders.models import Preorder
from apps.preorders.services import PreorderService
from apps.sales.models import Sale


User = get_user_model()


class PreorderFlowTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
            credit_limit=Decimal("100000"),
        )
        self.shop = StockLocation.objects.create(name="Shop", location_type="SHOP")
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        StockService.adjust(
            self.product, self.shop, Decimal("10"),
            movement_type="PURCHASE", user=self.boss,
        )
        PaymentMethod.objects.update_or_create(
            code="CASH", defaults={"name": "Cash", "is_active": True},
        )

    def _submit(self):
        return PreorderService.submit(
            self.customer,
            {"items": [{"product": self.product.pk, "quantity": "2"}]},
        )

    def test_submit_snapshots_price_and_stock(self):
        p = self._submit()
        self.assertEqual(p.status, "SUBMITTED")
        self.assertTrue(p.preorder_number.startswith("PR-"))
        item = p.items.first()
        self.assertEqual(item.unit_price_estimated, Decimal("130.00"))
        self.assertTrue(item.available_in_stock)
        self.assertEqual(item.available_quantity, Decimal("10"))
        self.assertEqual(p.total_estimated, Decimal("260.00"))

    def test_full_lifecycle_to_delivery(self):
        p = self._submit()
        PreorderService.confirm(p.pk, self.boss)
        PreorderService.prepare(p.pk, self.boss)
        PreorderService.mark_ready(p.pk, self.boss)

        p = PreorderService.deliver(
            p.pk,
            {
                "location": self.shop.pk,
                "payment_method": "CASH",
                "amount_paid": "301.60",
            },
            self.boss,
        )
        self.assertEqual(p.status, "DELIVERED")
        self.assertIsNotNone(p.converted_sale_id)

        sale = Sale.objects.get(pk=p.converted_sale_id)
        self.assertEqual(sale.total, Decimal("301.60"))  # 260.00 + 16% VAT
        self.assertEqual(sale.amount_paid, Decimal("301.60"))
        self.assertEqual(sale.balance_due, Decimal("0.00"))
        # Stock decremented
        from apps.inventory.models import StockLevel
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("8"))

    def test_confirm_with_price_adjustment(self):
        p = self._submit()
        item = p.items.first()
        p = PreorderService.confirm(
            p.pk, self.boss,
            price_adjustments=[{"item": item.pk, "final_price": "120.00"}],
        )
        self.assertEqual(p.total_estimated, Decimal("240.00"))
        item.refresh_from_db()
        self.assertEqual(item.final_price, Decimal("120.00"))

    def test_customer_can_cancel_while_submitted(self):
        p = self._submit()
        PreorderService.cancel(p.pk, None, "Changed mind", by_customer=True)
        p.refresh_from_db()
        self.assertEqual(p.status, "CANCELLED")
        self.assertIsNone(p.cancelled_by)

    def test_customer_cannot_cancel_after_confirm(self):
        from core.exceptions.domain import ConflictError
        p = self._submit()
        PreorderService.confirm(p.pk, self.boss)
        with self.assertRaises(ConflictError):
            PreorderService.cancel(p.pk, None, "Late", by_customer=True)

    def test_deliver_requires_ready(self):
        from core.exceptions.domain import ConflictError
        p = self._submit()
        with self.assertRaises(ConflictError):
            PreorderService.deliver(
                p.pk,
                {"location": self.shop.pk, "payment_method": "CASH", "amount_paid": "0"},
                self.boss,
            )