from django.db import models


class PreorderCustomerSession(models.Model):
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE,
        related_name="preorder_sessions",
    )
    # Hashed OTP — never store the plaintext.
    otp_code = models.CharField(max_length=128)
    otp_expires_at = models.DateTimeField()
    session_token = models.CharField(max_length=100, unique=True)

    is_active = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "is_active"]),
            models.Index(fields=["session_token"]),
            models.Index(fields=["otp_expires_at"]),
        ]

    def __str__(self):
        return f"Session {self.customer_id} ({'active' if self.is_active else 'pending'})"


class Preorder(models.Model):
    class Status(models.TextChoices):
        SUBMITTED      = "SUBMITTED",      "Submitted"
        CONFIRMED      = "CONFIRMED",      "Confirmed"
        IN_PREPARATION = "IN_PREPARATION", "In Preparation"
        READY          = "READY",          "Ready"
        DELIVERED      = "DELIVERED",      "Delivered"
        CANCELLED      = "CANCELLED",      "Cancelled"

    preorder_number = models.CharField(max_length=30, unique=True, blank=True)
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT,
        related_name="preorders",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SUBMITTED,
    )
    total_estimated = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    preferred_pickup_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    staff_notes = models.TextField(blank=True)

    converted_sale = models.ForeignKey(
        "sales.Sale", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="source_preorder",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        "accounts.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="preorders_cancelled",
    )
    cancel_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["customer", "created_at"]),
        ]

    def __str__(self):
        return f"{self.preorder_number or 'NEW'} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.preorder_number:
            from apps.common.services.numbering import next_number
            self.preorder_number = next_number("PREORDER", prefix="PR-", width=6)
        super().save(*args, **kwargs)


class PreorderItem(models.Model):
    preorder = models.ForeignKey(
        Preorder, on_delete=models.CASCADE, related_name="items",
    )
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price_estimated = models.DecimalField(max_digits=12, decimal_places=2)
    # Staff may override at confirm time; if set, this wins at delivery.
    final_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    available_in_stock = models.BooleanField(default=False)
    available_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Snapshot of stock at submission time, for audit.",
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    @property
    def effective_unit_price(self):
        return self.final_price if self.final_price is not None else self.unit_price_estimated

    @property
    def line_total(self):
        from decimal import Decimal
        return (Decimal(self.quantity) * Decimal(self.effective_unit_price)).quantize(Decimal("0.01"))