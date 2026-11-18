"""Typed wrapper over CustomerService.adjust_balance — the only place
ledger entries should be written from payments/sales/purchasing."""
from decimal import Decimal


class LedgerService:

    @staticmethod
    def _post(customer_id, delta, entry_type, reference_type, reference_id):
        from apps.customers.services import CustomerService
        return CustomerService.adjust_balance(
            customer_id=customer_id,
            delta=delta,
            entry_type=entry_type,
            reference_type=reference_type,
            reference_id=reference_id,
        )

    @classmethod
    def post_invoice(cls, customer_id, amount, reference_type, reference_id):
        """Customer owes more — sale on credit."""
        return cls._post(customer_id, Decimal(str(amount)), "INVOICE", reference_type, reference_id)

    @classmethod
    def post_payment(cls, customer_id, amount, reference_type, reference_id):
        """Customer paid — reduces debt."""
        return cls._post(customer_id, -Decimal(str(amount)), "PAYMENT", reference_type, reference_id)

    @classmethod
    def post_credit_note(cls, customer_id, amount, reference_type, reference_id):
        """Goods returned — reduces debt."""
        return cls._post(customer_id, -Decimal(str(amount)), "CREDIT_NOTE", reference_type, reference_id)

    @classmethod
    def post_adjustment(cls, customer_id, delta, reference_type, reference_id):
        """Free-form correction (signed)."""
        return cls._post(customer_id, Decimal(str(delta)), "ADJUSTMENT", reference_type, reference_id)

    @classmethod
    def post_opening_balance(cls, customer_id, amount):
        """Set the initial debt for an existing customer."""
        return cls._post(customer_id, Decimal(str(amount)), "OPENING_BALANCE", "CustomerSetup", "")