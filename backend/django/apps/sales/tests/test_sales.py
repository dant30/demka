from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.inventory.models import Category, Product, StockLevel, StockLocation
from apps.inventory.services import StockService
from apps.payments.models import Payment, PaymentMethod
from apps.sales.models import Sale
from apps.sales.services import SaleService


User = get_user_model()


class SaleServiceTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
            credit_limit=Decimal("20000.00"),
        )
        self.shop = StockLocation.objects.create(
            name="Main Shop", location_type="SHOP",
        )
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        StockService.adjust(
            self.product, self.shop, Decimal("50"),
            movement_type="PURCHASE", user=self.boss,
        )
        # seed payment methods
        PaymentMethod.objects.get_or_create(
            code="CASH", defaults={"name": "Cash", "requires_reference": False},
        )

    def _payload(self, **overrides):
        base = {
            "channel": "SHOP",
            "sale_type": "STANDARD",
            "customer": self.customer.pk,
            "location": self.shop.pk,
            "items": [
                {"product": self.product.pk, "quantity": "3", "unit_price": "130"},
            ],
            "amount_paid": "0",
            "payment_method": "CASH",
        }
        base.update(overrides)
        return base

    def test_create_and_confirm_cash_sale(self):
        sale = SaleService.create_sale(
            self._payload(amount_paid="452.40"), self.helper,
        )
        self.assertEqual(sale.status, "PAID")
        self.assertFalse(sale.is_credit_sale)
        self.assertEqual(sale.total, Decimal("452.40"))
        payment = Payment.objects.get(sale=sale)
        self.assertEqual(payment.amount, Decimal("452.40"))
        # Stock reduced
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("47"))

    def test_credit_sale_updates_customer_balance(self):
        sale = SaleService.create_sale(
            self._payload(amount_paid="0"), self.boss,
        )
        self.assertTrue(sale.is_credit_sale)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, sale.total)

    def test_credit_limit_exceeded(self):
        from core.exceptions.domain import CreditLimitExceededError
        # Credit limit 20000 → set a quantity that exceeds it
        StockService.adjust(
            self.product, self.shop, Decimal("500"),
            movement_type="PURCHASE", user=self.boss,
        )
        big = {
            "channel": "SHOP", "sale_type": "STANDARD",
            "customer": self.customer.pk, "location": self.shop.pk,
            "items": [{"product": self.product.pk, "quantity": "500", "unit_price": "130"}],
            "amount_paid": "0",
        }
        with self.assertRaises(CreditLimitExceededError):
            SaleService.create_sale(big, self.boss)

    def test_insufficient_stock_leaves_sale_draft(self):
        from core.exceptions.domain import InsufficientStockError
        payload = self._payload(
            items=[{"product": self.product.pk, "quantity": "999", "unit_price": "130"}],
            amount_paid="0",
        )
        with self.assertRaises(InsufficientStockError):
            SaleService.create_sale(payload, self.boss)
        self.assertFalse(Sale.objects.exists())

    def test_cancel_restores_stock(self):
        sale = SaleService.create_sale(self._payload(amount_paid="0"), self.boss)
        # Credit sale, no payments applied yet
        SaleService.cancel(sale.pk, self.boss, "Customer changed mind")
        sale.refresh_from_db()
        self.assertEqual(sale.status, "CANCELLED")
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("50"))
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("0"))

    def test_cannot_cancel_with_payments(self):
        from core.exceptions.domain import ConflictError
        sale = SaleService.create_sale(self._payload(amount_paid="100"), self.boss)
        # amount_paid > 0 → refuse
        with self.assertRaises(ConflictError):
            SaleService.cancel(sale.pk, self.boss, "Try")

    def test_apply_payment_partial(self):
        sale = SaleService.create_sale(self._payload(amount_paid="0"), self.boss)
        payment = SaleService.apply_payment(
            sale.pk,
            {"amount": "100", "method": "CASH"},
            self.boss,
        )
        sale.refresh_from_db()
        self.assertEqual(sale.amount_paid, Decimal("100"))
        self.assertEqual(sale.status, "PARTIAL")
        self.assertEqual(payment.amount, Decimal("100"))

    def test_apply_payment_fully_paid(self):
        sale = SaleService.create_sale(self._payload(amount_paid="0"), self.boss)
        SaleService.apply_payment(
            sale.pk,
            {"amount": str(sale.total), "method": "CASH"},
            self.boss,
        )
        sale.refresh_from_db()
        self.assertEqual(sale.status, "PAID")
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("0"))

    def test_preview_does_not_persist(self):
        result = SaleService.preview(self._payload(), self.boss)
        self.assertEqual(result["total"], "452.40")
        self.assertEqual(Sale.objects.count(), 0)
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("50"))