"""Payment lifecycle — create, reverse, initiate STK push."""
from decimal import Decimal

from django.db import transaction

from core.exceptions.domain import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from core.utils.money import q

from ..models import Payment, PaymentMethod


class PaymentService:

    # ---- Helpers ------------------------------------------
    @staticmethod
    def _resolve_method(code: str) -> PaymentMethod:
        method = PaymentMethod.objects.filter(code=code, is_active=True).first()
        if not method:
            raise NotFoundError("PaymentMethod", code)
        return method

    @staticmethod
    def _validate_reference(method: PaymentMethod, data: dict) -> str:
        """Return the effective reference string, or raise if missing."""
        reference = (data.get("reference") or "").strip()
        mpesa_receipt = (data.get("mpesa_receipt_number") or "").strip()
        if method.requires_reference:
            if not reference and not mpesa_receipt:
                raise ValidationError(
                    f"{method.name} requires a reference number."
                )
        return reference or mpesa_receipt

    # ---- Create (for sale) --------------------------------
    @classmethod
    @transaction.atomic
    def create_for_sale(cls, sale, data: dict, received_by) -> Payment:
        """
        Create a CONFIRMED payment attached to a sale.
        Caller (SaleService.apply_payment) is responsible for updating the
        sale's amounts and reducing the customer's credit balance.
        """
        method = cls._resolve_method(data["method"])
        amount = q(data["amount"])
        if amount <= 0:
            raise ValidationError("Payment amount must be positive.")
        reference = cls._validate_reference(method, data)

        return Payment.objects.create(
            sale=sale,
            customer=sale.customer,
            method=method,
            amount=amount,
            reference=reference,
            received_by=received_by,
            location=sale.location,
            mpesa_phone=(data.get("mpesa_phone") or "").strip(),
            mpesa_transaction_id=(data.get("mpesa_transaction_id") or "").strip(),
            mpesa_receipt_number=(data.get("mpesa_receipt_number") or "").strip(),
            notes=(data.get("notes") or "").strip(),
            status=Payment.Status.CONFIRMED,
        )

    # ---- Create (standalone / on-account) -----------------
    @classmethod
    @transaction.atomic
    def create_standalone(cls, data: dict, received_by) -> Payment:
        """
        Create a CONFIRMED payment not tied to any sale.
        Reduces the customer's outstanding balance and writes a PAYMENT ledger entry.
        """
        from apps.customers.models import Customer
        from .ledger_service import LedgerService

        customer = (
            Customer.objects
            .select_for_update()
            .filter(pk=data["customer"], is_active=True)
            .first()
        )
        if not customer:
            raise NotFoundError("Customer", data["customer"])

        method = cls._resolve_method(data["method"])
        amount = q(data["amount"])
        if amount <= 0:
            raise ValidationError("Payment amount must be positive.")
        if amount > customer.current_balance:
            raise ValidationError(
                f"Payment exceeds outstanding balance ({customer.current_balance})."
            )
        reference = cls._validate_reference(method, data)

        payment = Payment.objects.create(
            sale=None,
            customer=customer,
            method=method,
            amount=amount,
            reference=reference,
            received_by=received_by,
            location_id=data.get("location"),
            mpesa_phone=(data.get("mpesa_phone") or "").strip(),
            mpesa_transaction_id=(data.get("mpesa_transaction_id") or "").strip(),
            mpesa_receipt_number=(data.get("mpesa_receipt_number") or "").strip(),
            notes=(data.get("notes") or "").strip(),
            status=Payment.Status.CONFIRMED,
        )

        LedgerService.post_payment(
            customer_id=customer.pk,
            amount=amount,
            reference_type="Payment",
            reference_id=payment.payment_number,
        )

        # Fire SMS receipt asynchronously
        try:
            from .tasks import send_payment_receipt_sms
            send_payment_receipt_sms.delay(payment.pk)
        except Exception:
            pass

        return payment

    # ---- Reverse ------------------------------------------
    @classmethod
    @transaction.atomic
    def reverse(cls, payment_id: int, user, reason: str = "") -> Payment:
        """
        Reverse a payment:
          - Restore sale amounts + status if linked
          - Reverse the customer ledger entry
          - Mark payment REVERSED
        """
        from .ledger_service import LedgerService

        try:
            payment = (
                Payment.objects.select_for_update(of=("self",))
                .get(pk=payment_id)
            )
        except Payment.DoesNotExist:
            raise NotFoundError("Payment", payment_id)

        if payment.status == Payment.Status.REVERSED:
            return payment
        if payment.status == Payment.Status.PENDING:
            raise ConflictError("Cannot reverse a PENDING payment.")

        # If the payment is attached to a sale, reverse the sale amounts
        if payment.sale_id:
            from apps.sales.models import Sale

            sale = Sale.objects.select_for_update().get(pk=payment.sale_id)
            sale.amount_paid = q(Decimal(sale.amount_paid) - Decimal(payment.amount))
            sale.balance_due = q(Decimal(sale.total) - Decimal(sale.amount_paid))
            if sale.balance_due <= 0:
                sale.balance_due = Decimal("0.00")
                sale.status = "PAID"
            elif sale.amount_paid > 0:
                sale.status = "PARTIAL"
            else:
                sale.status = "CONFIRMED"
            sale.save(update_fields=["amount_paid", "balance_due", "status"])

        # Reverse the customer ledger entry (always — whether sale-linked or not)
        LedgerService.post_adjustment(
            customer_id=payment.customer_id,
            delta=Decimal(payment.amount),  # increases the debt back
            reference_type="PaymentReversal",
            reference_id=payment.payment_number,
        )

        payment.status = Payment.Status.REVERSED
        if reason:
            payment.notes = (payment.notes + f"\nReversed: {reason.strip()}").strip()
        payment.save(update_fields=["status", "notes"])
        return payment

    # ---- STK Push -----------------------------------------
    @classmethod
    @transaction.atomic
    def initiate_stk_push(
        cls,
        customer_id: int,
        phone: str,
        amount,
        account_reference: str,
        user,
        sale_id: int | None = None,
    ) -> tuple[Payment, dict]:
        """
        Kick off an M-Pesa STK Push. Creates a PENDING payment whose
        mpesa_transaction_id is the CheckoutRequestID. On callback,
        MpesaReconciliationService will CONFIRM it and update the sale/ledger.
        """
        from apps.customers.models import Customer
        from apps.sales.models import Sale
        from core.services.payment import MpesaError, MpesaService

        customer = Customer.objects.filter(pk=customer_id, is_active=True).first()
        if not customer:
            raise NotFoundError("Customer", customer_id)

        amount = q(amount)
        if amount <= 0:
            raise ValidationError("Amount must be positive.")

        sale = None
        if sale_id:
            sale = Sale.objects.filter(pk=sale_id, customer=customer).first()
            if not sale:
                raise NotFoundError("Sale", sale_id)

        method = cls._resolve_method("MPESA")

        try:
            response = MpesaService.stk_push(
                phone=phone,
                amount=float(amount),
                account_ref=account_reference,
            )
        except MpesaError as exc:
            raise ConflictError(f"M-Pesa request failed: {exc}")

        payment = Payment.objects.create(
            sale=sale,
            customer=customer,
            method=method,
            amount=amount,
            reference=account_reference,
            received_by=user,
            location_id=None,
            mpesa_phone=phone,
            mpesa_transaction_id=response.get("CheckoutRequestID", ""),
            status=Payment.Status.PENDING,
            notes=(
                f"STK push initiated. "
                f"MerchantRequestID: {response.get('MerchantRequestID', '')}"
            ),
        )
        return payment, response