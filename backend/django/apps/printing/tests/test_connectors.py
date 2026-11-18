import socket
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.printing.services.connectors import (
    NetworkConnector,
    PrinterConnectionError,
    SerialConnector,
    USBConnector,
)


class NetworkConnectorTests(SimpleTestCase):
    def test_open_and_write(self):
        with patch("socket.create_connection") as mock_conn:
            sock = MagicMock()
            mock_conn.return_value = sock
            with NetworkConnector("192.168.1.5", 9100) as c:
                c.write(b"hello")
            sock.sendall.assert_called_once_with(b"hello")
            sock.close.assert_called_once()

    def test_open_failure_wraps_error(self):
        with patch("socket.create_connection", side_effect=ConnectionRefusedError):
            with self.assertRaises(PrinterConnectionError):
                NetworkConnector("192.168.1.5").open()


class SerialConnectorTests(SimpleTestCase):
    def test_missing_pyserial_raises(self):
        with patch.dict("sys.modules", {"serial": None}):
            with self.assertRaises(PrinterConnectionError):
                SerialConnector("/dev/rfcomm0").open()


class USBConnectorTests(SimpleTestCase):
    def test_missing_pyusb_raises(self):
        with patch.dict("sys.modules", {"usb": None}):
            with self.assertRaises(PrinterConnectionError):
                USBConnector(0x04B8, 0x0202).open()