"""Money math — always Decimal, Kenyan rounding."""
from decimal import Decimal, ROUND_HALF_UP

TWO = Decimal("0.01")


def q(value) -> Decimal:
    return Decimal(str(value)).quantize(TWO, rounding=ROUND_HALF_UP)


def zero() -> Decimal:
    return Decimal("0.00")


def apply_discount(amount, discount) -> Decimal:
    return q(Decimal(str(amount)) - Decimal(str(discount)))


def add_vat(amount, rate_percent) -> Decimal:
    rate = Decimal(str(rate_percent)) / Decimal("100")
    return q(Decimal(str(amount)) * (1 + rate))


def extract_vat(amount_incl, rate_percent) -> Decimal:
    rate = Decimal(str(rate_percent)) / Decimal("100")
    return q(Decimal(str(amount_incl)) * rate / (1 + rate))