from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.inventory.models import (
    Category, Product, StockLevel, StockLocation, StockMovement,
)
from apps.inventory.services import StockService
from apps.purchasing.models import PurchaseOrder, PurchaseOrderItem
from apps.purchasing.services import PurchaseOrderService
from apps.suppliers.models import Supplier, SupplierProduct


User = get_user_model()


class GRNTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
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

        # Create and send a PO
        self.po = PurchaseOrderService.create_po(
            data={
                "supplier": self.supplier.pk,
                "items": [
                    {
                        "product": self.product.pk,
                        "quantity_ordered": "10.00",
                        "unit_cost": "80.00",
                    },
                ],
                "tax_rate": "16.00",
            },
            user=self.boss,
        )
        PurchaseOrderService.send(self.po.pk, self.boss)
        self.po.refresh_from_db()

    def test_full_receive_updates_stock_and_po(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/purchasing/grns/",
            {
                "supplier": self.supplier.pk,
                "location": self.location.pk,
                "po": self.po.pk,
                "items": [
                    {
                        "product": self.product.pk,
                        "quantity_received": "10.00",
                        "unit_cost": "80.00",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["grn_number"].startswith("GRN-"))

        # Stock incremented
        level = StockLevel.objects.get(product=self.product, location=self.location)
        self.assertEqual(level.quantity, Decimal("10.00"))

        # Movement logged
        mv = StockMovement.objects.filter(
            product=self.product, movement_type="PURCHASE",
        ).first()
        self.assertIsNotNone(mv)
        self.assertEqual(mv.reference_type, "GoodsReceivedNote")

        # PO fully received
        self.po.refresh_from_db()
        self.assertEqual(self.po.status, "RECEIVED")
        poi = self.po.items.first()
        self.assertEqual(poi.quantity_received, Decimal("10.00"))

        # Supplier product price synced
        link = SupplierProduct.objects.get(
            supplier=self.supplier, product=self.product,
        )
        self.assertEqual(link.last_purchase_price, Decimal("80.00"))

    def test_partial_receive_sets_partial_status(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/purchasing/grns/",
            {
                "supplier": self.supplier.pk,
                "location": self.location.pk,
                "po": self.po.pk,
                "items": [
                    {
                        "product": self.product.pk,
                        "quantity_received": "4.00",
                        "unit_cost": "80.00",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.po.refresh_from_db()
        self.assertEqual(self.po.status, "PARTIAL")
        poi = self.po.items.first()
        self.assertEqual(poi.quantity_received, Decimal("4.00"))

    def test_over_receive_refused(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/purchasing/grns/",
            {
                "supplier": self.supplier.pk,
                "location": self.location.pk,
                "po": self.po.pk,
                "items": [
                    {
                        "product": self.product.pk,
                        "quantity_received": "50.00",
                        "unit_cost": "80.00",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        # Nothing persisted
        self.assertEqual(StockLevel.objects.count(), 0)

    def test_direct_grn_without_po(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/purchasing/grns/",
            {
                "supplier": self.supplier.pk,
                "location": self.location.pk,
                "items": [
                    {
                        "product": self.product.pk,
                        "quantity_received": "5.00",
                        "unit_cost": "85.00",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        level = StockLevel.objects.get(product=self.product, location=self.location)
        self.assertEqual(level.quantity, Decimal("5.00"))

    def test_receive_po_convenience_action(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            f"/api/purchasing/purchase-orders/{self.po.pk}/receive/",
            {"location": self.location.pk},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.po.refresh_from_db()
        self.assertEqual(self.po.status, "RECEIVED")
        level = StockLevel.objects.get(product=self.product, location=self.location)
        self.assertEqual(level.quantity, Decimal("10.00"))

    def test_cancel_po_with_grn_refused(self):
        # Receive one GRN
        self.client.force_authenticate(self.boss)
        self.client.post(
            "/api/purchasing/grns/",
            {
                "supplier": self.supplier.pk,
                "location": self.location.pk,
                "po": self.po.pk,
                "items": [
                    {
                        "product": self.product.pk,
                        "quantity_received": "3.00",
                        "unit_cost": "80.00",
                    },
                ],
            },
            format="json",
        )
        # Attempt cancel
        res = self.client.post(
            f"/api/purchasing/purchase-orders/{self.po.pk}/cancel/",
        )
        self.assertEqual(res.status_code, 409)

    def test_helper_cannot_post_grn(self):
        helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )
        self.client.force_authenticate(helper)
        res = self.client.post(
            "/api/purchasing/grns/",
            {
                "supplier": self.supplier.pk,
                "location": self.location.pk,
                "items": [
                    {
                        "product": self.product.pk,
                        "quantity_received": "1.00",
                        "unit_cost": "80.00",
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 403)