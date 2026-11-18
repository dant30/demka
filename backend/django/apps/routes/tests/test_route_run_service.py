from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.expenses.models import Expense, ExpenseCategory
from apps.inventory.models import Category, Product, StockLocation
from apps.inventory.services import StockService
from apps.payments.models import Payment, PaymentMethod
from apps.routes.models import Route, RouteRun
from apps.routes.services import RouteRunService
from apps.sales.models import Sale
from apps.customers.models import Customer


class RouteRunServiceTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.agent = User.objects.create_user(
            username="agent", phone="0722222222",
            password="Secret123", role="FIELD_AGENT",
        )
        self.route = Route.objects.create(
            name="Route A", code="RA", default_agent=self.agent, is_active=True,
        )
        self.van = StockLocation.objects.create(
            name="Van 1", location_type="FIELD", assigned_agent=self.agent,
        )
        cat = Category.objects.create(name="Engine")
        self.product = Product.objects.create(
            sku="SKU1", name="Piston", category=cat,
            cost_price=100, retail_price=150, wholesale_price=130,
        )
        StockService.adjust(
            self.product, self.van, Decimal("10"),
            movement_type="PURCHASE", user=self.boss,
        )
        PaymentMethod.objects.update_or_create(
            code="CASH", defaults={"name": "Cash", "is_active": True},
        )

    def test_materialize_range_creates_scheduled_run_once(self):
        today = timezone.localdate()
        self.route.schedules.create(day_of_week=today.weekday())

        created = RouteRunService.materialize_range(today, today)
        repeated = RouteRunService.materialize_range(today, today)

        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].agent, self.agent)
        self.assertEqual(created[0].stock_location, self.van)
        self.assertEqual(repeated, [])

    def test_start_computes_opening_stock(self):
        run = RouteRunService.create(
            {
                "route": self.route.pk,
                "stock_location": self.van.pk,
                "run_date": timezone.now().date(),
            },
            self.boss,
        )
        self.assertEqual(run.status, "PLANNED")
        self.assertEqual(run.opening_stock_value, Decimal("0"))

        RouteRunService.start(run.pk, self.agent)
        run.refresh_from_db()
        self.assertEqual(run.status, "IN_PROGRESS")
        self.assertIsNotNone(run.started_at)
        self.assertEqual(run.opening_stock_value, Decimal("1000.00"))  # 10 × 100

    def test_complete_computes_reconciliation(self):
        run = RouteRunService.create(
            {
                "route": self.route.pk,
                "stock_location": self.van.pk,
                "run_date": timezone.now().date(),
            },
            self.boss,
        )
        RouteRunService.start(run.pk, self.agent)

        # Simulate one cash payment during the run
        customer = Customer.objects.create(
            code="CUST-0001", name="Walk", phone="0700000001",
            customer_type="WALK_IN",
        )
        Payment.objects.create(
            customer=customer,
            method=PaymentMethod.objects.get(code="CASH"),
            amount=Decimal("300.00"),
            received_by=self.agent,
            status="CONFIRMED",
        )
        # Cash expense during run
        fuel_cat = ExpenseCategory.objects.create(name="Fuel")
        Expense.objects.create(
            expense_number="EXP-001",
            category=fuel_cat, amount=Decimal("100.00"),
            expense_date=timezone.now().date(),
            paid_by=self.agent,
            payment_method=PaymentMethod.objects.get(code="CASH"),
            route_run=run,
        )

        completed = RouteRunService.complete(
            run.pk, self.agent, {"cash_handed_in": "200.00"},
        )
        self.assertEqual(completed.cash_collected, Decimal("300.00"))
        self.assertEqual(completed.cash_expected, Decimal("200.00"))
        self.assertEqual(completed.cash_handed_in, Decimal("200.00"))
        self.assertEqual(completed.cash_variance, Decimal("0.00"))

    def test_complete_with_shortage(self):
        run = RouteRunService.create(
            {
                "route": self.route.pk,
                "stock_location": self.van.pk,
                "run_date": timezone.now().date(),
            },
            self.boss,
        )
        RouteRunService.start(run.pk, self.agent)
        customer = Customer.objects.create(
            code="CUST-0001", name="Walk", phone="0700000001",
            customer_type="WALK_IN",
        )
        Payment.objects.create(
            customer=customer,
            method=PaymentMethod.objects.get(code="CASH"),
            amount=Decimal("500.00"),
            received_by=self.agent,
            status="CONFIRMED",
        )
        completed = RouteRunService.complete(
            run.pk, self.agent, {"cash_handed_in": "400.00"},
        )
        self.assertEqual(completed.cash_variance, Decimal("-100.00"))  # short

    def test_cancel_from_planned(self):
        run = RouteRunService.create(
            {
                "route": self.route.pk,
                "stock_location": self.van.pk,
                "run_date": timezone.now().date(),
            },
            self.boss,
        )
        cancelled = RouteRunService.cancel(run.pk, self.boss, "Weather")
        self.assertEqual(cancelled.status, "CANCELLED")

    def test_cannot_complete_unstarted(self):
        from core.exceptions.domain import ConflictError
        run = RouteRunService.create(
            {
                "route": self.route.pk,
                "stock_location": self.van.pk,
                "run_date": timezone.now().date(),
            },
            self.boss,
        )
        with self.assertRaises(ConflictError):
            RouteRunService.complete(run.pk, self.agent, {"cash_handed_in": "0"})