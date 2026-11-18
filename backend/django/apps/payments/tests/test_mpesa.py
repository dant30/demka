from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.customers.models import Customer
from apps.payments.models import MpesaTransaction, Payment, PaymentMethod
from apps.payments.services import LedgerService, MpesaReconciliationService


User = get_user_model()


class MpesaTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user(
            username="boss", phone="0711111111",
            password="Secret123", role="BOSS",
        )
        self.customer = Customer.objects.create(
            code="CUST-0001", name="Acme",
            phone="0744444444", customer_type="RESELLER",
        )
        PaymentMethod.objects.update_or_create(
            code="MPESA",
            defaults={"name": "M-Pesa", "requires_reference": True, "is_active": True},
        )

    def _make_tx(self, checkout_id, receipt="REC001", amount="100"):
        return MpesaTransaction.objects.create(
            transaction_id=checkout_id,
            mpesa_receipt=receipt,
            phone="0744444444",
            amount=Decimal(amount),
            transaction_date="2026-01-01T10:00:00Z",
            raw_payload={"test": True},
        )

    def test_auto_match_confirms_pending_payment(self):
        payment = Payment.objects.create(
            customer=self.customer,
            method=PaymentMethod.objects.get(code="MPESA"),
            amount=Decimal("100.00"),
            received_by=self.boss,
            mpesa_transaction_id="CHK123",
            status=Payment.Status.PENDING,
        )
        self._make_tx("CHK123", receipt="REC001", amount="100")

        result = MpesaReconciliationService.auto_match("CHK123")
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "CONFIRMED")
        self.assertEqual(result.mpesa_receipt_number, "REC001")

        tx = MpesaTransaction.objects.get(transaction_id="CHK123")
        self.assertTrue(tx.reconciled)
        self.assertEqual(tx.matched_payment_id, payment.pk)

    def test_auto_match_no_payment_returns_none(self):
        self._make_tx("CHK-NOBODY", receipt="REC-X")
        result = MpesaReconciliationService.auto_match("CHK-NOBODY")
        self.assertIsNone(result)

    def test_auto_match_idempotent(self):
        payment = Payment.objects.create(
            customer=self.customer,
            method=PaymentMethod.objects.get(code="MPESA"),
            amount=Decimal("100.00"),
            received_by=self.boss,
            mpesa_transaction_id="CHK456",
            status=Payment.Status.PENDING,
        )
        self._make_tx("CHK456")
        MpesaReconciliationService.auto_match("CHK456")
        # Second call should not duplicate
        MpesaReconciliationService.auto_match("CHK456")
        self.assertEqual(
            MpesaTransaction.objects.filter(transaction_id="CHK456").count(), 1,
        )

    def test_manual_match(self):
        LedgerService.post_invoice(self.customer.pk, "100", "Seed", "S1")
        payment = Payment.objects.create(
            customer=self.customer,
            method=PaymentMethod.objects.get(code="MPESA"),
            amount=Decimal("100.00"),
            received_by=self.boss,
            status=Payment.Status.PENDING,
        )
        tx = self._make_tx("CHK-MANUAL", receipt="MAN001")

        result = MpesaReconciliationService.manual_match(tx.pk, payment.pk, self.boss)
        self.assertEqual(result.status, "CONFIRMED")
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_balance, Decimal("0.00"))

    def test_cannot_match_already_reconciled(self):
        from core.exceptions.domain import ConflictError
        payment1 = Payment.objects.create(
            customer=self.customer,
            method=PaymentMethod.objects.get(code="MPESA"),
            amount=Decimal("100.00"),
            received_by=self.boss,
            mpesa_transaction_id="CHK-DUP",
            status=Payment.Status.PENDING,
        )
        self._make_tx("CHK-DUP")
        MpesaReconciliationService.auto_match("CHK-DUP")

        tx = MpesaTransaction.objects.get(transaction_id="CHK-DUP")
        # Try to manually match a different payment to the same tx
        payment2 = Payment.objects.create(
            customer=self.customer,
            method=PaymentMethod.objects.get(code="MPESA"),
            amount=Decimal("50.00"),
            received_by=self.boss,
            status=Payment.Status.PENDING,
        )
        with self.assertRaises(ConflictError):
            MpesaReconciliationService.manual_match(tx.pk, payment2.pk, self.boss)