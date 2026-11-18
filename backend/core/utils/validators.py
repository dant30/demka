"""Custom validators."""
import re
from django.core.exceptions import ValidationError

KE_PHONE_RE = re.compile(r"^(?:\+254|0)(7\d{8}|1\d{8})$")


def validate_kenyan_phone(value: str) -> None:
    if not KE_PHONE_RE.match(value):
        raise ValidationError(f"'{value}' is not a valid Kenyan phone number.")


def validate_kra_pin(value: str) -> None:
    if not re.match(r"^[A-Z]\d{9}[A-Z]$", value):
        raise ValidationError(f"'{value}' is not a valid KRA PIN.")