"""
Sale lifecycle — create, confirm, cancel, apply payment.

Atomicity contract:
    confirm() writes stock movements, customer ledger, and status in one
    transaction. If any line fails (insufficient stock, credit limit),
    the whole sale stays DRAFT and no side-effects persist.
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from core.exceptions.domain import (
    ConflictError,
    CreditLimitExceededError,
    NotFoundError,
    ValidationError,
)
from core.utils.money import q

from ..models import Sale, SaleItem


DEFAULT_TAX_RATE_PCT = Decimal("16.00")


class SaleService:

    # ---- Tax rate resolution ------------------------------
    @staticmethod
    def _resolve_tax_rate():
        """Return (rate_pct, TaxRate instance or None)."""
        try:
            from apps.common.models import TaxRate, BusinessConfiguration
            cfg = BusinessConfiguration.get_solo()
            rate_obj = cfg.default_tax_rate
            if rate_obj is None:
                rate_obj = TaxRate.objects.filter(is_active=True).order_by("-effective_from").first()
        except Exception:
            rate_obj = None

        if rate_obj:
            return q(rate_obj.rate), rate_obj
        return DEFAULT_TAX_RATE_PCT, None

    # ---- Line computation ---------------------------------
    @classmethod
    def _compute_line(
        cls,
        product,
        quantity,
        unit_price,
        discount,
        tax_rate_pct,
    ) -> dict:
        qty = q(quantity)
        if qty <= 0:
            raise ValidationError(f"Quantity for {product.sku} must be positive.")
        price = q(unit_price)
        if price <= 0:
            raise ValidationError(f"Unit price for {product.sku} must be positive.")
        disc = q(discount or 0)
        if disc < 0:
            raise ValidationError(f"Discount for {product.sku} cannot be negative.")

        line_sub = q(qty * price - disc)
        if line_sub < 0:
            raise ValidationError(f"Discount exceeds line amount for {product.sku}.")
        line_tax = q(line_sub * tax_rate_pct / Decimal("100"))
        line_total = q(line_sub + line_tax)
        return {
            "quantity": qty,
            "unit_price": price,
            "unit_cost": q(product.cost_price),
            "discount": disc,
            "line_subtotal": line_sub,
            "line_tax": line_tax,
            "line_total": line_total,
        }

    @classmethod
    def _resolve_unit_price(cls, product, customer, explicit=None, user=None):
        if explicit is not None:
            price = q(explicit)
            cost = q(product.cost_price)
            if price < cost and getattr(user, "role", None) not in ("BOSS", "ADMIN"):
                raise ValidationError(
                    f"Cannot sell {product.sku} below cost price."
                )
            return price
        if customer.customer_type == "RESELLER":
            return q(product.wholesale_price)
        return q(product.retail_price)

    # ---- Preview (used by POS to show totals before submitting) ----
    @classmethod
    def preview(cls, data: dict, user) -> dict:
        from apps.customers.models import Customer
        from apps.inventory.models import Product

        customer = Customer.objects.filter(pk=data["customer"]).first()
        if not customer:
            raise NotFoundError("Customer", data["customer"])

        tax_rate_pct, _ = cls._resolve_tax_rate()
        items = data.get("items") or []
        if not items:
            raise ValidationError("Sale must contain at least one item.")

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        rows = []

        for line in items:
            product = Product.objects.filter(pk=line["product"], is_active=True).first()
            if not product:
                raise NotFoundError("Product", line["product"])
            unit_price = cls._resolve_unit_price(
                product, customer, explicit=line.get("unit_price"), user=user,
            )
            row = cls._compute_line(
                product=product,
                quantity=line["quantity"],
                unit_price=unit_price,
                discount=line.get("discount", 0),
                tax_rate_pct=tax_rate_pct,
            )
            subtotal += row["line_subtotal"]
            tax_amount += row["line_tax"]
            rows.append({
                "product": product.pk,
                "sku": product.sku,
                "name": product.name,
                "quantity": str(row["quantity"]),
                "unit_price": str(row["unit_price"]),
                "unit_cost": str(row["unit_cost"]),
                "discount": str(row["discount"]),
                "tax_rate": str(tax_rate_pct),
                "line_subtotal": str(row["line_subtotal"]),
                "line_tax": str(row["line_tax"]),
                "line_total": str(row["line_total"]),
            })

        sale_discount = q(data.get("discount_amount", 0))
        if sale_discount < 0:
            raise ValidationError("Sale discount cannot be negative.")
        if sale_discount > subtotal + tax_amount:
            raise ValidationError("Sale discount exceeds total.")
        total = q(subtotal + tax_amount - sale_discount)
        amount_paid = q(data.get("amount_paid", 0))
        if amount_paid < 0 or amount_paid > total:
            raise ValidationError("Initial payment must be between 0 and total.")

        return {
            "items": rows,
            "subtotal": str(q(subtotal)),
            "tax_amount": str(q(tax_amount)),
            "discount_amount": str(sale_discount),
            "total": str(total),
            "amount_paid": str(amount_paid),
            "balance_due": str(q(total - amount_paid)),
        }

    # ---- Create -------------------------------------------
    @classmethod
    @transaction.atomic
    def create_sale(cls, data: dict, user, confirm: bool = True) -> Sale:
        from apps.customers.models import Customer
        from apps.inventory.models import Product, StockLocation
        from apps.routes.models import Route

        # Customer
        customer = Customer.objects.filter(pk=data["customer"], is_active=True).first()
        if not customer:
            raise NotFoundError("Customer", data["customer"])

        # Location
        location = StockLocation.objects.filter(pk=data["location"], is_active=True).first()
        if not location:
            raise NotFoundError("StockLocation", data["location"])

        # Channel
        channel = data.get("channel")
        if channel not in (Sale.Channel.SHOP, Sale.Channel.FIELD):
            raise ValidationError("channel must be SHOP or FIELD.")
        if channel == Sale.Channel.SHOP and location.location_type not in ("SHOP", "WAREHOUSE"):
            raise ValidationError("Shop sales must originate from a shop/warehouse location.")
        if channel == Sale.Channel.FIELD and location.location_type != "FIELD":
            raise ValidationError("Field sales must originate from a field (van) location.")

        # Sale type
        sale_type = data.get("sale_type", Sale.SaleType.STANDARD)
        if sale_type not in (Sale.SaleType.STANDARD, Sale.SaleType.SPECIAL_ORDER):
            raise ValidationError("Invalid sale_type.")

        # Optional route
        route = None
        if data.get("route"):
            route = Route.objects.filter(pk=data["route"]).first()

        items_input = data.get("items") or []
        if not items_input:
            raise ValidationError("Sale must contain at least one item.")

        sale = Sale.objects.create(
            channel=channel,
            sale_type=sale_type,
            customer=customer,
            location=location,
            route=route,
            agent=user,
            notes=data.get("notes", ""),
            due_date=data.get("due_date"),
        )

        tax_rate_pct, tax_rate_ref = cls._resolve_tax_rate()
        subtotal = Decimal("0")
        tax_amount = Decimal("0")

        for line in items_input:
            product = Product.objects.filter(pk=line["product"], is_active=True).first()
            if not product:
                raise NotFoundError("Product", line["product"])

            unit_price = cls._resolve_unit_price(
                product, customer, explicit=line.get("unit_price"), user=user,
            )
            row = cls._compute_line(
                product=product,
                quantity=line["quantity"],
                unit_price=unit_price,
                discount=line.get("discount", 0),
                tax_rate_pct=tax_rate_pct,
            )

            item = SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=row["quantity"],
                unit_price=row["unit_price"],
                unit_cost=row["unit_cost"],
                discount=row["discount"],
                tax_rate=tax_rate_pct,
                tax_rate_ref=tax_rate_ref,
                line_total=row["line_total"],
            )
            subtotal += row["line_subtotal"]
            tax_amount += row["line_tax"]

            if sale_type == Sale.SaleType.SPECIAL_ORDER:
                from .special_order_service import SpecialOrderService
                SpecialOrderService.create_for_sale_item(
                    sale_item=item,
                    supplier_id=line.get("supplier"),
                    expected_arrival_date=line.get("expected_arrival_date"),
                    customer_deposit=q(line.get("customer_deposit", 0)),
                )

        sale_discount = q(data.get("discount_amount", 0))
        if sale_discount < 0:
            raise ValidationError("Sale discount cannot be negative.")
        if sale_discount > subtotal + tax_amount:
            raise ValidationError("Sale discount exceeds total.")

        sale.subtotal = q(subtotal)
        sale.tax_amount = q(tax_amount)
        sale.discount_amount = sale_discount
        sale.total = q(subtotal + tax_amount - sale_discount)

        initial_payment = q(data.get("amount_paid", 0))
        if initial_payment < 0 or initial_payment > sale.total:
            raise ValidationError("Initial payment must be between 0 and total.")
        sale.amount_paid = initial_payment
        sale.balance_due = q(sale.total - initial_payment)
        sale.is_credit_sale = sale.balance_due > Decimal("0")
        sale.save(update_fields=[
            "subtotal", "tax_amount", "discount_amount", "total",
            "amount_paid", "balance_due", "is_credit_sale",
        ])

        if initial_payment > 0:
            payment_method_code = data.get("payment_method")
            if not payment_method_code:
                raise ValidationError(
                    "payment_method is required when amount_paid > 0."
                )
            from apps.payments.models import PaymentMethod
            from apps.payments.services import PaymentService

            method = PaymentMethod.objects.filter(
                code=payment_method_code, is_active=True,
            ).first()
            if not method:
                raise ValidationError(
                    f"Unknown payment method: {payment_method_code}"
                )
            PaymentService.create_for_sale(
                sale=sale,
                data={
                    "amount": initial_payment,
                    "method": payment_method_code,
                    "reference": data.get("payment_reference", ""),
                },
                received_by=user,
            )

        if confirm:
            sale = cls.confirm(sale.pk, user)

        return sale

    # ---- Confirm ------------------------------------------
    @classmethod
    @transaction.atomic
    def confirm(cls, sale_id: int, user) -> Sale:
        from apps.customers.services import CustomerService
        from apps.inventory.services import StockService

        try:
            sale = (
                Sale.objects.select_for_update()
                .select_related("customer", "location")
                .get(pk=sale_id)
            )
        except Sale.DoesNotExist:
            raise NotFoundError("Sale", sale_id)

        if sale.status != Sale.Status.DRAFT:
            raise ConflictError(f"Cannot confirm a sale in status {sale.status}.")

        items = list(sale.items.select_related("product").all())
        if not items:
            raise ValidationError("Cannot confirm an empty sale.")

        # Deduct stock (skipped for special orders — items aren't in inventory yet)
        if sale.sale_type == Sale.SaleType.STANDARD:
            for item in items:
                StockService.sell(
                    product=item.product,
                    location=sale.location,
                    quantity=item.quantity,
                    sale_reference=sale.sale_number,
                    unit_cost=item.unit_cost,
                    user=user,
                )

        # Validate credit after stock so insufficient inventory is reported
        # first when a sale violates both constraints. Atomic rollback keeps
        # the stock changes from persisting if the credit check fails.
        if sale.is_credit_sale and sale.balance_due > 0:
            CustomerService.check_credit_limit(sale.customer, sale.balance_due)

        # Credit ledger
        if sale.is_credit_sale and sale.balance_due > 0:
            CustomerService.adjust_balance(
                customer_id=sale.customer_id,
                delta=sale.balance_due,
                entry_type="INVOICE",
                reference_type="Sale",
                reference_id=sale.sale_number,
            )

        sale.status = Sale.Status.CONFIRMED
        sale.confirmed_at = timezone.now()
        # Reflect paid state
        if sale.balance_due == 0 and sale.amount_paid == sale.total:
            sale.status = Sale.Status.PAID
        elif sale.amount_paid > 0 and sale.balance_due > 0:
            sale.status = Sale.Status.PARTIAL
        sale.save(update_fields=["status", "confirmed_at"])

        # Async hooks
        try:
            from .tasks import queue_sale_receipt, submit_sale_to_etims
            queue_sale_receipt.delay(sale.pk, user.pk)
            submit_sale_to_etims.delay(sale.pk)
        except Exception:
            pass

        return sale

    # ---- Cancel -------------------------------------------
    @classmethod
    @transaction.atomic
    def cancel(cls, sale_id: int, user, reason: str) -> Sale:
        from apps.customers.services import CustomerService
        from apps.inventory.services import StockService

        if not reason or not reason.strip():
            raise ValidationError("A cancellation reason is required.")

        try:
            sale = (
                Sale.objects.select_for_update()
                .select_related("customer", "location")
                .get(pk=sale_id)
            )
        except Sale.DoesNotExist:
            raise NotFoundError("Sale", sale_id)

        if sale.status == Sale.Status.CANCELLED:
            return sale
        if sale.status == Sale.Status.RETURNED:
            raise ConflictError("Cannot cancel a fully returned sale.")
        if sale.amount_paid > 0:
            raise ConflictError(
                "Cannot cancel a sale with payments applied. Use the Returns flow."
            )

        # Reverse stock (only if it was deducted)
        if (
            sale.sale_type == Sale.SaleType.STANDARD
            and sale.status in (Sale.Status.CONFIRMED, Sale.Status.PAID, Sale.Status.PARTIAL)
        ):
            for item in sale.items.select_related("product"):
                StockService.adjust(
                    product=item.product,
                    location=sale.location,
                    delta=item.quantity,
                    movement_type="ADJUSTMENT",
                    reference_type="SaleCancellation",
                    reference_id=sale.sale_number,
                    notes=f"Cancelled by {user.username}: {reason.strip()[:200]}",
                    user=user,
                )

        # Reverse credit ledger (if credit was extended)
        if sale.is_credit_sale and sale.balance_due > 0:
            CustomerService.adjust_balance(
                customer_id=sale.customer_id,
                delta=-sale.balance_due,
                entry_type="ADJUSTMENT",
                reference_type="SaleCancellation",
                reference_id=sale.sale_number,
            )

        sale.cancel(user=user, reason=reason)
        return sale

    # ---- Apply payment ------------------------------------
    @classmethod
    @transaction.atomic
    def apply_payment(cls, sale_id: int, data: dict, user) -> "Payment":
        """
        Record a payment against a confirmed sale.
        Delegates to the payments app to create the Payment row, then updates
        the sale's amount_paid / balance_due / status and reverses credit.
        """
        from apps.payments.services import PaymentService
        from apps.customers.services import CustomerService

        try:
            sale = Sale.objects.select_for_update().select_related("customer").get(pk=sale_id)
        except Sale.DoesNotExist:
            raise NotFoundError("Sale", sale_id)

        if sale.status not in (
            Sale.Status.CONFIRMED, Sale.Status.PARTIAL, Sale.Status.PAID,
        ):
            raise ConflictError(f"Cannot apply payment to a sale in status {sale.status}.")

        amount = q(data["amount"])
        if amount <= 0:
            raise ValidationError("Payment amount must be positive.")
        if amount > sale.balance_due:
            raise ValidationError(
                f"Payment exceeds outstanding balance ({sale.balance_due})."
            )

        payment = PaymentService.create_for_sale(
            sale=sale,
            data=data,
            received_by=user,
        )

        sale.amount_paid = q(sale.amount_paid + amount)
        sale.balance_due = q(sale.total - sale.amount_paid)
        if sale.balance_due == 0:
            sale.status = Sale.Status.PAID
        else:
            sale.status = Sale.Status.PARTIAL
        sale.save(update_fields=["amount_paid", "balance_due", "status"])

        # Reduce customer debt (only for the credit portion)
        if sale.is_credit_sale:
            CustomerService.adjust_balance(
                customer_id=sale.customer_id,
                delta=-amount,
                entry_type="PAYMENT",
                reference_type="Payment",
                reference_id=payment.payment_number,
            )

        return payment

    # ---- Receipt payload ----------------------------------
    @classmethod
    def receipt_payload(cls, sale_id: int) -> dict:
        from apps.common.models import BusinessConfiguration

        sale = (
            Sale.objects
            .select_related("customer", "location", "agent", "route")
            .prefetch_related("items__product")
            .filter(pk=sale_id)
            .first()
        )
        if not sale:
            raise NotFoundError("Sale", sale_id)

        cfg = BusinessConfiguration.get_solo()
        return {
            "business": {
                "name": cfg.business_name,
                "kra_pin": cfg.kra_pin,
                "address": cfg.address,
                "phone": cfg.phone,
                "email": cfg.email,
                "receipt_footer": cfg.receipt_footer,
            },
            "sale": {
                "sale_number": sale.sale_number,
                "channel": sale.channel,
                "sale_type": sale.sale_type,
                "status": sale.status,
                "customer_name": sale.customer.name,
                "customer_phone": sale.customer.phone,
                "agent": sale.agent.get_full_name() or sale.agent.username,
                "location": sale.location.name,
                "route": sale.route.name if sale.route else None,
                "subtotal": str(sale.subtotal),
                "tax_amount": str(sale.tax_amount),
                "discount_amount": str(sale.discount_amount),
                "total": str(sale.total),
                "amount_paid": str(sale.amount_paid),
                "balance_due": str(sale.balance_due),
                "is_credit_sale": sale.is_credit_sale,
                "etims_invoice_number": sale.etims_invoice_number,
                "created_at": sale.created_at.isoformat(),
                "confirmed_at": sale.confirmed_at.isoformat() if sale.confirmed_at else None,
            },
            "items": [
                {
                    "sku": item.product.sku,
                    "name": item.product.name,
                    "quantity": str(item.quantity),
                    "unit_price": str(item.unit_price),
                    "discount": str(item.discount),
                    "tax_rate": str(item.tax_rate),
                    "line_total": str(item.line_total),
                }
                for item in sale.items.all()
            ],
            "payments": [
                {
                    "payment_number": p.payment_number,
                    "method": p.method.code,
                    "amount": str(p.amount),
                    "reference": p.reference,
                    "received_at": p.received_at.isoformat(),
                }
                for p in sale.payments.all()
            ],
        }