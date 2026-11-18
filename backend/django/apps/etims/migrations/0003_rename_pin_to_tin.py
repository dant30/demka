from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("etims", "0002_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="etimsconfig",
            old_name="pin",
            new_name="tin",
        ),
    ]