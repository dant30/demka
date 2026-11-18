from django.db import models

from apps.common.services.numbering import next_number


class SalesReturn(models.Model):
    class Status(models.TextChoices):
        DRAFT     = "DRAFT",     "Draft"
        APPROVED  = "APPROVED",  "Approved"
        REJECTED  = "REJECTED",  "Rejected"
        COMPLETED = "COMPLETED", "Completed"

    return_number = models.CharField(max_length=30, unique=True, blank=True)
    original_sale = models.ForeignKey("sales.Sale", on_delete=models.PROTECT, related_name="returns")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refund_method = models.ForeignKey(
        "payments.PaymentMethod", null=True, blank=True, on_delete=models.SET_NULL,
    )

    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["original_sale", "created_at"]),
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.return_number or 'NEW'} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = next_number("SALES_RETURN", prefix="RTN", width=6)
        super().save(*args, **kwargs)


class SalesReturnItem(models.Model):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey("sales.SaleItem", on_delete=models.PROTECT)
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    restock = models.BooleanField(default=True)
    location = models.ForeignKey(
        "inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL,
    )

    class Meta:
        indexes = [
            models.Index(fields=["sales_return"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"{self.product} x {self.quantity}"