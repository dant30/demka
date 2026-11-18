from django.db import models

from apps.common.fields import EncryptedTextField


class EtimsConfig(models.Model):
    """Singleton — one active device per business."""

    class Environment(models.TextChoices):
        SANDBOX = "sandbox", "Sandbox"
        PRODUCTION = "production", "Production"

    environment = models.CharField(
        max_length=20, choices=Environment.choices, default=Environment.SANDBOX,
    )
    tin = models.CharField(
        max_length=20, help_text="Taxpayer KRA PIN (e.g. P051234567A).",
    )
    bhf_id = models.CharField(
        max_length=10, default="00",
        help_text="Branch ID. 00 = head office.",
    )
    device_serial = models.CharField(
        max_length=100,
        help_text="dvcSrlNo sent at /selectInitOsdcInfo. MUST be stable across redeploys.",
    )
    cmc_key = EncryptedTextField(
        blank=True,
        help_text="Communication key returned by /selectInitOsdcInfo. Long-lived credential.",
    )
    sdc_id = models.CharField(max_length=100, blank=True)
    mrc_no = models.CharField(max_length=100, blank=True)
    trade_name = models.CharField(max_length=200, blank=True)
    branch_name = models.CharField(max_length=200, blank=True)

    # Legacy OAuth fields remain available but are unused by OSCU.
    client_id = models.CharField(max_length=200, blank=True)
    client_secret = EncryptedTextField(blank=True)

    initialized_at = models.DateTimeField(null=True, blank=True)
    last_code_sync_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "eTIMS Configuration"
        verbose_name_plural = "eTIMS Configuration"

    def __str__(self):
        return f"eTIMS [{self.environment}] {self.tin}/{self.bhf_id}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"tin": "", "device_serial": ""})
        return obj

    @property
    def base_url(self) -> str:
        return (
            "https://etims-api.kra.go.ke/etims-api"
            if self.environment == self.Environment.PRODUCTION
            else "https://etims-api-sbx.kra.go.ke/etims-api"
        )


class EtimsSequence(models.Model):
    """Gap-free per-branch invoice number allocator."""

    tin = models.CharField(max_length=20)
    bhf_id = models.CharField(max_length=10)
    next_no = models.PositiveBigIntegerField(default=1)

    class Meta:
        unique_together = ("tin", "bhf_id")
        verbose_name = "eTIMS Sequence"

    def __str__(self):
        return f"{self.tin}/{self.bhf_id} -> {self.next_no}"


class EtimsItem(models.Model):
    """Registration state for a product against KRA."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REGISTERED = "REGISTERED", "Registered"
        FAILED = "FAILED", "Failed"

    product = models.OneToOneField(
        "inventory.Product", on_delete=models.CASCADE, related_name="etims_item",
    )
    item_cd = models.CharField(max_length=100)
    item_cls_cd = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    response_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "eTIMS Item"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.item_cd} ({self.status})"


class EtimsInvoice(models.Model):
    """Invoice transmission attempt and outbox record."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        QUEUED = "QUEUED", "Queued"
        SUBMITTED = "SUBMITTED", "Submitted"
        FAILED = "FAILED", "Failed"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    class ReceiptType(models.TextChoices):
        SALE = "S", "Sale"
        CREDIT_NOTE = "R", "Credit Note"

    sale = models.ForeignKey(
        "sales.Sale", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="etims_invoices",
    )
    sales_return = models.ForeignKey(
        "sales.SalesReturn", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="etims_invoices",
    )

    receipt_type = models.CharField(
        max_length=1, choices=ReceiptType.choices, default=ReceiptType.SALE,
    )
    invoice_number = models.CharField(max_length=50, blank=True)
    invc_no = models.PositiveBigIntegerField(null=True, blank=True)
    org_invc_no = models.PositiveBigIntegerField(null=True, blank=True)

    cu_invc_no = models.CharField(
        max_length=100, blank=True,
        help_text="Composite of curRcptNo/totRcptNo returned by KRA.",
    )
    cur_rcpt_no = models.PositiveBigIntegerField(null=True, blank=True)
    tot_rcpt_no = models.PositiveBigIntegerField(null=True, blank=True)
    control_code = models.CharField(max_length=100, blank=True)
    receipt_signature = models.CharField(max_length=100, blank=True)
    sdc_date_time = models.CharField(max_length=20, blank=True)
    qr_code_data = models.TextField(blank=True)

    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["receipt_type", "created_at"]),
            models.Index(fields=["sale"]),
            models.Index(fields=["sales_return"]),
            models.Index(fields=["invc_no"]),
        ]

    def __str__(self):
        return f"eTIMS#{self.invc_no or '-'} {self.receipt_type} ({self.status})"