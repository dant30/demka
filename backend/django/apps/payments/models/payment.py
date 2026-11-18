from django.db import models

from apps.common.services.numbering import next_number


class PaymentMethod(models.Model):
    class Code(models.TextChoices):
        CASH          = "CASH",          "Cash"
        MPESA         = "MPESA",         "M-Pesa"
        CREDIT        = "CREDIT",        "Credit"
        CHEQUE        = "CHEQUE",        "Cheque"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"

    code = models.CharField(max_length=30, choices=Code.choices, unique=True)
    name = models.CharField(max_length=50)
    requires_reference = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REVERSED  = "REVERSED",  "Reversed"

    payment_number = models.CharField(max_length=30, unique=True, blank=True)
    sale = models.ForeignKey(
        "sales.Sale", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="payments",
    )
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="payments")
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)

    received_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    received_at = models.DateTimeField(auto_now_add=True)
    location = models.ForeignKey(
        "inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)

    mpesa_phone = models.CharField(max_length=20, blank=True)
    mpesa_transaction_id = models.CharField(max_length=50, blank=True)
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "received_at"]),
            models.Index(fields=["method", "received_at"]),
            models.Index(fields=["sale"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.payment_number or 'NEW'} - {self.amount}"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = next_number("PAYMENT", prefix="PAY", width=6)
        super().save(*args, **kwargs)


class MpesaTransaction(models.Model):
    transaction_id = models.CharField(max_length=50, unique=True)
    mpesa_receipt = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    account_reference = models.CharField(max_length=100, blank=True)
    transaction_date = models.DateTimeField()
    raw_payload = models.JSONField(default=dict)
    matched_payment = models.ForeignKey(
        Payment, null=True, blank=True, on_delete=models.SET_NULL,
    )
    reconciled = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["mpesa_receipt"]),
            models.Index(fields=["reconciled", "transaction_date"]),
        ]

    def __str__(self):
        return f"{self.mpesa_receipt or self.transaction_id}"


class CustomerLedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        INVOICE         = "INVOICE",         "Invoice"
        PAYMENT         = "PAYMENT",         "Payment"
        CREDIT_NOTE     = "CREDIT_NOTE",     "Credit Note"
        OPENING_BALANCE = "OPENING_BALANCE", "Opening Balance"
        ADJUSTMENT      = "ADJUSTMENT",      "Adjustment"

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.CASCADE, related_name="ledger_entries",
    )
    entry_type = models.CharField(max_length=30, choices=EntryType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)      # signed (+ credit sale, - payment)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["entry_type"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer} {self.entry_type} {self.amount}"