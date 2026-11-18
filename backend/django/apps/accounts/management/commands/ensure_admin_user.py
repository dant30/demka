import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or ensure the configured DEMKA administrator account."

    def handle(self, *args, **options):
        email = os.getenv("ADMIN_EMAIL", "").strip().lower()
        phone = os.getenv("ADMIN_PHONE", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "")
        missing = [
            name for name, value in (
                ("ADMIN_EMAIL", email),
                ("ADMIN_PHONE", phone),
                ("ADMIN_PASSWORD", password),
            ) if not value
        ]
        if missing:
            raise CommandError(
                f"Admin bootstrap requires these environment variables: {', '.join(missing)}."
            )

        user_model = get_user_model()
        user = user_model.objects.filter(email__iexact=email).first()
        if user is None:
            user = user_model.objects.filter(username=email).first()

        created = user is None
        if created:
            user = user_model.objects.create_user(
                username=email,
                email=email,
                phone=phone,
                password=password,
                role="ADMIN",
            )
        elif user.phone != phone:
            raise CommandError(
                "The configured ADMIN_EMAIL belongs to an account with a different phone number."
            )
        elif not user.is_active:
            raise CommandError("The configured admin account is inactive; activate it before deployment.")

        changed_fields = []
        for field, value in (
            ("is_staff", True),
            ("is_superuser", True),
            ("role", "ADMIN"),
        ):
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        if changed_fields:
            user.save(update_fields=changed_fields)

        action = "Created" if created else "Ensured"
        self.stdout.write(self.style.SUCCESS(f"{action} admin account for {email}."))