from django.db import models


class TaxRate(models.Model):
    name = models.CharField(max_length=50)
    rate = models.DecimalField(max_digits=5, decimal_places=2)   # 16.00
    etims_code = models.CharField(
        max_length=1, blank=True,
        choices=[("A", "Exempt (0%)"), ("B", "Standard (16%)"),
                 ("C", "Zero-rated (0%)"), ("D", "Non-VAT (0%)"),
                 ("E", "Reduced (8%)")],
        help_text="KRA eTIMS tax type code. Required for eTIMS submission.",
    )
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.rate}%)"