"""
Transport connectors for the three supported physical paths.

    BaseConnector       abstract write(bytes) / close()
    NetworkConnector    TCP socket (WiFi / Ethernet) to ip:port (default 9100)
    USBConnector        pyusb — vendor_id / product_id
    SerialConnector     pyserial — /dev/ttyUSB0, /dev/rfcomm0, COM3, etc.

`connector_for(printer)` inspects the Printer row and builds the right one.
"""
from __future__ import annotations

import logging
import socket
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Base connector failure."""


class PrinterConnectionError(ConnectorError):
    """Connection refused, host unreachable, permission denied."""


class PrinterUnavailableError(ConnectorError):
    """Printer is offline, out of paper, or unreachable."""


class BaseConnector(ABC):
    """Interface every transport implements."""

    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def write(self, data: bytes) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


# ---------------------------------------------------------------------------
# Network / WiFi
# ---------------------------------------------------------------------------
class NetworkConnector(BaseConnector):
    """
    Raw TCP to the printer's RAW port (9100). Works for any WiFi/Ethernet
    thermal printer that exposes a RAW socket — almost all of them do.
    """
    def __init__(self, host: str, port: int = 9100, *, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def open(self) -> None:
        try:
            self._sock = socket.create_connection(
                (self.host, self.port), timeout=self.timeout,
            )
        except (socket.timeout, ConnectionRefusedError, OSError) as exc:
            raise PrinterConnectionError(
                f"Network printer {self.host}:{self.port} unreachable: {exc}"
            ) from exc

    def write(self, data: bytes) -> None:
        if not self._sock:
            raise PrinterConnectionError("Socket is not open.")
        try:
            self._sock.sendall(data)
        except OSError as exc:
            raise PrinterUnavailableError(
                f"Failed to send to {self.host}:{self.port}: {exc}"
            ) from exc

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass
            finally:
                self._sock.close()
                self._sock = None


# ---------------------------------------------------------------------------
# USB (direct — pyusb)
# ---------------------------------------------------------------------------
class USBConnector(BaseConnector):
    """
    Direct USB via pyusb. Requires:
        pip install pyusb
        system libusb
        Linux: udev rule (or run as root), or use the OS print queue instead
        Windows: WinUSB / Zadig driver binding

    For most shops on Windows, `SerialConnector` with the COM port assigned by
    the vendor driver is more reliable than direct pyusb. USBConnector is the
    cleaner path on Linux when you can manage udev.
    """
    def __init__(
        self,
        vendor_id: int | str,
        product_id: int | str,
        *,
        timeout_ms: int = 10000,
        out_ep: int = 0x01,
    ):
        self.vendor_id = self._hex(vendor_id)
        self.product_id = self._hex(product_id)
        self.timeout_ms = timeout_ms
        self.out_ep = out_ep
        self._dev = None

    @staticmethod
    def _hex(value) -> int:
        if isinstance(value, int):
            return value
        s = str(value).strip().lower()
        return int(s, 16) if s.startswith("0x") else int(s, 16)

    def open(self) -> None:
        try:
            import usb.core  # type: ignore
            import usb.util  # type: ignore
        except ImportError as exc:
            raise PrinterConnectionError(
                "pyusb is not installed. Install with: pip install pyusb"
            ) from exc

        self._usb_util = usb.util
        dev = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
        if dev is None:
            raise PrinterConnectionError(
                f"USB printer {self.vendor_id:#06x}:{self.product_id:#06x} not found."
            )

        # Detach kernel driver if a backend holds it (Linux)
        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except (NotImplementedError, Exception):
            pass

        try:
            dev.set_configuration()
        except Exception as exc:
            logger.warning("Could not set USB configuration: %s", exc)

        self._dev = dev

    def write(self, data: bytes) -> None:
        if self._dev is None:
            raise PrinterConnectionError("USB device is not open.")
        try:
            self._dev.write(self.out_ep, data, self.timeout_ms)
        except Exception as exc:
            raise PrinterUnavailableError(f"USB write failed: {exc}") from exc

    def close(self) -> None:
        if self._dev is not None:
            try:
                self._usb_util.dispose_resources(self._dev)
            except Exception:
                pass
            self._dev = None


# ---------------------------------------------------------------------------
# Serial / RFCOMM (Bluetooth on shop PC + USB-to-serial adapters)
# ---------------------------------------------------------------------------
class SerialConnector(BaseConnector):
    """
    Uses pyserial — works for:
      * Bluetooth SPP / RFCOMM on Linux (after `sudo rfcomm bind /dev/rfcomm0 MAC 1`)
      * Bluetooth SPP on Windows (after pairing assigns a COM port, e.g. COM4)
      * USB printers exposing a virtual COM port
      * Classic USB-to-serial adapters (/dev/ttyUSB0)
    """
    def __init__(self, device: str, baudrate: int = 9600, *, timeout: float = 5.0):
        self.device = device
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    def open(self) -> None:
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise PrinterConnectionError(
                "pyserial is not installed. Install with: pip install pyserial"
            ) from exc
        try:
            self._serial = serial.Serial(
                self.device, self.baudrate, timeout=self.timeout,
            )
        except serial.SerialException as exc:
            raise PrinterConnectionError(
                f"Cannot open serial device {self.device}: {exc}"
            ) from exc

    def write(self, data: bytes) -> None:
        if not self._serial:
            raise PrinterConnectionError("Serial device is not open.")
        try:
            self._serial.write(data)
            self._serial.flush()
        except Exception as exc:
            raise PrinterUnavailableError(f"Serial write failed: {exc}") from exc

    def close(self) -> None:
        if self._serial:
            try:
                self._serial.close()
            finally:
                self._serial = None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def connector_for(printer) -> BaseConnector:
    """Build the correct connector based on the Printer row's configuration."""
    t = printer.printer_type

    if t == printer.Type.NETWORK:
        if not printer.ip_address:
            raise PrinterConnectionError(
                f"Printer '{printer.name}' has no ip_address configured."
            )
        return NetworkConnector(printer.ip_address, printer.port)

    if t == printer.Type.USB:
        if not printer.usb_vendor_id or not printer.usb_product_id:
            raise PrinterConnectionError(
                f"Printer '{printer.name}' missing USB vendor/product ID."
            )
        return USBConnector(printer.usb_vendor_id, printer.usb_product_id)

    if t == printer.Type.BLUETOOTH:
        # The MAC + channel are stored on the row, but the actual /dev/rfcomm*
        # or COM* path is provisioned at the OS layer. `identifier` holds that
        # path (e.g. /dev/rfcomm0 or COM4).
        device = printer.identifier
        if not device:
            raise PrinterConnectionError(
                f"Printer '{printer.name}' needs `identifier` set to the OS "
                f"serial path (e.g. /dev/rfcomm0 or COM4)."
            )
        return SerialConnector(device, 9600)

    raise PrinterConnectionError(f"Unsupported printer type: {t}")