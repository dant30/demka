"""Map DEMKA domain values to KRA eTIMS code tables."""
from decimal import Decimal

from core.exceptions.domain import DomainError


class EtimsMappingError(DomainError):
    code = "etims_mapping_error"

    def __init__(self, message: str):
        super().__init__(message, code="etims_mapping_error")


class TaxMapper:
    """
    TaxRate.etims_code is authoritative. Only fall back to rate inference
    when the code is missing — and refuse rather than guess incorrectly.
    """

    RATE_TO_CODE = {
        Decimal("16.00"): "B",
        Decimal("8.00"):  "E",
        Decimal("0.00"):  "C",   # safe default; boss should set A/C/D explicitly
    }

    @classmethod
    def code_for_sale_item(cls, sale_item) -> str:
        ref = sale_item.tax_rate_ref
        if ref is not None:
            code = getattr(ref, "etims_code", "") or ""
            if code:
                return code
        rate = Decimal(str(sale_item.tax_rate)).quantize(Decimal("0.01"))
        code = cls.RATE_TO_CODE.get(rate)
        if not code:
            raise EtimsMappingError(
                f"SaleItem {sale_item.pk}: no eTIMS tax code for rate {rate}%. "
                f"Set `TaxRate.etims_code`."
            )
        return code


class PaymentMapper:
    MAP = {
        "CASH":          "01",
        "CREDIT":        "02",
        "CHEQUE":        "03",
        "MPESA":         "04",
        "CARD":          "05",
        "BANK_TRANSFER": "06",
    }

    @classmethod
    def code_for_method(cls, code: str) -> str:
        return cls.MAP.get(code, "06")

    @classmethod
    def code_for_sale(cls, sale) -> str:
        """
        Pick the dominant payment type for the whole sale.
        Credit sale with no confirmed payments → 02.
        Otherwise → method of the largest confirmed payment.
        """
        payments = list(sale.payments.filter(status="CONFIRMED"))
        if not payments:
            return "02" if sale.is_credit_sale else "01"
        largest = max(payments, key=lambda p: p.amount)
        return cls.code_for_method(largest.method.code)


class UnitMapper:
    """DEMKA Product.unit → KRA qtyUnitCd."""
    MAP = {
        "PIECE": "U",
        "SET":   "U",   # KRA code list has no dedicated 'set'; U is accepted
        "PAIR":  "U",
        "LITRE": "L",
    }

    @classmethod
    def qty_unit_for(cls, product) -> str:
        return cls.MAP.get(product.unit, "U")