from django.db import migrations, models
from django.utils import timezone


def backfill_printer_timestamps(apps, schema_editor):
    Printer = apps.get_model("printing", "Printer")
    now = timezone.now()
    Printer.objects.using(schema_editor.connection.alias).filter(
        created_at__isnull=True,
    ).update(created_at=now, updated_at=now)


class Migration(migrations.Migration):

    dependencies = [
        ("printing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="printer",
            name="created_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="printer",
            name="updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_printer_timestamps, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="printer",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="printer",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]