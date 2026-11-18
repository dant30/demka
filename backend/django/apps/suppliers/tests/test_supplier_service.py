from decimal import Decimal

from django.test import TestCase

from apps.inventory.models import Category, Product
from apps.suppliers.models import Supplier, SupplierProduct
from apps.suppliers.services import SupplierService


class SupplierServiceTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            code="SUP-0001", name="S1", phone="0700000001",
        )
        cat = Category.objects.create(name="Engine", applies_to="BOTH")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )

    def test_record_purchase_price_creates_link(self):
        link = SupplierService.record_purchase_price(
            self.supplier.pk, self.product.pk, Decimal("85.50"), lead_time_days=4,
        )
        self.assertEqual(link.last_purchase_price, Decimal("85.50"))
        self.assertEqual(link.lead_time_days, 4)

    def test_record_purchase_price_updates_existing(self):
        SupplierProduct.objects.create(
            supplier=self.supplier, product=self.product,
            last_purchase_price=Decimal("90.00"), lead_time_days=2,
        )
        link = SupplierService.record_purchase_price(
            self.supplier.pk, self.product.pk, Decimal("85.00"),
        )
        self.assertEqual(link.last_purchase_price, Decimal("85.00"))
        self.assertEqual(link.lead_time_days, 2)  # unchanged

    def test_preferred_supplier_none_when_no_links(self):
        self.assertIsNone(SupplierService.preferred_supplier_for(self.product.pk))

    def test_summary_stats(self):
        SupplierProduct.objects.create(
            supplier=self.supplier, product=self.product,
            last_purchase_price=Decimal("90.00"), lead_time_days=3,
        )
        stats = SupplierService.summary_stats(self.supplier.pk)
        self.assertEqual(stats["product_count"], 1)
        self.assertEqual(stats["cheapest_purchase_price"], "90.00")
        self.assertEqual(stats["average_lead_time_days"], 3)