from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from openpyxl import Workbook
from rest_framework.test import APITestCase

from apps.inventory.models import Category, Product
from apps.inventory.services.product_import_service import ProductImportService


User = get_user_model()


def _make_xlsx(rows: list[list]) -> SimpleUploadedFile:
    wb = Workbook()
    ws = wb.active
    headers = [
        "sku", "name", "category", "product_type", "brand", "unit",
        "cost_price", "retail_price", "wholesale_price", "is_stocked",
        "reorder_level", "reorder_qty", "barcode", "compatibility_notes",
        "etims_item_cls_cd", "part_number",
    ]
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile(
        "products.xlsx",
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


class ProductImportServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="boss", phone="0711111111", password="Secret123", role="BOSS",
        )

    def test_preview_valid_file(self):
        file = _make_xlsx([
            ["AUTO-001", "Oil Filter", "Engine", "AUTO_PART", "Toyota", "PIECE",
             450, 550, 500, "TRUE", 20, 50, "", "", ""],
        ])
        result = ProductImportService.import_file(file, user=self.user, mode="preview")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["valid"], 1)
        self.assertEqual(result["invalid"], 0)
        self.assertEqual(result["created"], 0)  # preview does not create

    def test_commit_creates_products(self):
        file = _make_xlsx([
            ["AUTO-002", "Brake Pad", "Braking", "AUTO_PART", "Toyota", "PIECE",
             350, 500, 450, "TRUE", 15, 40, "", "", ""],
        ])
        result = ProductImportService.import_file(file, user=self.user, mode="commit")
        self.assertEqual(result["created"], 1)
        self.assertEqual(Product.objects.count(), 1)
        p = Product.objects.get(sku="AUTO-002")
        self.assertEqual(p.retail_price, Decimal("500.00"))
        self.assertTrue(p.is_stocked)

    def test_part_number_is_imported(self):
        file = _make_xlsx([
            ["AUTO-010", "Oil Filter", "Engine", "AUTO_PART", "Toyota", "PIECE",
             450, 550, 500, "TRUE", 20, 50, "", "", "", "21050"],
        ])
        ProductImportService.import_file(file, user=self.user, mode="commit")
        self.assertEqual(Product.objects.get(sku="AUTO-010").part_number, "21050")

    def test_blank_is_stocked_defaults_to_order_on_demand(self):
        file = _make_xlsx([
            ["AUTO-009", "Order Item", "Engine", "AUTO_PART", "", "PIECE",
             100, 150, 130, "", 0, 0, "", "", ""],
        ])
        ProductImportService.import_file(file, user=self.user, mode="commit")
        self.assertFalse(Product.objects.get(sku="AUTO-009").is_stocked)

    def test_commit_is_atomic_on_error(self):
        file = _make_xlsx([
            ["AUTO-003", "Good Product", "Engine", "AUTO_PART", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
            ["", "Bad Product", "Engine", "AUTO_PART", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
        ])
        result = ProductImportService.import_file(file, user=self.user, mode="commit")
        self.assertEqual(result["created"], 0)
        self.assertTrue(result.get("aborted"))
        self.assertEqual(Product.objects.count(), 0)

    def test_skip_errors_imports_valid_rows(self):
        file = _make_xlsx([
            ["AUTO-004", "Good", "Engine", "AUTO_PART", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
            ["", "Bad", "Engine", "AUTO_PART", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
        ])
        result = ProductImportService.import_file(
            file, user=self.user, mode="commit", skip_errors=True,
        )
        self.assertEqual(result["created"], 1)
        self.assertEqual(Product.objects.count(), 1)

    def test_duplicate_sku_within_file(self):
        file = _make_xlsx([
            ["AUTO-005", "A", "Engine", "AUTO_PART", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
            ["AUTO-005", "B", "Engine", "AUTO_PART", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
        ])
        result = ProductImportService.import_file(file, user=self.user, mode="preview")
        self.assertEqual(result["invalid"], 1)

    def test_category_auto_created(self):
        file = _make_xlsx([
            ["AUTO-006", "A", "Brand New Category", "AUTO_PART", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
        ])
        self.assertFalse(Category.objects.filter(name__iexact="Brand New Category").exists())
        ProductImportService.import_file(file, user=self.user, mode="commit")
        self.assertTrue(Category.objects.filter(name__iexact="Brand New Category").exists())

    def test_price_below_cost_is_warning_not_error(self):
        file = _make_xlsx([
            ["AUTO-007", "Cheap", "Engine", "AUTO_PART", "", "PIECE",
             200, 150, 130, "TRUE", 10, 20, "", "", ""],
        ])
        result = ProductImportService.import_file(file, user=self.user, mode="preview")
        self.assertEqual(result["invalid"], 0)
        self.assertEqual(result["warnings"], 1)

    def test_invalid_product_type_rejected(self):
        file = _make_xlsx([
            ["AUTO-008", "A", "Engine", "WIDGET", "", "PIECE",
             100, 150, 130, "TRUE", 10, 20, "", "", ""],
        ])
        result = ProductImportService.import_file(file, user=self.user, mode="preview")
        self.assertEqual(result["invalid"], 1)


class ProductImportApiPermissionTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="import-boss", phone="0711111112", password="Secret123", role="BOSS",
        )
        self.staff = User.objects.create_user(
            username="import-staff", phone="0711111113", password="Secret123", role="SALES_HELPER",
        )

    def test_boss_can_download_template(self):
        self.client.force_authenticate(user=self.boss)
        response = self.client.get("/api/inventory/products/import/template/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_non_boss_cannot_access_import_endpoints(self):
        self.client.force_authenticate(user=self.staff)
        template_response = self.client.get("/api/inventory/products/import/template/")
        import_response = self.client.post("/api/inventory/products/import/")
        self.assertEqual(template_response.status_code, 403)
        self.assertEqual(import_response.status_code, 403)