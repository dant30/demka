from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


User = get_user_model()


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="boss1",
            phone="0712345678",
            password="Secret123",
            role="BOSS",
        )

    def test_login_with_username(self):
        res = self.client.post(
            reverse("auth-login"),
            {"identifier": "boss1", "password": "Secret123"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.data["user"]["role"], "BOSS")

    def test_login_with_phone(self):
        res = self.client.post(
            reverse("auth-login"),
            {"identifier": "0712345678", "password": "Secret123"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)

    def test_login_wrong_password(self):
        res = self.client.post(
            reverse("auth-login"),
            {"identifier": "boss1", "password": "wrong"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_me_requires_auth(self):
        res = self.client.get(reverse("auth-me"))
        self.assertEqual(res.status_code, 401)

    def test_me_returns_profile_when_authenticated(self):
        self.client.force_authenticate(self.user)
        res = self.client.get(reverse("auth-me"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["username"], "boss1")

    def test_change_password(self):
        self.client.force_authenticate(self.user)
        res = self.client.post(
            reverse("auth-change-password"),
            {
                "current_password": "Secret123",
                "new_password": "NewSecret456",
                "confirm_password": "NewSecret456",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecret456"))