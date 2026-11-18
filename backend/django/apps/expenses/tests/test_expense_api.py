from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.expenses.models import Expense, ExpenseCategory
from apps.inventory.models import StockLocation
from apps.payments.models import PaymentMethod


User = get_user_model()


class ExpenseAPITests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )
        self.cat = ExpenseCategory.objects.create(name="Fuel")
        self.method = PaymentMethod.objects.update_or_create(
            code="CASH", defaults={"name": "Cash", "requires_reference": False, "is_active": True},
        )[0]
        self.location = StockLocation.objects.create(name="Shop", location_type="SHOP")

        self.client = APIClient()

    def _payload(self):
        return {
            "category": self.cat.pk,
            "amount": "500.00",
            "description": "Fuel",
            "expense_date": timezone.now().date().isoformat(),
            "payment_method": self.method.pk,
            "location": self.location.pk,
        }

    def test_helper_can_create(self):
        self.client.force_authenticate(self.helper)
        res = self.client.post("/api/expenses/", self._payload(), format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["expense_number"].startswith("EXP-"))

    def test_helper_sees_only_own_expenses(self):
        Expense.objects.create(
            expense_number="EXP-X1", category=self.cat, amount=100,
            expense_date=timezone.now().date(), paid_by=self.boss,
            payment_method=self.method, location=self.location,
        )
        self.client.force_authenticate(self.helper)
        res = self.client.get("/api/expenses/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 0)

    def test_boss_sees_all_expenses(self):
        Expense.objects.create(
            expense_number="EXP-X1", category=self.cat, amount=100,
            expense_date=timezone.now().date(), paid_by=self.boss,
            payment_method=self.method, location=self.location,
        )
        Expense.objects.create(
            expense_number="EXP-X2", category=self.cat, amount=200,
            expense_date=timezone.now().date(), paid_by=self.helper,
            payment_method=self.method, location=self.location,
        )
        self.client.force_authenticate(self.boss)
        res = self.client.get("/api/expenses/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["results"]), 2)

    def test_helper_cannot_delete(self):
        exp = Expense.objects.create(
            expense_number="EXP-X1", category=self.cat, amount=100,
            expense_date=timezone.now().date(), paid_by=self.helper,
            payment_method=self.method, location=self.location,
        )
        self.client.force_authenticate(self.helper)
        res = self.client.delete(f"/api/expenses/{exp.pk}/")
        self.assertEqual(res.status_code, 403)

    def test_boss_can_delete(self):
        exp = Expense.objects.create(
            expense_number="EXP-X1", category=self.cat, amount=100,
            expense_date=timezone.now().date(), paid_by=self.helper,
            payment_method=self.method, location=self.location,
        )
        self.client.force_authenticate(self.boss)
        res = self.client.delete(f"/api/expenses/{exp.pk}/")
        self.assertEqual(res.status_code, 204)

    def test_summary_endpoint(self):
        Expense.objects.create(
            expense_number="EXP-X1", category=self.cat, amount=300,
            expense_date=timezone.now().date(), paid_by=self.boss,
            payment_method=self.method, location=self.location,
        )
        self.client.force_authenticate(self.boss)
        res = self.client.get("/api/expenses/summary/?period=daily")
        self.assertEqual(res.status_code, 200)
        self.assertIn("total", res.data)
        self.assertIn("by_category", res.data)

    def test_monthly_trend(self):
        self.client.force_authenticate(self.boss)
        res = self.client.get("/api/expenses/monthly-trend/?months=3")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 3)

    def test_helper_cannot_manage_categories(self):
        self.client.force_authenticate(self.helper)
        res = self.client.post(
            "/api/expenses/categories/", {"name": "New Cat"}, format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_boss_can_manage_categories(self):
        self.client.force_authenticate(self.boss)
        res = self.client.post(
            "/api/expenses/categories/", {"name": "New Cat"}, format="json",
        )
        self.assertEqual(res.status_code, 201)