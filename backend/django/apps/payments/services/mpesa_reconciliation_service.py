"""Bridge between M-Pesa callbacks and Payment rows."""
from decimal import Decimal

from django.db import transaction

from core.exceptions.domain import ConflictError, NotFoundError
from core.utils.money import q

from ..models import MpesaTransaction, Payment


class MpesaReconciliationService:

    # ---- Auto-match (called from callback view) -----------
    @staticmethod
    @transaction.atomic
    def auto_match(checkout_request_id: str) -> Payment | None:
        """
        Called on every successful callback. Finds the PENDING Payment whose
        mpesa_transaction_id == CheckoutRequestID, confirms it, updates any
        linked sale, and adjusts the customer ledger.
        """
        from .ledger_service import LedgerService

        try:
            tx = (
                MpesaTransaction.objects
                .select_for_update()
                .get(transaction_id=checkout_request_id)
            )
        except MpesaTransaction.DoesNotExist:
            return None

        if tx.reconciled:
            return tx.matched_payment

        payment = (
            Payment.objects
            .select_for_update(of=("self",))
            .filter(
                mpesa_transaction_id=checkout_request_id,
                status=Payment.Status.PENDING,
            )
            .first()
        )
        if not payment:
            return None

        payment.mpesa_receipt_number = tx.mpesa_receipt
        payment.reference = tx.mpesa_receipt
        payment.status = Payment.Status.CONFIRMED
        payment.save(update_fields=["mpesa_receipt_number", "reference", "status"])

        tx.matched_payment = payment
        tx.reconciled = True
        tx.save(update_fields=["matched_payment", "reconciled"])

        # Apply to linked sale (reduce balance, update status)
        if payment.sale_id:
            from apps.sales.models import Sale

            sale = Sale.objects.select_for_update().get(pk=payment.sale_id)
            sale.amount_paid = q(Decimal(sale.amount_paid) + Decimal(payment.amount))
            sale.balance_due = q(Decimal(sale.total) - Decimal(sale.amount_paid))
            if sale.balance_due <= 0:
                sale.balance_due = Decimal("0.00")
                sale.status = "PAID"
            else:
                sale.status = "PARTIAL"
            sale.save(update_fields=["amount_paid", "balance_due", "status"])

            if sale.is_credit_sale:
                LedgerService.post_payment(
                    customer_id=sale.customer_id,
                    amount=payment.amount,
                    reference_type="Payment",
                    reference_id=payment.payment_number,
                )
        else:
            # Standalone — reduce customer balance
            LedgerService.post_payment(
                customer_id=payment.customer_id,
                amount=payment.amount,
                reference_type="Payment",
                reference_id=payment.payment_number,
            )

        return payment

    # ---- Manual reconciliation (boss only) ----------------
    @staticmethod
    @transaction.atomic
    def manual_match(transaction_id: int, payment_id: int, user) -> Payment:
        """
        Manually link a specific M-Pesa transaction to an existing
        PENDING payment (e.g. auto-match failed because the customer paid
        from a different phone number, or an earlier STK push was abandoned).
        """
        try:
            tx = MpesaTransaction.objects.select_for_update().get(pk=transaction_id)
        except MpesaTransaction.DoesNotExist:
            raise NotFoundError("MpesaTransaction", transaction_id)
        if tx.reconciled:
            raise ConflictError("This M-Pesa transaction is already reconciled.")

        try:
            payment = (
                Payment.objects.select_for_update(of=("self",))
                .get(pk=payment_id)
            )
        except Payment.DoesNotExist:
            raise NotFoundError("Payment", payment_id)
        if payment.status != Payment.Status.PENDING:
            raise ConflictError(
                f"Only PENDING payments can be reconciled (current: {payment.status})."
            )

        payment.mpesa_transaction_id = tx.transaction_id
        payment.mpesa_receipt_number = tx.mpesa_receipt
        payment.mpesa_phone = tx.phone
        payment.reference = tx.mpesa_receipt or payment.reference
        payment.status = Payment.Status.CONFIRMED
        payment.save(update_fields=[
            "mpesa_transaction_id", "mpesa_receipt_number",
            "mpesa_phone", "reference", "status",
        ])

        tx.matched_payment = payment
        tx.reconciled = True
        tx.save(update_fields=["matched_payment", "reconciled"])

        # Apply ledger effects
        from .ledger_service import LedgerService
        if payment.sale_id:
            from apps.sales.models import Sale

            sale = Sale.objects.select_for_update().get(pk=payment.sale_id)
            sale.amount_paid = q(Decimal(sale.amount_paid) + Decimal(payment.amount))
            sale.balance_due = q(Decimal(sale.total) - Decimal(sale.amount_paid))
            sale.status = "PAID" if sale.balance_due <= 0 else "PARTIAL"
            sale.save(update_fields=["amount_paid", "balance_due", "status"])
            if sale.is_credit_sale:
                LedgerService.post_payment(
                    customer_id=sale.customer_id,
                    amount=payment.amount,
                    reference_type="Payment",
                    reference_id=payment.payment_number,
                )
        else:
            LedgerService.post_payment(
                customer_id=payment.customer_id,
                amount=payment.amount,
                reference_type="Payment",
                reference_id=payment.payment_number,
            )

        return payment

    # ---- Unreconciled listing -----------------------------
    @staticmethod
    def unreconciled_transactions():
        return (
            MpesaTransaction.objects
            .filter(reconciled=False)
            .order_by("-transaction_date")
        )