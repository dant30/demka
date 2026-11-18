from django.db import migrations, models
from django.db.models import F
from django.utils import timezone


def backfill_created_at(apps, schema_editor):
    EtimsInvoice = apps.get_model("etims", "EtimsInvoice")
    EtimsInvoice.objects.filter(
        created_at__isnull=True,
        submitted_at__isnull=False,
    ).update(created_at=F("submitted_at"))
    EtimsInvoice.objects.filter(created_at__isnull=True).update(
        created_at=timezone.now(),
    )


class Migration(migrations.Migration):

    dependencies = [
        ("etims", "0003_rename_pin_to_tin"),
    ]

    operations = [
        migrations.AddField(
            model_name="etimsinvoice",
            name="created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_created_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="etimsinvoice",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]