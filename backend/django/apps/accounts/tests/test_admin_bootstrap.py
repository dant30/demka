import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.test import TestCase


User = get_user_model()


class EnsureAdminUserTests(TestCase):
    @patch.dict(os.environ, {
        "ADMIN_EMAIL": "admin@example.com",
        "ADMIN_PHONE": "0712345678",
        "ADMIN_PASSWORD": "SecurePass123!",
    })
    def test_creates_superuser_with_admin_role(self):
        call_command("ensure_admin_user", stdout=StringIO())

        user = User.objects.get(username="admin@example.com")
        self.assertEqual(user.email, "admin@example.com")
        self.assertEqual(user.phone, "0712345678")
        self.assertEqual(user.role, "ADMIN")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("SecurePass123!"))

    @patch.dict(os.environ, {
        "ADMIN_EMAIL": "admin@example.com",
        "ADMIN_PHONE": "0712345678",
        "ADMIN_PASSWORD": "AReplacementPass123!",
    })
    def test_is_idempotent_and_does_not_reset_existing_password(self):
        user = User.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            phone="0712345678",
            password="OriginalPass123!",
            role="BOSS",
        )

        call_command("ensure_admin_user", stdout=StringIO())

        user.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.role, "ADMIN")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("OriginalPass123!"))

    @patch.dict(os.environ, {}, clear=True)
    def test_requires_admin_environment(self):
        with self.assertRaisesMessage(CommandError, "ADMIN_EMAIL, ADMIN_PHONE, ADMIN_PASSWORD"):
            call_command("ensure_admin_user", stdout=StringIO())