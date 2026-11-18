from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.inventory.models import Category, Product, StockLocation
from apps.purchasing.models import PurchaseOrder
from apps.suppliers.models import Supplier


User = get_user_model()


class PurchaseOrderTests(APITestCase):
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
            code="SUP-0001", name="Parts Co", phone="0700000001",
        )
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        self.location = StockLocation.objects.create(name="Shop")

    def _payload(self, **overrides):
        base = {
            "supplier": self.supplier.pk,
            "expected_date": "2026-12-01",
            "items": [
                {
                    "product": self.product.pk,
                    "quantity_ordered": "10.00",
                    "unit_cost": "80.00",
                },
            ],
            "tax_rate": "16.00",
        }
        base.update(overrides)
        return base

    def test_create_po_computes_totals(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/purchasing/purchase-orders/", self._payload(), format="json",
        )
        self.assertEqual(res.status_code, 201)
        po = PurchaseOrder.objects.get(pk=res.data["id"])
        self.assertEqual(po.subtotal, Decimal("800.00"))
        self.assertEqual(po.tax, Decimal("128.00"))
        self.assertEqual(po.total, Decimal("928.00"))
        self.assertEqual(po.status, "DRAFT")
        self.assertTrue(po.po_number.startswith("PO-"))

    def test_helper_cannot_create_po(self):
        self.client.force_authenticate(self.helper)
        res = self.client.post(
            "/api/purchasing/purchase-orders/", self._payload(), format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_duplicate_products_rejected(self):
        self.client.force_authenticate(self.boss)
        payload = self._payload()
        payload["items"].append(payload["items"][0])
        res = self.client.post(
            "/api/purchasing/purchase-orders/", payload, format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_send_po_transitions(self):
        self.client.force_authenticate(self.boss)
        create = self.client.post(
            "/api/purchasing/purchase-orders/", self._payload(), format="json",
        )
        po_id = create.data["id"]
        res = self.client.post(f"/api/purchasing/purchase-orders/{po_id}/send/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "SENT")

    def test_cancel_draft_po(self):
        self.client.force_authenticate(self.boss)
        create = self.client.post(
            "/api/purchasing/purchase-orders/", self._payload(), format="json",
        )
        po_id = create.data["id"]
        res = self.client.post(f"/api/purchasing/purchase-orders/{po_id}/cancel/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "CANCELLED")

    def test_outstanding_endpoint(self):
        self.client.force_authenticate(self.boss)
        create = self.client.post(
            "/api/purchasing/purchase-orders/", self._payload(), format="json",
        )
        po_id = create.data["id"]
        res = self.client.get(f"/api/purchasing/purchase-orders/{po_id}/outstanding/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["remaining"], "10.00")