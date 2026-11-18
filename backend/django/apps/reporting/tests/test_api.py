from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


User = get_user_model()


@override_settings(CACHES={
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "reporting-api-tests",
    },
})
class ReportingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111", password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222", password="Secret123", role="SALES_HELPER",
        )

    def test_reports_are_boss_only(self):
        self.client.force_authenticate(self.helper)
        response = self.client.get("/api/reporting/dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_boss_can_view_dashboard(self):
        self.client.force_authenticate(self.boss)
        response = self.client.get("/api/reporting/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("today", response.data)

    def test_invalid_period_returns_400(self):
        self.client.force_authenticate(self.boss)
        response = self.client.get("/api/reporting/profit-loss/?period=bad")
        self.assertEqual(response.status_code, 400)
