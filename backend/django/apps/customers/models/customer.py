from django.db import models


class Customer(models.Model):
    class Type(models.TextChoices):
        RETAIL   = "RETAIL",   "Retail"
        RESELLER = "RESELLER", "Reseller"
        WALK_IN  = "WALK_IN",  "Walk-in"

    code = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    customer_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.RETAIL
    )
    business_name = models.CharField(max_length=200, blank=True)
    kra_pin = models.CharField(max_length=20, blank=True)
    physical_address = models.TextField(blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_terms_days = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["customer_type", "is_active"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            from apps.common.services.numbering import next_number
            self.code = next_number("CUSTOMER", prefix="CUST", width=4)
        super().save(*args, **kwargs)


class CustomerRouteAssignment(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="route_assignments"
    )
    route = models.ForeignKey("routes.Route", on_delete=models.CASCADE)
    assigned_from = models.DateField()
    assigned_to = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-assigned_from"]
        indexes = [models.Index(fields=["customer", "assigned_to"])]

    def __str__(self):
        return f"{self.customer.code} -> {self.route.code}"


class CustomerContact(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="contacts"
    )
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} ({self.customer.code})"