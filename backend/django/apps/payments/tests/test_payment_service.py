from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.customers.models import Customer
from apps.payments.models import CustomerLedgerEntry, Payment, PaymentMethod
from apps.payments.services import LedgerService, PaymentService


User = get_user_model()


class PaymentServiceTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
            credit_limit=Decimal("20000.00"),
        )
        for code, name, req in [
            ("CASH", "Cash", False),
            ("MPESA", "M-Pesa", True),
            ("CHEQUE", "Cheque", True),
            ("BANK_TRANSFER", "Bank Transfer", True),
        ]:
            PaymentMethod.objects.update_or_create(
                code=code,
                defaults={"name": name, "requires_reference": req, "is_active": True},
            )

    def test_standalone_payment_reduces_balance(self):
        # Seed customer with 5000 debt
        LedgerService.post_invoice(self.customer.pk, "5000", "Seed", "S1")
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("5000.00"))

        payment = PaymentService.create_standalone(
            {"customer": self.customer.pk, "amount": "2000", "method": "CASH"},
            self.boss,
        )
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("3000.00"))
        self.assertEqual(payment.status, "CONFIRMED")
        self.assertTrue(payment.payment_number.startswith("PAY"))

        # Ledger entry created with signed amount
        entry = CustomerLedgerEntry.objects.filter(
            customer=self.customer, entry_type="PAYMENT",
        ).first()
        self.assertIsNotNone(entry)
        self.assertEqual(entry.amount, Decimal("-2000.00"))

    def test_standalone_payment_exceeding_balance_rejected(self):
        LedgerService.post_invoice(self.customer.pk, "500", "Seed", "S1")
        from core.exceptions.domain import ValidationError
        with self.assertRaises(ValidationError):
            PaymentService.create_standalone(
                {"customer": self.customer.pk, "amount": "1000", "method": "CASH"},
                self.boss,
            )

    def test_mpesa_requires_reference(self):
        from core.exceptions.domain import ValidationError
        LedgerService.post_invoice(self.customer.pk, "500", "Seed", "S1")
        with self.assertRaises(ValidationError):
            PaymentService.create_standalone(
                {"customer": self.customer.pk, "amount": "100", "method": "MPESA"},
                self.boss,
            )

    def test_mpesa_with_receipt_ok(self):
        LedgerService.post_invoice(self.customer.pk, "500", "Seed", "S1")
        payment = PaymentService.create_standalone(
            {
                "customer": self.customer.pk, "amount": "100",
                "method": "MPESA", "mpesa_receipt_number": "ABC123",
            },
            self.boss,
        )
        self.assertEqual(payment.reference, "ABC123")
        self.assertEqual(payment.status, "CONFIRMED")

    def test_reverse_restores_balance(self):
        LedgerService.post_invoice(self.customer.pk, "3000", "Seed", "S1")
        payment = PaymentService.create_standalone(
            {"customer": self.customer.pk, "amount": "1000", "method": "CASH"},
            self.boss,
        )
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("2000.00"))

        PaymentService.reverse(payment.pk, self.boss, reason="Bank mispost")
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("3000.00"))

        payment.refresh_from_db()
        self.assertEqual(payment.status, "REVERSED")

    def test_ledger_sum_equals_balance(self):
        """sum(amount) must equal current_balance — the reason we fixed the abs() bug."""
        LedgerService.post_invoice(self.customer.pk, "5000", "Seed", "S1")
        PaymentService.create_standalone(
            {"customer": self.customer.pk, "amount": "2000", "method": "CASH"}, self.boss,
        )
        LedgerService.post_credit_note(self.customer.pk, "500", "Seed", "R1")
        self.customer.refresh_from_db()

        total = sum(
            e.amount for e in CustomerLedgerEntry.objects.filter(customer=self.customer)
        )
        self.assertEqual(total, self.customer.current_balance)