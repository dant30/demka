from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.inventory.models import Category, Product, StockLevel, StockLocation
from apps.inventory.services import StockService
from apps.payments.models import PaymentMethod
from apps.sales.services import ReturnService, SaleService


User = get_user_model()


class ReturnServiceTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RETAIL",
        )
        self.shop = StockLocation.objects.create(name="Shop", location_type="SHOP")
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        StockService.adjust(
            self.product, self.shop, Decimal("20"),
            movement_type="PURCHASE", user=self.boss,
        )
        PaymentMethod.objects.get_or_create(
            code="CASH", defaults={"name": "Cash", "requires_reference": False},
        )
        self.sale = SaleService.create_sale(
            {
                "channel": "SHOP", "sale_type": "STANDARD",
                "customer": self.customer.pk, "location": self.shop.pk,
                "items": [{"product": self.product.pk, "quantity": "5", "unit_price": "150"}],
                "amount_paid": "870",  # fully paid
                "payment_method": "CASH",
            },
            self.boss,
        )
        self.sale_item = self.sale.items.first()

    def test_return_partial_item(self):
        ret = ReturnService.create_return(
            {
                "original_sale": self.sale.pk,
                "reason": "Wrong part",
                "items": [{"sale_item": self.sale_item.pk, "quantity": "2", "restock": True}],
            },
            self.boss,
        )
        self.assertEqual(ret.status, "DRAFT")
        ReturnService.approve(ret.pk, self.boss)
        ReturnService.complete(ret.pk, self.boss)
        ret.refresh_from_db()
        self.assertEqual(ret.status, "COMPLETED")
        self.sale_item.refresh_from_db()
        self.assertEqual(self.sale_item.returned_quantity, Decimal("2"))
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("17"))  # 20 - 5 + 2

    def test_return_more_than_sold_rejected(self):
        from core.exceptions.domain import ValidationError
        with self.assertRaises(ValidationError):
            ReturnService.create_return(
                {
                    "original_sale": self.sale.pk,
                    "items": [{"sale_item": self.sale_item.pk, "quantity": "10"}],
                },
                self.boss,
            )

    def test_full_return_flips_sale_status(self):
        ret = ReturnService.create_return(
            {
                "original_sale": self.sale.pk,
                "items": [{"sale_item": self.sale_item.pk, "quantity": "5"}],
            },
            self.boss,
        )
        ReturnService.approve(ret.pk, self.boss)
        ReturnService.complete(ret.pk, self.boss)
        self.sale.refresh_from_db()
        self.assertEqual(self.sale.status, "RETURNED")

    def test_no_restock_skips_stock_increase(self):
        ret = ReturnService.create_return(
            {
                "original_sale": self.sale.pk,
                "items": [{"sale_item": self.sale_item.pk, "quantity": "2", "restock": False}],
            },
            self.boss,
        )
        ReturnService.approve(ret.pk, self.boss)
        ReturnService.complete(ret.pk, self.boss)
        level = StockLevel.objects.get(product=self.product, location=self.shop)
        self.assertEqual(level.quantity, Decimal("15"))  # 20 - 5, no +2

    def test_cannot_complete_unapproved(self):
        from core.exceptions.domain import ConflictError
        ret = ReturnService.create_return(
            {
                "original_sale": self.sale.pk,
                "items": [{"sale_item": self.sale_item.pk, "quantity": "1"}],
            },
            self.boss,
        )
        with self.assertRaises(ConflictError):
            ReturnService.complete(ret.pk, self.boss)