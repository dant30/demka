from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.customers.models import Customer
from apps.payments.models import CustomerLedgerEntry
from apps.payments.services import LedgerService


User = get_user_model()


class LedgerServiceTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
        )

    def test_post_invoice_positive(self):
        LedgerService.post_invoice(self.customer.pk, "1000", "Sale", "S1")
        e = CustomerLedgerEntry.objects.get(customer=self.customer)
        self.assertEqual(e.amount, Decimal("1000.00"))
        self.assertEqual(e.entry_type, "INVOICE")
        self.assertEqual(e.balance_after, Decimal("1000.00"))

    def test_post_payment_negative(self):
        LedgerService.post_invoice(self.customer.pk, "1000", "Sale", "S1")
        LedgerService.post_payment(self.customer.pk, "400", "Payment", "P1")
        e = CustomerLedgerEntry.objects.filter(entry_type="PAYMENT").first()
        self.assertEqual(e.amount, Decimal("-400.00"))
        self.assertEqual(e.balance_after, Decimal("600.00"))

    def test_post_credit_note(self):
        LedgerService.post_invoice(self.customer.pk, "1000", "Sale", "S1")
        LedgerService.post_credit_note(self.customer.pk, "250", "Return", "R1")
        e = CustomerLedgerEntry.objects.filter(entry_type="CREDIT_NOTE").first()
        self.assertEqual(e.amount, Decimal("-250.00"))

    def test_post_adjustment_signed(self):
        LedgerService.post_adjustment(self.customer.pk, "-100", "Correction", "C1")
        e = CustomerLedgerEntry.objects.get(customer=self.customer)
        self.assertEqual(e.amount, Decimal("-100.00"))

    def test_sum_equals_balance(self):
        LedgerService.post_invoice(self.customer.pk, "1000", "Sale", "S1")
        LedgerService.post_payment(self.customer.pk, "300", "Payment", "P1")
        LedgerService.post_adjustment(self.customer.pk, "-50", "Adj", "A1")
        self.customer.refresh_from_db()
        total = sum(
            e.amount for e in CustomerLedgerEntry.objects.filter(customer=self.customer)
        )
        self.assertEqual(total, self.customer.current_balance)