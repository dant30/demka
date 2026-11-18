"""Domain-level exceptions — carried through services, translated by API handler."""
from typing import Any, Optional


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None):
        self.message = message
        if code:
            self.code = code
        self.details = details
        super().__init__(message)


class NotFoundError(DomainError):
    code = "not_found"

    def __init__(self, resource: str, identifier: Any = None):
        msg = f"{resource} not found" + (f": {identifier}" if identifier else ".")
        super().__init__(msg, code="not_found")


class ValidationError(DomainError):
    code = "validation_error"


class BusinessRuleViolation(DomainError):
    code = "business_rule_violation"


class ConflictError(DomainError):
    code = "conflict"


class InsufficientStockError(DomainError):
    def __init__(self, product_name: str, requested, available):
        super().__init__(
            f"Insufficient stock for '{product_name}'. Requested {requested}, available {available}.",
            code="insufficient_stock",
            details={"product": product_name, "requested": str(requested), "available": str(available)},
        )


class CreditLimitExceededError(DomainError):
    def __init__(self, customer_name: str, limit=None, current=None):
        details = None
        if limit is not None and current is not None:
            details = {"limit": str(limit), "current": str(current)}
        super().__init__(
            f"Credit limit exceeded for '{customer_name}'.",
            code="credit_limit_exceeded",
            details=details,
        )