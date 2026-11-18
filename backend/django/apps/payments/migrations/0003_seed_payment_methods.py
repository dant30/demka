from django.db import migrations


SEEDS = [
    ("CASH", "Cash", False),
    ("MPESA", "M-Pesa", True),
    ("CREDIT", "Credit", False),
    ("CHEQUE", "Cheque", True),
    ("BANK_TRANSFER", "Bank Transfer", True),
]


def seed(apps, schema_editor):
    PaymentMethod = apps.get_model("payments", "PaymentMethod")
    for code, name, needs_ref in SEEDS:
        PaymentMethod.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "requires_reference": needs_ref,
                "is_active": True,
            },
        )


def unseed(apps, schema_editor):
    PaymentMethod = apps.get_model("payments", "PaymentMethod")
    PaymentMethod.objects.filter(code__in=[seed[0] for seed in SEEDS]).delete()


class Migration(migrations.Migration):
    dependencies = [("payments", "0002_initial")]

    operations = [migrations.RunPython(seed, unseed)]