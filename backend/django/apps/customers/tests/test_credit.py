from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.customers.models import Customer
from apps.customers.services import CustomerService
from apps.payments.models import CustomerLedgerEntry


User = get_user_model()


class CreditTests(APITestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0100", name="Reseller A",
            phone="0744444444", customer_type="RESELLER",
            credit_limit=Decimal("10000.00"),
        )

    def test_adjust_balance_creates_ledger(self):
        CustomerService.adjust_balance(
            self.customer.pk, Decimal("5000.00"), entry_type="INVOICE",
            reference_type="Sale", reference_id="SAL-000001",
        )
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("5000.00"))
        entry = CustomerLedgerEntry.objects.get(customer=self.customer)
        self.assertEqual(entry.entry_type, "INVOICE")
        self.assertEqual(entry.balance_after, Decimal("5000.00"))

    def test_payment_reduces_balance(self):
        CustomerService.adjust_balance(
            self.customer.pk, Decimal("5000.00"), "INVOICE",
        )
        CustomerService.adjust_balance(
            self.customer.pk, Decimal("-2000.00"), "PAYMENT",
        )
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("3000.00"))

    def test_credit_limit_exceeded(self):
        from core.exceptions.domain import CreditLimitExceededError
        CustomerService.adjust_balance(
            self.customer.pk, Decimal("9000.00"), "INVOICE",
        )
        self.customer.refresh_from_db()
        with self.assertRaises(CreditLimitExceededError):
            CustomerService.check_credit_limit(
                self.customer, Decimal("2000.00"),
            )

    def test_credit_limit_ok(self):
        CustomerService.adjust_balance(
            self.customer.pk, Decimal("5000.00"), "INVOICE",
        )
        self.customer.refresh_from_db()
        # Should not raise
        CustomerService.check_credit_limit(self.customer, Decimal("4000.00"))

    def test_assign_route_closes_previous(self):
        from apps.routes.models import Route

        r1 = Route.objects.create(name="Route A", code="RA")
        r2 = Route.objects.create(name="Route B", code="RB")

        a1 = CustomerService.assign_route(
            self.customer.pk, r1.pk, reason="Initial",
        )
        self.assertIsNone(a1.assigned_to)

        a2 = CustomerService.assign_route(
            self.customer.pk, r2.pk, reason="Reassigned to B",
        )
        a1.refresh_from_db()
        self.assertIsNotNone(a1.assigned_to)
        self.assertIsNone(a2.assigned_to)
        self.assertEqual(a2.route_id, r2.pk)