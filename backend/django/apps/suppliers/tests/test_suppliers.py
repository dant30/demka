from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.inventory.models import Category, Product
from apps.suppliers.models import Supplier, SupplierProduct


User = get_user_model()


class SupplierViewSetTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )

    def test_create_supplier_auto_code(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/suppliers/",
            {"name": "Parts Ltd", "phone": "0733333333"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        supplier = Supplier.objects.get(name="Parts Ltd")
        self.assertTrue(supplier.code.startswith("SUP-"))

    def test_create_supplier_custom_code(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/suppliers/",
            {"code": "SUP-X01", "name": "Custom", "phone": "0733333334"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Supplier.objects.get(name="Custom").code, "SUP-X01")

    def test_duplicate_code_rejected(self):
        Supplier.objects.create(code="SUP-DUP", name="A", phone="0700000001")
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/suppliers/",
            {"code": "SUP-DUP", "name": "B", "phone": "0700000002"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_helper_cannot_create_supplier(self):
        self.client.force_authenticate(self.helper)
        res = self.client.post(
            "/api/suppliers/",
            {"name": "Blocked", "phone": "0733333335"},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_helper_can_list_suppliers(self):
        Supplier.objects.create(code="SUP-0001", name="X", phone="0700000003")
        self.client.force_authenticate(self.helper)
        res = self.client.get("/api/suppliers/")
        self.assertEqual(res.status_code, 200)

    def test_search_by_name(self):
        Supplier.objects.create(code="SUP-A", name="Nakuru Parts", phone="0700000004")
        Supplier.objects.create(code="SUP-B", name="Eldoret Spares", phone="0700000005")
        self.client.force_authenticate(self.boss)
        res = self.client.get("/api/suppliers/?search=Nakuru")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 1)

    def test_stats_endpoint(self):
        supplier = Supplier.objects.create(code="SUP-S", name="S", phone="0700000006")
        self.client.force_authenticate(self.boss)
        res = self.client.get(f"/api/suppliers/{supplier.pk}/stats/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["product_count"], 0)

    def test_deactivate_endpoint(self):
        supplier = Supplier.objects.create(code="SUP-D", name="D", phone="0700000007")
        self.client.force_authenticate(self.boss)
        res = self.client.post(f"/api/suppliers/{supplier.pk}/deactivate/")
        self.assertEqual(res.status_code, 200)
        supplier.refresh_from_db()
        self.assertFalse(supplier.is_active)


class SupplierProductTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )
        self.supplier = Supplier.objects.create(
            code="SUP-0001", name="S1", phone="0700000001",
        )
        cat = Category.objects.create(name="Engine", applies_to="BOTH")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )

    def test_create_link(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/suppliers/products/",
            {
                "supplier": self.supplier.pk,
                "product": self.product.pk,
                "last_purchase_price": "90.00",
                "lead_time_days": 3,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(
            SupplierProduct.objects.filter(
                supplier=self.supplier, product=self.product
            ).exists()
        )

    def test_duplicate_link_rejected(self):
        SupplierProduct.objects.create(
            supplier=self.supplier, product=self.product,
            last_purchase_price=90,
        )
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/suppliers/products/",
            {
                "supplier": self.supplier.pk,
                "product": self.product.pk,
                "last_purchase_price": "80.00",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_helper_cannot_see_purchase_price(self):
        SupplierProduct.objects.create(
            supplier=self.supplier, product=self.product,
            last_purchase_price=90,
        )
        self.client.force_authenticate(self.helper)
        res = self.client.get("/api/suppliers/products/")
        self.assertEqual(res.status_code, 200)
        row = res.data["results"][0]
        self.assertNotIn("last_purchase_price", row)

    def test_boss_can_see_purchase_price(self):
        SupplierProduct.objects.create(
            supplier=self.supplier, product=self.product,
            last_purchase_price=90,
        )
        self.client.force_authenticate(self.boss)
        res = self.client.get("/api/suppliers/products/")
        row = res.data["results"][0]
        self.assertIn("last_purchase_price", row)
        self.assertEqual(row["last_purchase_price"], "90.00")

    def test_helper_cannot_set_purchase_price(self):
        self.client.force_authenticate(self.helper)
        res = self.client.post(
            "/api/suppliers/products/",
            {
                "supplier": self.supplier.pk,
                "product": self.product.pk,
                "last_purchase_price": "80.00",
            },
            format="json",
        )
        # Permission gate (CanManageSuppliers) rejects before serializer runs
        self.assertEqual(res.status_code, 403)

    def test_preferred_supplier_cheapest(self):
        s2 = Supplier.objects.create(code="SUP-0002", name="S2", phone="0700000002")
        SupplierProduct.objects.create(
            supplier=self.supplier, product=self.product,
            last_purchase_price=120, lead_time_days=2,
        )
        SupplierProduct.objects.create(
            supplier=s2, product=self.product,
            last_purchase_price=90, lead_time_days=7,
        )
        self.client.force_authenticate(self.boss)
        res = self.client.get(f"/api/suppliers/products/preferred/{self.product.pk}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["supplier"], s2.pk)

    def test_preferred_supplier_fastest(self):
        s2 = Supplier.objects.create(code="SUP-0002", name="S2", phone="0700000002")
        SupplierProduct.objects.create(
            supplier=self.supplier, product=self.product,
            last_purchase_price=120, lead_time_days=2,
        )
        SupplierProduct.objects.create(
            supplier=s2, product=self.product,
            last_purchase_price=90, lead_time_days=7,
        )
        self.client.force_authenticate(self.boss)
        res = self.client.get(
            f"/api/suppliers/products/preferred/{self.product.pk}/?prefer_fast=true"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["supplier"], self.supplier.pk)