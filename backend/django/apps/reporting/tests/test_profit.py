from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from apps.customers.models import Customer
from apps.expenses.models import Expense, ExpenseCategory
from apps.inventory.models import Category, Product, StockLocation
from apps.inventory.services import StockService
from apps.payments.models import PaymentMethod
from apps.reporting.services import ProfitReportingService
from apps.sales.services import SaleService


User = get_user_model()


class ProfitReportingTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111", password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme", phone="0744444444",
            customer_type="RESELLER", credit_limit=Decimal("100000"),
        )
        self.shop = StockLocation.objects.create(name="Shop", location_type="SHOP")
        category = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=category,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        StockService.adjust(
            self.product, self.shop, Decimal("100"),
            movement_type="PURCHASE", user=self.boss,
        )
        PaymentMethod.objects.update_or_create(
            code="CASH", defaults={"name": "Cash", "is_active": True},
        )

    def _sell_two(self):
        return SaleService.create_sale({
            "channel": "SHOP", "sale_type": "STANDARD",
            "customer": self.customer.pk, "location": self.shop.pk,
            "items": [{"product": self.product.pk, "quantity": "2", "unit_price": "130"}],
            "amount_paid": "301.60", "payment_method": "CASH",
        }, self.boss)

    def test_pnl_simple_sale(self):
        self._sell_two()
        today = timezone.localdate()
        pnl = ProfitReportingService.period_pnl(today, today)
        self.assertEqual(pnl["revenue"]["gross"], "301.60")
        self.assertEqual(pnl["cogs"]["gross"], "200.00")
        self.assertEqual(pnl["gross_profit"], "101.60")

    def test_pnl_with_expenses(self):
        self._sell_two()
        fuel = ExpenseCategory.objects.create(name="Fuel")
        Expense.objects.create(
            expense_number="EXP-001", category=fuel, amount=Decimal("50"),
            expense_date=timezone.localdate(), paid_by=self.boss,
            payment_method=PaymentMethod.objects.get(code="CASH"),
        )
        today = timezone.localdate()
        pnl = ProfitReportingService.period_pnl(today, today)
        self.assertEqual(pnl["net_profit"], "51.60")

    def test_pnl_empty_period(self):
        today = timezone.localdate()
        pnl = ProfitReportingService.period_pnl(today - timedelta(days=30), today - timedelta(days=20))
        self.assertEqual(pnl["revenue"]["net"], "0.00")
        self.assertEqual(pnl["net_profit"], "0.00")
