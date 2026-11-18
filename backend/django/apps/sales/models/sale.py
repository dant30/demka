from django.db import models

from apps.common.services.numbering import next_number


class Sale(models.Model):
    class Channel(models.TextChoices):
        SHOP  = "SHOP",  "Shop"
        FIELD = "FIELD", "Field"

    class Status(models.TextChoices):
        DRAFT     = "DRAFT",     "Draft"
        CONFIRMED = "CONFIRMED", "Confirmed"
        INVOICED  = "INVOICED",  "Invoiced"
        PAID      = "PAID",      "Paid"
        PARTIAL   = "PARTIAL",   "Partial"
        CANCELLED = "CANCELLED", "Cancelled"
        RETURNED  = "RETURNED",  "Returned"

    class SaleType(models.TextChoices):
        STANDARD      = "STANDARD",      "Standard"
        SPECIAL_ORDER = "SPECIAL_ORDER", "Special Order"

    class EtimsStatus(models.TextChoices):
        NA      = "NA",      "N/A"
        PENDING = "PENDING", "Pending"
        SENT    = "SENT",    "Sent"
        FAILED  = "FAILED",  "Failed"

    sale_number = models.CharField(max_length=30, unique=True, blank=True)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    sale_type = models.CharField(
        max_length=20, choices=SaleType.choices, default=SaleType.STANDARD
    )
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="sales")
    location = models.ForeignKey("inventory.StockLocation", on_delete=models.PROTECT)
    route = models.ForeignKey("routes.Route", null=True, blank=True, on_delete=models.SET_NULL)
    agent = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="sales_made")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_credit_sale = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    etims_invoice_number = models.CharField(max_length=50, blank=True)
    etims_status = models.CharField(
        max_length=20, choices=EtimsStatus.choices, default=EtimsStatus.NA
    )

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        "accounts.User", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="sales_cancelled",
    )
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["channel", "created_at"]),
            models.Index(fields=["sale_number"]),
        ]

    def __str__(self):
        return f"{self.sale_number or 'NEW'} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.sale_number:
            prefix = "SL" if self.channel == self.Channel.SHOP else "FL"
            self.sale_number = next_number("SALE", prefix=prefix, width=6)
        super().save(*args, **kwargs)

    def cancel(self, *, user, reason: str):
        """Cancel a sale. Reason is required — audit trail must survive."""
        if not reason or not reason.strip():
            raise ValueError("A cancellation reason is required.")
        if self.status == self.Status.CANCELLED:
            return
        from django.utils import timezone

        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.cancelled_by = user
        self.cancellation_reason = reason.strip()
        self.save(update_fields=["status", "cancelled_at", "cancelled_by", "cancellation_reason"])


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)      # price snapshot
    unit_cost  = models.DecimalField(max_digits=12, decimal_places=2)      # COGS snapshot
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=16.0)
    tax_rate_ref = models.ForeignKey(
        "common.TaxRate", null=True, blank=True, on_delete=models.SET_NULL,
    )

    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    returned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=["product", "sale"]),
        ]

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    @property
    def returnable_quantity(self):
        return self.quantity - self.returned_quantity