from django.db import models


class StockLocation(models.Model):
    class Type(models.TextChoices):
        SHOP      = "SHOP",      "Shop"
        FIELD     = "FIELD",     "Field"
        WAREHOUSE = "WAREHOUSE", "Warehouse"

    name = models.CharField(max_length=100)
    location_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.SHOP
    )
    assigned_agent = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_locations",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StockLevel(models.Model):
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.CASCADE, related_name="levels"
    )
    location = models.ForeignKey(
        StockLocation, on_delete=models.CASCADE, related_name="levels"
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.PositiveIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("product", "location")
        indexes = [models.Index(fields=["product", "location"])]

    def effective_reorder_level(self) -> int:
        return self.reorder_level if self.reorder_level is not None else self.product.reorder_level

    def __str__(self):
        return f"{self.product.sku} @ {self.location.name}: {self.quantity}"


class StockMovement(models.Model):
    class Type(models.TextChoices):
        SALE              = "SALE",              "Sale"
        PURCHASE          = "PURCHASE",          "Purchase"
        TRANSFER_IN       = "TRANSFER_IN",       "Transfer In"
        TRANSFER_OUT      = "TRANSFER_OUT",      "Transfer Out"
        ADJUSTMENT        = "ADJUSTMENT",        "Adjustment"
        RETURN            = "RETURN",            "Return"
        SPECIAL_ORDER_OUT = "SPECIAL_ORDER_OUT", "Special Order Out"

    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE)
    location = models.ForeignKey(StockLocation, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=Type.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "location", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["movement_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} {self.product.sku}"


class StockTransfer(models.Model):
    class Status(models.TextChoices):
        PENDING    = "PENDING",    "Pending"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        RECEIVED   = "RECEIVED",   "Received"
        CANCELLED  = "CANCELLED",  "Cancelled"

    from_location = models.ForeignKey(
        StockLocation, on_delete=models.CASCADE, related_name="transfers_out"
    )
    to_location = models.ForeignKey(
        StockLocation, on_delete=models.CASCADE, related_name="transfers_in"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    initiated_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT,
        related_name="transfers_initiated",
    )
    received_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="transfers_received",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transfer {self.pk} ({self.status})"


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(
        StockTransfer, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey("inventory.Product", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.sku}"