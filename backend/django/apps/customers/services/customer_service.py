"""Customer domain services — balance, credit, walk-in, route assignment."""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.exceptions.domain import (
    CreditLimitExceededError,
    NotFoundError,
    ValidationError,
)
from core.utils.money import q


class CustomerService:

    # ---- Walk-in singleton ---------------------------------
    @staticmethod
    def get_or_create_walkin():
        from ..models import Customer

        customer = Customer.objects.filter(
            customer_type=Customer.Type.WALK_IN, is_active=True
        ).first()
        if customer:
            return customer
        return Customer.objects.create(
            code="WALK-IN",
            name="Walk-in Customer",
            phone="0000000000",
            customer_type=Customer.Type.WALK_IN,
            is_active=True,
        )

    # ---- Balance & credit ----------------------------------
    @staticmethod
    @transaction.atomic
    def adjust_balance(
        customer_id: int,
        delta,
        entry_type: str,
        reference_type: str = "",
        reference_id: str = "",
    ) -> Decimal:
        """
        Atomically change a customer's balance and write a ledger entry.
        Negative delta reduces debt; positive delta increases debt.
        """
        from ..models import Customer
        from apps.payments.models import CustomerLedgerEntry

        try:
            customer = Customer.objects.select_for_update().get(pk=customer_id)
        except Customer.DoesNotExist:
            raise NotFoundError("Customer", customer_id)

        delta = q(delta)
        new_balance = q(Decimal(customer.current_balance) + delta)
        customer.current_balance = new_balance
        customer.save(update_fields=["current_balance", "updated_at"])

        CustomerLedgerEntry.objects.create(
            customer=customer,
            entry_type=entry_type,
            amount=delta,
            balance_after=new_balance,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        return new_balance

    @staticmethod
    def check_credit_limit(customer, additional_amount) -> None:
        """Raise if `additional_amount` would exceed the customer's limit."""
        if customer.credit_limit <= 0:
            # No credit allowed at all
            if additional_amount > 0:
                raise CreditLimitExceededError(
                    customer.name,
                    limit=customer.credit_limit,
                    current=customer.current_balance,
                )
            return
        projected = q(Decimal(customer.current_balance) + Decimal(additional_amount))
        if projected > customer.credit_limit:
            raise CreditLimitExceededError(
                customer.name,
                limit=customer.credit_limit,
                current=customer.current_balance,
            )

    # ---- Route assignment ----------------------------------
    @staticmethod
    @transaction.atomic
    def assign_route(
        customer_id: int,
        route_id: int,
        reason: str = "",
        effective_date=None,
    ):
        from ..models import Customer, CustomerRouteAssignment
        from apps.routes.models import Route

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise NotFoundError("Customer", customer_id)
        try:
            route = Route.objects.get(pk=route_id, is_active=True)
        except Route.DoesNotExist:
            raise NotFoundError("Route", route_id)

        today = effective_date or timezone.now().date()

        # Close any open assignment
        CustomerRouteAssignment.objects.filter(
            customer=customer, assigned_to__isnull=True
        ).update(assigned_to=today, reason=reason or "Reassigned")

        return CustomerRouteAssignment.objects.create(
            customer=customer,
            route=route,
            assigned_from=today,
            reason=reason,
        )

    # ---- Bulk helpers --------------------------------------
    @staticmethod
    def customers_with_debt():
        from ..models import Customer

        return Customer.objects.filter(
            current_balance__gt=0, is_active=True
        ).order_by("-current_balance")

    @staticmethod
    def route_customers(route_id: int):
        from ..models import Customer, CustomerRouteAssignment

        return Customer.objects.filter(
            route_assignments__route_id=route_id,
            route_assignments__assigned_to__isnull=True,
            is_active=True,
        ).distinct()