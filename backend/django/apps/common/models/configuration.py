from django.db import models


class BusinessConfiguration(models.Model):
    business_name = models.CharField(max_length=200)
    kra_pin = models.CharField(max_length=20)
    vat_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="business/", null=True, blank=True)
    default_tax_rate = models.ForeignKey("TaxRate", null=True, blank=True, on_delete=models.SET_NULL)
    receipt_footer = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"business_name": "DEMKA", "kra_pin": ""})
        return obj