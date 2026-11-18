from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


User = get_user_model()


class UserViewSetTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )

    def test_helper_cannot_list_users(self):
        self.client.force_authenticate(self.helper)
        res = self.client.get("/api/accounts/users/")
        self.assertEqual(res.status_code, 403)

    def test_boss_can_list_users(self):
        self.client.force_authenticate(self.boss)
        res = self.client.get("/api/accounts/users/")
        self.assertEqual(res.status_code, 200)

    def test_boss_can_create_user(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/accounts/users/",
            {
                "username": "newhelper",
                "phone": "0733333333",
                "role": "SALES_HELPER",
                "password": "Secret123",
                "confirm_password": "Secret123",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.filter(username="newhelper").exists())

    def test_phone_validation_rejects_bad_format(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/accounts/users/",
            {
                "username": "newhelper2",
                "phone": "12345",
                "role": "SALES_HELPER",
                "password": "Secret123",
                "confirm_password": "Secret123",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("phone", res.data["error"]["message"])