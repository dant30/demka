"""Password strength policies."""
import re

MIN_LENGTH = 8


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < MIN_LENGTH:
        return False, f"Password must be at least {MIN_LENGTH} characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain a digit."
    return True, ""