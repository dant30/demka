from django.db import models


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Expense(models.Model):
    expense_number = models.CharField(max_length=30, unique=True)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    expense_date = models.DateField()
    paid_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    payment_method = models.ForeignKey("payments.PaymentMethod", on_delete=models.PROTECT)
    reference = models.CharField(max_length=100, blank=True)
    receipt_image = models.ImageField(upload_to="receipts/", null=True, blank=True)
    location = models.ForeignKey("inventory.StockLocation", null=True, blank=True, on_delete=models.SET_NULL)
    route_run = models.ForeignKey("routes.RouteRun", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.expense_number:
            from apps.common.services.numbering import next_number
            self.expense_number = next_number("EXPENSE", prefix="EXP-", width=6)
        super().save(*args, **kwargs)