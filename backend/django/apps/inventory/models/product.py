from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="children",
    )
    applies_to = models.CharField(
        max_length=20,
        choices=[("MOTORBIKE", "Motorbike"), ("AUTO", "Auto"), ("BOTH", "Both")],
        default="BOTH",
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = "PIECE", "Piece"
        SET   = "SET",   "Set"
        PAIR  = "PAIR",  "Pair"
        LITRE = "LITRE", "Litre"

    sku = models.CharField(max_length=50, unique=True)
    part_number = models.CharField(max_length=100, blank=True)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    product_type = models.CharField(
        max_length=20,
        choices=[
            ("MOTORBIKE_PART", "Motorbike Part"),
            ("AUTO_PART",      "Auto Part"),
            ("ACCESSORY",      "Accessory"),
        ],
        default="AUTO_PART",
    )
    brand = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_stocked = models.BooleanField(default=True)
    reorder_level = models.PositiveIntegerField(default=0)
    reorder_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    compatibility_notes = models.TextField(blank=True)
    etims_item_cls_cd = models.CharField(
        max_length=20, blank=True,
        help_text="KRA UNSPSC-derived 10-digit classification code "
                  "(from /selectItemClsList). Required before the item can be sold.",
    )
    etims_item_type = models.CharField(
        max_length=1, blank=True, default="2",
        choices=[("1", "Raw Material"), ("2", "Finished Product"), ("3", "Service")],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["product_type", "is_active"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["sku"]),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"