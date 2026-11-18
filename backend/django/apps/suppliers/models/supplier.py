from django.db import models


class Supplier(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    kra_pin = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    payment_terms_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE)
    supplier_part_number = models.CharField(max_length=100, blank=True)
    last_purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.PositiveIntegerField(default=0)