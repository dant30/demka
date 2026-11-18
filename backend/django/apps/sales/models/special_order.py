from django.db import models


class SpecialOrder(models.Model):
    class Status(models.TextChoices):
        ORDERED   = "ORDERED",   "Ordered"
        ARRIVED   = "ARRIVED",   "Arrived"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    sale_item = models.OneToOneField("sales.SaleItem", on_delete=models.CASCADE, related_name="special_order")
    supplier = models.ForeignKey("suppliers.Supplier", null=True, blank=True, on_delete=models.SET_NULL)
    purchase_order_item = models.ForeignKey("purchasing.PurchaseOrderItem", null=True, blank=True, on_delete=models.SET_NULL)
    customer_deposit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_arrival_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORDERED)
    notes = models.TextField(blank=True)