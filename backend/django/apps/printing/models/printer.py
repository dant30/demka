from django.db import models


class Printer(models.Model):
    class Type(models.TextChoices):
        USB = "USB", "USB (direct)"
        NETWORK = "NETWORK", "Network / WiFi (TCP 9100)"
        BLUETOOTH = "BLUETOOTH", "Bluetooth (RFCOMM / SPP)"

    class PaperWidth(models.IntegerChoices):
        MM58 = 58, "58 mm"
        MM80 = 80, "80 mm"

    name = models.CharField(max_length=100)
    printer_type = models.CharField(max_length=20, choices=Type.choices)
    identifier = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="Printer IP for WiFi / network printers (port 9100).",
    )
    port = models.PositiveIntegerField(
        default=9100,
        help_text="Raw TCP port. 9100 is the ESC/POS standard.",
    )
    usb_vendor_id = models.CharField(
        max_length=10, blank=True,
        help_text="Hex vendor ID, e.g. 0x04b8. Find with `lsusb` (Linux) or "
                  "Device Manager (Windows).",
    )
    usb_product_id = models.CharField(
        max_length=10, blank=True,
        help_text="Hex product ID, e.g. 0x0202.",
    )
    bt_mac_address = models.CharField(
        max_length=30, blank=True,
        help_text="Bluetooth MAC, e.g. 00:11:22:33:44:55.",
    )
    bt_rfcomm_channel = models.PositiveSmallIntegerField(
        default=1,
        help_text="RFCOMM channel. Usually 1 for ESC/POS receipt printers.",
    )
    assigned_location = models.ForeignKey(
        "inventory.StockLocation", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="printers",
    )
    assigned_user = models.ForeignKey(
        "accounts.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="printers",
    )
    paper_width_mm = models.PositiveIntegerField(
        choices=PaperWidth.choices, default=PaperWidth.MM58,
    )
    supports_cash_drawer = models.BooleanField(default=False)
    is_default = models.BooleanField(
        default=False,
        help_text="Fallback printer when a job has no explicit target.",
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["printer_type", "is_active"]),
            models.Index(fields=["assigned_location", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_printer_type_display()})"

    def transport_summary(self) -> str:
        if self.printer_type == self.Type.NETWORK:
            return f"{self.ip_address or '?'}:{self.port}"
        if self.printer_type == self.Type.USB:
            return f"{self.usb_vendor_id or '?'}/{self.usb_product_id or '?'}"
        if self.printer_type == self.Type.BLUETOOTH:
            return f"{self.bt_mac_address or '?'} ch{self.bt_rfcomm_channel}"
        return self.identifier or "-"


class PrintJob(models.Model):
    class Status(models.TextChoices):
        QUEUED  = "QUEUED",  "Queued"
        PRINTING = "PRINTING", "Printing"
        PRINTED = "PRINTED", "Printed"
        FAILED  = "FAILED",  "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    class DocumentType(models.TextChoices):
        RECEIPT = "RECEIPT", "Sale Receipt"
        INVOICE = "INVOICE", "Invoice"
        CREDIT_NOTE = "CREDIT_NOTE", "Credit Note"
        DELIVERY_NOTE = "DELIVERY_NOTE", "Delivery Note"
        PREORDER_SLIP = "PREORDER_SLIP", "Preorder Slip"
        ROUTE_SHEET = "ROUTE_SHEET", "Route Sheet"
        EXPENSE_SLIP = "EXPENSE_SLIP", "Expense Slip"
        TEST = "TEST", "Test Print"

    printer = models.ForeignKey(
        Printer, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="jobs",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    payload = models.JSONField(
        default=dict,
        help_text="Structured receipt data — the same dict the renderer consumed.",
    )
    escpos_data = models.BinaryField(
        null=True, blank=True,
        help_text="Rendered ESC/POS bytes. Identical for USB / WiFi / Bluetooth.",
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="print_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    printed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["printer", "status"]),
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["document_type", "created_at"]),
        ]

    def __str__(self):
        return f"Job #{self.pk} - {self.document_type} ({self.status})"

    @property
    def escpos_base64(self) -> str:
        """Base64-encoded ESC/POS payload used by the frontend printer client."""
        if not self.escpos_data:
            return ""
        import base64
        return base64.b64encode(bytes(self.escpos_data)).decode()