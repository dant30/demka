from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.reporting.services.dashboard_service import DashboardService


User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="boss", phone="0711111111", password="Secret123", role="BOSS",
        )

    def test_dashboard_structure(self):
        payload = DashboardService.build()
        self.assertIn("today", payload)
        self.assertIn("mtd", payload)
        self.assertIn("alerts", payload)
        self.assertIn("trends", payload)
        self.assertIn("position", payload)
        self.assertIn("sales_revenue", payload["today"])
        self.assertIn("cash_position", payload["today"])
        self.assertIn("last_7_days", payload["trends"])
        self.assertEqual(len(payload["trends"]["last_7_days"]), 7)
