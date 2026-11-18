from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.customers.models import Customer
from apps.inventory.models import Category, Product, StockLocation
from apps.inventory.services import StockService
from apps.preorders.authentication import PortalUser
from apps.preorders.models import PreorderCustomerSession
from apps.preorders.services import CatalogService


class CatalogTests(TestCase):
    def setUp(self):
        self.shop = StockLocation.objects.create(name="Shop", location_type="SHOP")
        cat = Category.objects.create(name="Engine")
        self.p1 = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        self.p2 = Product.objects.create(
            sku="SKU2", name="Filter", category=cat,
            cost_price=50, retail_price=80, wholesale_price=70,
            is_stocked=False,
        )
        StockService.adjust(
            self.p1, self.shop, Decimal("10"),
            movement_type="PURCHASE", user=None,
        )

    def test_catalog_shows_wholesale_only(self):
        qs = CatalogService.list_products()
        data = [CatalogService.serialize(p) for p in qs]
        for row in data:
            self.assertNotIn("cost_price", row)
            self.assertNotIn("retail_price", row)
            self.assertIn("wholesale_price", row)

    def test_catalog_flags_special_orders(self):
        qs = CatalogService.list_products()
        by_sku = {p.sku: p for p in qs}
        row = CatalogService.serialize(by_sku["SKU2"])
        self.assertTrue(row["is_special_order"])  # not stocked

        row = CatalogService.serialize(by_sku["SKU1"])
        self.assertFalse(row["is_special_order"])  # in stock

    def test_in_stock_filter(self):
        qs = CatalogService.list_products(only_in_stock=True)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().sku, "SKU1")

    def test_search_by_compatibility(self):
        self.p1.compatibility_notes = "Boxer 150"
        self.p1.save()
        qs = CatalogService.list_products(search="Boxer")
        self.assertEqual(qs.count(), 1)