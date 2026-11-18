from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.expenses.models import Expense, ExpenseCategory
from apps.expenses.services import ExpenseService
from apps.inventory.models import StockLocation
from apps.payments.models import PaymentMethod
from apps.routes.models import Route, RouteRun


User = get_user_model()


class ExpenseServiceTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.helper = User.objects.create_user(
            username="helper", phone="0722222222",
            password="Secret123", role="SALES_HELPER",
        )
        self.agent = User.objects.create_user(
            username="agent", phone="0733333333",
            password="Secret123", role="FIELD_AGENT",
        )
        self.cat = ExpenseCategory.objects.create(name="Fuel")
        self.method = PaymentMethod.objects.update_or_create(
            code="CASH", defaults={"name": "Cash", "requires_reference": False, "is_active": True},
        )[0]
        self.location = StockLocation.objects.create(name="Shop", location_type="SHOP")

        route = Route.objects.create(name="Route A", code="RA")
        self.run = RouteRun.objects.create(
            route=route, agent=self.agent, stock_location=self.location,
            run_date=timezone.now().date(), status="IN_PROGRESS",
        )

    def _payload(self, **overrides):
        base = {
            "category": self.cat.pk,
            "amount": "1500.00",
            "description": "Diesel for van",
            "expense_date": timezone.now().date(),
            "payment_method": self.method.pk,
            "location": self.location.pk,
        }
        base.update(overrides)
        return base

    def test_create_auto_numbers(self):
        exp = ExpenseService.create(self._payload(), self.boss)
        self.assertTrue(exp.expense_number.startswith("EXP-"))
        self.assertEqual(exp.amount, Decimal("1500.00"))

    def test_future_date_rejected(self):
        from core.exceptions.domain import ValidationError
        with self.assertRaises(ValidationError):
            ExpenseService.create(
                self._payload(expense_date=timezone.now().date() + timedelta(days=1)),
                self.boss,
            )

    def test_zero_amount_rejected(self):
        from core.exceptions.domain import ValidationError
        with self.assertRaises(ValidationError):
            ExpenseService.create(self._payload(amount="0"), self.boss)

    def test_agent_can_attach_to_own_run(self):
        exp = ExpenseService.create(
            self._payload(route_run=self.run.pk), self.agent,
        )
        self.assertEqual(exp.route_run_id, self.run.pk)

    def test_agent_cannot_attach_to_others_run(self):
        from core.exceptions.domain import ValidationError
        other_agent = User.objects.create_user(
            username="other", phone="0744444444",
            password="Secret123", role="FIELD_AGENT",
        )
        with self.assertRaises(ValidationError):
            ExpenseService.create(
                self._payload(route_run=self.run.pk), other_agent,
            )

    def test_summary_by_category(self):
        ExpenseService.create(self._payload(amount="1000"), self.boss)
        ExpenseService.create(self._payload(amount="500"), self.boss)
        rows = ExpenseService.by_category(
            timezone.now().date(), timezone.now().date(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["total"], "1500.00")
        self.assertEqual(rows[0]["count"], 2)

    def test_missing_receipt_task_includes_null_images(self):
        expense = ExpenseService.create(self._payload(), self.boss)
        from apps.expenses.tasks import flag_expenses_missing_receipts

        result = flag_expenses_missing_receipts()

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["expenses"][0]["id"], expense.pk)

    def test_by_route_run(self):
        ExpenseService.create(self._payload(amount="800", route_run=self.run.pk), self.agent)
        ExpenseService.create(self._payload(amount="400", route_run=self.run.pk), self.agent)
        result = ExpenseService.by_route_run(self.run.pk)
        self.assertEqual(result["total_expenses"], "1200.00")
        self.assertEqual(len(result["by_category"]), 1)
        self.assertEqual(result["by_category"][0]["category"], "Fuel")

    def test_update_changes_amount(self):
        exp = ExpenseService.create(self._payload(), self.boss)
        updated = ExpenseService.update(exp.pk, {"amount": "2000"}, self.boss)
        self.assertEqual(updated.amount, Decimal("2000.00"))

    def test_delete(self):
        exp = ExpenseService.create(self._payload(), self.boss)
        ExpenseService.delete(exp.pk, self.boss)
        self.assertFalse(Expense.objects.filter(pk=exp.pk).exists())