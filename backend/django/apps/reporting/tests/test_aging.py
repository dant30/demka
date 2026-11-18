from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.customers.models import Customer
from apps.inventory.models import StockLocation
from apps.reporting.services import CustomerReportingService
from apps.sales.models import Sale


User = get_user_model()


class AgingTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111", password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme", phone="0744444444", customer_type="RESELLER",
        )
        self.shop = StockLocation.objects.create(name="Shop", location_type="SHOP")

    def make_sale(self, days_ago, balance):
        confirmed = timezone.now() - timedelta(days=days_ago)
        return Sale.objects.create(
            sale_number=f"SL-{days_ago}", channel="SHOP", customer=self.customer,
            location=self.shop, agent=self.boss, status="CONFIRMED",
            subtotal=Decimal("1000"), total=Decimal("1160"),
            balance_due=Decimal(balance), is_credit_sale=True, confirmed_at=confirmed,
        )

    def test_aging_buckets(self):
        self.make_sale(10, "500.00")
        self.make_sale(45, "300.00")
        self.make_sale(75, "200.00")
        self.make_sale(120, "150.00")
        summary = CustomerReportingService.aging_summary()
        self.assertEqual(summary["buckets"]["0-30"], "500.00")
        self.assertEqual(summary["buckets"]["31-60"], "300.00")
        self.assertEqual(summary["buckets"]["61-90"], "200.00")
        self.assertEqual(summary["buckets"]["90+"], "150.00")
        self.assertEqual(summary["total_outstanding"], "1150.00")

    def test_aging_detail_contains_customer(self):
        self.make_sale(10, "500.00")
        rows = CustomerReportingService.aging_detail()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["customer_code"], "CUST-0001")
        self.assertEqual(rows[0]["bucket"], "0-30")
