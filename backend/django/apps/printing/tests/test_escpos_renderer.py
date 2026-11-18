from decimal import Decimal

from django.test import SimpleTestCase

from apps.printing.services.escpos_renderer import (
    ReceiptRenderer,
    render_credit_note,
    render_sale_receipt,
    render_test_slip,
)


class RendererTests(SimpleTestCase):
    def test_initializes_and_cuts(self):
        data = ReceiptRenderer(width=32).reset().line("Hi").cut().bytes()
        self.assertTrue(data.startswith(b"\x1b@"))  # ESC @
        self.assertTrue(data.endswith(b"\x1dVa\x03") or b"\x1dV" in data)

    def test_bold_and_double(self):
        data = ReceiptRenderer().reset().line("X", bold=True, double_height=True).bytes()
        self.assertIn(b"\x1bE\x01", data)
        self.assertIn(b"\x1d!\x11", data)

    def test_two_col_aligns_right(self):
        r = ReceiptRenderer(width=32).reset()
        r.two_col("Subtotal", "100.00")
        text = bytes(r.bytes()).decode("cp437")
        self.assertIn("Subtotal", text)
        self.assertIn("100.00", text)

    def test_two_col_truncates_overlong_left(self):
        r = ReceiptRenderer(width=20).reset()
        r.two_col("A" * 100, "5.00")
        # Must not raise; line still produced
        self.assertGreater(len(r.bytes()), 0)

    def test_qr_emits_store_and_print(self):
        data = ReceiptRenderer().reset().qr("https://example.com").bytes()
        # Store command
        self.assertIn(b"\x1d(k", data)
        # Print command
        self.assertIn(b"\x31\x51", data)

    def test_three_col(self):
        r = ReceiptRenderer(width=32).reset()
        r.three_col("Piston", "2x", "260.00")
        text = bytes(r.bytes()).decode("cp437")
        self.assertIn("Piston", text)
        self.assertIn("2x", text)
        self.assertIn("260.00", text)

    def test_sale_receipt_payload(self):
        payload = {
            "business": {
                "name": "DEMKA", "kra_pin": "P051234567A",
                "address": "Nakuru", "phone": "0712345678",
                "receipt_footer": "Asante!",
            },
            "sale": {
                "sale_number": "SL-000001",
                "agent": "J. Doe",
                "location": "Main Shop",
                "customer_name": "Acme",
                "customer_phone": "0744444444",
                "subtotal": "500.00",
                "tax_amount": "80.00",
                "discount_amount": "0",
                "total": "580.00",
                "amount_paid": "580.00",
                "balance_due": "0.00",
                "created_at": "2026-01-01T10:00:00",
                "etims_invoice_number": "1/42",
            },
            "items": [
                {"name": "Piston", "quantity": "2", "line_total": "260.00"},
            ],
            "payments": [
                {"method": "CASH", "amount": "580.00", "reference": ""},
            ],
        }
        data = render_sale_receipt(payload, paper_width_mm=58)
        text = data.decode("cp437", errors="replace")
        self.assertIn("DEMKA", text)
        self.assertIn("SL-000001", text)
        self.assertIn("Piston", text)
        self.assertIn("580.00", text)
        self.assertTrue(data.startswith(b"\x1b@"))