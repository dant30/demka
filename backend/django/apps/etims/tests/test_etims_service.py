from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.common.models import TaxRate
from apps.customers.models import Customer
from apps.etims.models import EtimsConfig, EtimsInvoice, EtimsItem
from apps.etims.services import ETIMSService
from apps.inventory.models import Category, Product, StockLocation
from apps.inventory.services import StockService
from apps.payments.models import PaymentMethod
from apps.sales.services import SaleService
from apps.accounts.models import User


class EtimsSubmissionTests(TestCase):
    def setUp(self):
        cfg = EtimsConfig.get_solo()
        cfg.tin = "P051234567A"
        cfg.bhf_id = "00"
        cfg.device_serial = "DEV-1"
        cfg.cmc_key = "KEY-ABC"
        cfg.environment = EtimsConfig.Environment.SANDBOX
        cfg.is_active = True
        cfg.save()

        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
            kra_pin="P051234567Z",
            credit_limit=Decimal("100000"),
        )
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
            etims_item_cls_cd="5059690800",
        )
        EtimsItem.objects.create(
            product=self.product, item_cd="SKU1",
            item_cls_cd="5059690800", status=EtimsItem.Status.REGISTERED,
        )
        self.shop = StockLocation.objects.create(name="Shop", location_type="SHOP")
        StockService.adjust(
            self.product, self.shop, Decimal("50"),
            movement_type="PURCHASE", user=self.boss,
        )
        PaymentMethod.objects.update_or_create(
            code="CASH", defaults={"name": "Cash", "is_active": True},
        )

    @patch("apps.etims.services.client.requests.Session.post")
    def test_successful_submission_stamps_invoice(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "resultCd": "000", "resultMsg": "Successful",
            "data": {"curRcptNo": 87, "totRcptNo": 1042,
                     "intrlData": "INTRL", "rcptSign": "SIGN",
                     "sdcDateTime": "20260101120000"},
        }
        sale = SaleService.create_sale(
            {
                "channel": "SHOP", "sale_type": "STANDARD",
                "customer": self.customer.pk, "location": self.shop.pk,
                "items": [{"product": self.product.pk, "quantity": "1"}],
                "amount_paid": "0",
            },
            self.boss,
        )
        inv = ETIMSService.submit_sale(sale.pk)
        self.assertEqual(inv.status, EtimsInvoice.Status.SUBMITTED)
        self.assertEqual(inv.invc_no, 1)
        self.assertEqual(inv.control_code, "INTRL")
        self.assertEqual(inv.receipt_signature, "SIGN")
        self.assertIn("indexEtimsReceiptData", inv.qr_code_data)

    @patch("apps.etims.services.client.requests.Session.post")
    def test_idempotent_resubmit_returns_same_row(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "resultCd": "000", "resultMsg": "Successful",
            "data": {"curRcptNo": 1, "totRcptNo": 1, "intrlData": "X",
                     "rcptSign": "Y", "sdcDateTime": "20260101120000"},
        }
        sale = SaleService.create_sale(
            {
                "channel": "SHOP", "sale_type": "STANDARD",
                "customer": self.customer.pk, "location": self.shop.pk,
                "items": [{"product": self.product.pk, "quantity": "1"}],
                "amount_paid": "0",
            },
            self.boss,
        )
        a = ETIMSService.submit_sale(sale.pk)
        b = ETIMSService.submit_sale(sale.pk)
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(EtimsInvoice.objects.count(), 1)

    @patch("apps.etims.services.client.requests.Session.post")
    def test_rejection_marks_rejected(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "resultCd": "921", "resultMsg": "Duplicate",
        }
        sale = SaleService.create_sale(
            {
                "channel": "SHOP", "sale_type": "STANDARD",
                "customer": self.customer.pk, "location": self.shop.pk,
                "items": [{"product": self.product.pk, "quantity": "1"}],
                "amount_paid": "0",
            },
            self.boss,
        )
        inv = ETIMSService.submit_sale(sale.pk)
        inv.refresh_from_db()
        self.assertEqual(inv.status, EtimsInvoice.Status.REJECTED)
        self.assertIsNone(inv.next_retry_at)

    @patch("apps.etims.services.client.requests.Session.post")
    def test_transient_schedules_retry(self, mock_post):
        mock_post.return_value.status_code = 503
        sale = SaleService.create_sale(
            {
                "channel": "SHOP", "sale_type": "STANDARD",
                "customer": self.customer.pk, "location": self.shop.pk,
                "items": [{"product": self.product.pk, "quantity": "1"}],
                "amount_paid": "0",
            },
            self.boss,
        )
        inv = ETIMSService.submit_sale(sale.pk)
        inv.refresh_from_db()
        self.assertEqual(inv.status, EtimsInvoice.Status.FAILED)
        self.assertIsNotNone(inv.next_retry_at)