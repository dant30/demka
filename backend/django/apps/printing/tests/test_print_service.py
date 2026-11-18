from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.printing.models import Printer, PrintJob
from apps.printing.services import PrintService


User = get_user_model()


class PrintServiceTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.printer = Printer.objects.create(
            name="Shop Printer", printer_type=Printer.Type.NETWORK,
            ip_address="192.168.1.50", port=9100,
            paper_width_mm=58, is_default=True,
        )

    def test_queue_test_print(self):
        job = PrintService.queue_test_print(printer_id=self.printer.pk, user=self.boss)
        self.assertEqual(job.status, "QUEUED")
        self.assertGreater(len(bytes(job.escpos_data)), 0)

    def test_dispatch_success(self):
        job = PrintService.queue_test_print(printer_id=self.printer.pk, user=self.boss)
        with patch("apps.printing.services.connectors.socket.create_connection") as mock_conn:
            sock = MagicMock()
            mock_conn.return_value = sock
            result = PrintService.dispatch(job.pk)
        self.assertEqual(result.status, "PRINTED")
        sock.sendall.assert_called_once()

    def test_dispatch_failure(self):
        job = PrintService.queue_test_print(printer_id=self.printer.pk, user=self.boss)
        with patch(
            "apps.printing.services.connectors.socket.create_connection",
            side_effect=ConnectionRefusedError("refused"),
        ):
            result = PrintService.dispatch(job.pk)
        self.assertEqual(result.status, "FAILED")
        self.assertIn("unreachable", result.error_message)

    def test_base64_payload(self):
        job = PrintService.queue_test_print(printer_id=self.printer.pk, user=self.boss)
        data = PrintService.base64_payload(job.pk)
        self.assertEqual(data["job_id"], job.pk)
        self.assertGreater(data["bytes_length"], 0)
        import base64
        self.assertGreater(len(base64.b64decode(data["escpos_base64"])), 0)

    def test_mark_printed_by_client(self):
        job = PrintService.queue_test_print(printer_id=self.printer.pk, user=self.boss)
        result = PrintService.mark_printed_by_client(job.pk, user=self.boss)
        self.assertEqual(result.status, "PRINTED")
        self.assertIsNotNone(result.printed_at)